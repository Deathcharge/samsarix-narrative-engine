# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Command-line interface for planning and running narrative workflows."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Optional

from . import __version__
from .agents import PRESETS, build_plan, build_resume_plan
from .artifacts import dumps_run_bundle, load_run_bundle
from .engine import NarrativeEngine
from .exceptions import (
    BudgetExceededError,
    ConfigurationError,
    InputValidationError,
    OutputError,
    ProviderError,
)
from .models import GenerationOptions
from .providers import Provider, build_provider

ProviderFactory = Callable[..., Provider]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="samsarix-narrative",
        description="Run inspectable, cost-bounded narrative workflows.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser(
        "plan",
        help="show calls and output-token caps without using a provider",
    )
    plan_parser.add_argument("--preset", choices=tuple(PRESETS), default="balanced")
    plan_parser.add_argument(
        "--from-stage",
        help="show only the calls needed to resume from this stage",
    )
    plan_parser.add_argument("--json", action="store_true", dest="as_json")

    generate_parser = subparsers.add_parser("generate", help="generate one complete short story")
    prompt_group = generate_parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument("--prompt", help="creative brief; use --prompt-file for long prompts")
    prompt_group.add_argument(
        "--prompt-file",
        help="UTF-8 creative brief file, or - to read standard input",
    )
    generate_parser.add_argument("--preset", choices=tuple(PRESETS), default="balanced")
    generate_parser.add_argument(
        "--provider",
        choices=("openai", "anthropic", "xai", "perplexity"),
        default=os.getenv("SAMSARIX_PROVIDER", "openai"),
    )
    generate_parser.add_argument(
        "--model",
        default=os.getenv("SAMSARIX_MODEL"),
        help="provider model ID; defaults to a documented stable model",
    )
    generate_parser.add_argument("--output", type=Path, help="write final Markdown story here")
    generate_parser.add_argument(
        "--artifacts",
        type=Path,
        help="write JSON with all stages and provider-reported usage here",
    )
    generate_parser.add_argument(
        "--force",
        action="store_true",
        help="replace explicitly named output files if they already exist",
    )
    generate_parser.add_argument("--timeout", type=float, default=90.0, dest="timeout_seconds")
    generate_parser.add_argument("--max-prompt-chars", type=int, default=12_000)
    generate_parser.add_argument("--max-calls", type=int, default=7)
    generate_parser.add_argument("--max-total-output-tokens", type=int, default=10_000)

    resume_parser = subparsers.add_parser(
        "resume",
        help="branch an editable run bundle and rerun one stage plus its successors",
    )
    resume_parser.add_argument(
        "--artifacts-in",
        required=True,
        type=Path,
        help="existing Samsarix run bundle to branch",
    )
    resume_parser.add_argument(
        "--from-stage",
        required=True,
        help="first stage to rerun; earlier edited artifacts are reused",
    )
    resume_parser.add_argument(
        "--provider",
        choices=("openai", "anthropic", "xai", "perplexity"),
        default=os.getenv("SAMSARIX_PROVIDER", "openai"),
    )
    resume_parser.add_argument("--model", default=os.getenv("SAMSARIX_MODEL"))
    resume_parser.add_argument("--output", type=Path, help="write branched Markdown story here")
    resume_parser.add_argument(
        "--artifacts-out",
        type=Path,
        help="write the new versioned run bundle here",
    )
    resume_parser.add_argument(
        "--allow-workflow-change",
        action="store_true",
        help="resume after reviewing changes to built-in prompts or stage definitions",
    )
    resume_parser.add_argument("--force", action="store_true")
    resume_parser.add_argument("--timeout", type=float, default=90.0, dest="timeout_seconds")
    resume_parser.add_argument("--max-prompt-chars", type=int, default=12_000)
    resume_parser.add_argument("--max-calls", type=int, default=7)
    resume_parser.add_argument("--max-total-output-tokens", type=int, default=10_000)
    return parser


def _render_plan(preset: str, as_json: bool, from_stage: Optional[str] = None) -> str:
    try:
        plan = build_resume_plan(preset, from_stage) if from_stage else build_plan(preset)
    except ValueError as error:
        raise InputValidationError(str(error)) from error
    if as_json:
        payload = plan.to_dict()
        if from_stage:
            payload["from_stage"] = from_stage
        return json.dumps(payload, indent=2)
    rows = [f"Preset: {plan.preset}"]
    if from_stage:
        rows.append(f"Resume from: {from_stage}")
    for index, stage in enumerate(plan.stages, start=1):
        rows.append(
            f"{index}. {stage.stage_id} - {stage.role} "
            f"(max {stage.max_output_tokens} output tokens)"
        )
    rows.extend(
        (
            f"Maximum provider calls: {plan.max_calls}",
            f"Maximum requested output tokens: {plan.max_output_tokens}",
            "Input tokens are provider-dependent and are not estimated by this command.",
        )
    )
    return "\n".join(rows)


def _read_prompt(args: argparse.Namespace) -> str:
    if args.prompt is not None:
        return str(args.prompt)
    if args.prompt_file == "-":
        return sys.stdin.read()
    try:
        return Path(args.prompt_file).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise InputValidationError(
            f"cannot read UTF-8 prompt file ({type(error).__name__})"
        ) from error


def _preflight_output(path: Optional[Path], *, force: bool) -> None:
    if path is None:
        return
    if path.exists() and path.is_dir():
        raise OutputError(f"output path is a directory: {path}")
    if path.exists() and not force:
        raise OutputError(f"output already exists; pass --force to replace it: {path}")
    parent = path.resolve().parent
    if parent.exists() and not parent.is_dir():
        raise OutputError(f"output parent is not a directory: {parent}")


def _atomic_write(path: Path, content: str, *, force: bool) -> None:
    resolved_path = path.resolve()
    parent = resolved_path.parent
    temporary_name: Optional[str] = None
    try:
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        if force:
            os.replace(temporary_name, resolved_path)
        else:
            # Publishing via a same-directory hard link is an atomic no-clobber
            # operation. It closes the gap between preflight and persistence.
            os.link(temporary_name, resolved_path)
            Path(temporary_name).unlink()
            temporary_name = None
    except OSError as error:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink(missing_ok=True)
            except OSError:
                pass
        raise OutputError(f"cannot write output ({type(error).__name__}): {path}") from error


async def _generate(args: argparse.Namespace, provider_factory: ProviderFactory) -> int:
    if args.output is not None and args.artifacts is not None:
        if args.output.resolve() == args.artifacts.resolve():
            raise OutputError("--output and --artifacts must name different files")
    _preflight_output(args.output, force=args.force)
    _preflight_output(args.artifacts, force=args.force)

    prompt = _read_prompt(args)
    options = GenerationOptions(
        preset=args.preset,
        timeout_seconds=args.timeout_seconds,
        max_prompt_chars=args.max_prompt_chars,
        max_calls=args.max_calls,
        max_total_output_tokens=args.max_total_output_tokens,
    )
    provider = provider_factory(
        args.provider,
        model=args.model,
        timeout_seconds=args.timeout_seconds,
    )
    result = await NarrativeEngine(provider).generate(prompt, options)

    story = result.content.rstrip() + "\n"
    if args.output is None:
        sys.stdout.write(story)
    else:
        _atomic_write(args.output, story, force=args.force)
    if args.artifacts is not None:
        _atomic_write(
            args.artifacts,
            dumps_run_bundle(result),
            force=args.force,
        )

    usage = result.usage
    token_summary = str(usage.total_tokens) if usage.total_tokens else "unreported"
    destination = str(args.output) if args.output is not None else "standard output"
    print(
        f"Generated {result.generation_id}: {len(result.stages)} calls, "
        f"{token_summary} total tokens; story written to {destination}.",
        file=sys.stderr,
    )
    return 0


async def _resume(args: argparse.Namespace, provider_factory: ProviderFactory) -> int:
    if args.output is not None and args.artifacts_out is not None:
        if args.output.resolve() == args.artifacts_out.resolve():
            raise OutputError("--output and --artifacts-out must name different files")
    if args.artifacts_out is not None:
        if args.artifacts_in.resolve() == args.artifacts_out.resolve():
            raise OutputError("--artifacts-in and --artifacts-out must name different files")
    _preflight_output(args.output, force=args.force)
    _preflight_output(args.artifacts_out, force=args.force)

    previous = load_run_bundle(args.artifacts_in)
    options = GenerationOptions(
        preset=previous.preset,
        timeout_seconds=args.timeout_seconds,
        max_prompt_chars=args.max_prompt_chars,
        max_calls=args.max_calls,
        max_total_output_tokens=args.max_total_output_tokens,
    )
    provider = provider_factory(
        args.provider,
        model=args.model,
        timeout_seconds=args.timeout_seconds,
    )
    result = await NarrativeEngine(provider).resume(
        previous,
        args.from_stage,
        options,
        allow_workflow_change=args.allow_workflow_change,
    )

    story = result.content.rstrip() + "\n"
    if args.output is None:
        sys.stdout.write(story)
    else:
        _atomic_write(args.output, story, force=args.force)
    if args.artifacts_out is not None:
        _atomic_write(args.artifacts_out, dumps_run_bundle(result), force=args.force)

    resumed_plan = build_resume_plan(previous.preset, args.from_stage)
    resumed_stages = result.stages[-resumed_plan.max_calls :]
    resumed_tokens = sum(stage.usage.total_tokens for stage in resumed_stages)
    token_summary = str(resumed_tokens) if resumed_tokens else "unreported"
    destination = str(args.output) if args.output is not None else "standard output"
    print(
        f"Resumed {previous.generation_id} from {args.from_stage} as {result.generation_id}: "
        f"{resumed_plan.max_calls} new calls, {token_summary} new total tokens; "
        f"story written to {destination}.",
        file=sys.stderr,
    )
    return 0


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    provider_factory: ProviderFactory = build_provider,
) -> int:
    """CLI entry point returning a meaningful process exit code."""

    args = _build_parser().parse_args(argv)
    try:
        if args.command == "plan":
            print(_render_plan(args.preset, args.as_json, args.from_stage))
            return 0
        if args.command == "resume":
            return asyncio.run(_resume(args, provider_factory))
        return asyncio.run(_generate(args, provider_factory))
    except (ConfigurationError, InputValidationError, BudgetExceededError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except ProviderError as error:
        print(f"provider error: {error}", file=sys.stderr)
        return 3
    except OutputError as error:
        print(f"output error: {error}", file=sys.stderr)
        return 4
    except KeyboardInterrupt:
        print("cancelled", file=sys.stderr)
        return 130
    except Exception as error:
        print(f"internal error ({type(error).__name__})", file=sys.stderr)
        return 1
