# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Deterministic blinded evaluation packets and evidence-backed reports."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Optional

from .artifacts import dumps_run_bundle, load_run_bundle
from .exceptions import InputValidationError

EVALUATION_SCHEMA = "samsarix.evaluation/v1"
EVALUATION_KEY_SCHEMA = "samsarix.evaluation-key/v1"
SCORES_SCHEMA = "samsarix.scores/v1"
EVALUATION_REPORT_SCHEMA = "samsarix.evaluation-report/v1"
MAX_EVALUATION_BYTES = 2 * 1024 * 1024
_IDENTIFIER = re.compile(r"[a-z][a-z0-9._-]{0,63}")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")


def _exact(data: Mapping[str, Any], expected: set[str], label: str) -> None:
    unknown = set(data) - expected
    missing = expected - set(data)
    if unknown:
        raise ValueError(f"{label} contains unknown fields: {', '.join(sorted(unknown))}")
    if missing:
        raise ValueError(f"{label} is missing fields: {', '.join(sorted(missing))}")


def _string(
    data: Mapping[str, Any],
    key: str,
    *,
    label: Optional[str] = None,
    minimum: int = 1,
    maximum: int = 10_000,
) -> str:
    value = data.get(key)
    if (
        not isinstance(value, str)
        or len(value) < minimum
        or len(value) > maximum
        or "\x00" in value
    ):
        raise ValueError(
            f"{label or key} must contain between {minimum} and {maximum} safe characters"
        )
    return value


def _identifier_value(value: Any, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase portable identifier")
    return value


def _portable_path(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or any(ord(character) < 32 for character in value)
    ):
        raise ValueError("run_bundle must be a non-empty portable relative path")
    raw_parts = value.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise ValueError("run_bundle must stay within the evaluation directory")
    selected = PurePosixPath(value)
    if selected.is_absolute():
        raise ValueError("run_bundle must stay within the evaluation directory")
    if ":" in raw_parts[0]:
        raise ValueError("run_bundle must not contain a drive or URI scheme")
    return selected.as_posix()


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _table_cell(value: str) -> str:
    return (
        value.replace("|", "¦").replace("\r\n", "<br>").replace("\r", "<br>").replace("\n", "<br>")
    )


def _read_json_object(path: str | Path, label: str) -> Mapping[str, Any]:
    selected = Path(path)
    try:
        if selected.stat().st_size > MAX_EVALUATION_BYTES:
            raise InputValidationError(f"{label} exceeds {MAX_EVALUATION_BYTES} bytes")
        payload = selected.read_text(encoding="utf-8")
    except InputValidationError:
        raise
    except (OSError, UnicodeError) as error:
        raise InputValidationError(f"cannot read UTF-8 {label} ({type(error).__name__})") from error
    if len(payload.encode("utf-8")) > MAX_EVALUATION_BYTES:
        raise InputValidationError(f"{label} exceeds {MAX_EVALUATION_BYTES} bytes")
    try:
        decoded: Any = json.loads(payload)
    except json.JSONDecodeError as error:
        raise InputValidationError(
            f"invalid {label} JSON at line {error.lineno}, column {error.colno}"
        ) from error
    if not isinstance(decoded, Mapping):
        raise InputValidationError(f"{label} must contain a JSON object")
    return decoded


@dataclass(frozen=True)
class RubricCriterion:
    """One equally weighted criterion scored from one through five."""

    criterion_id: str
    label: str
    description: str

    def __post_init__(self) -> None:
        _identifier_value(self.criterion_id, "criterion id")
        if (
            not self.label.strip()
            or "\x00" in self.label
            or "\r" in self.label
            or "\n" in self.label
            or len(self.label) > 128
        ):
            raise ValueError("criterion label must contain between 1 and 128 safe characters")
        if (
            not self.description.strip()
            or "\x00" in self.description
            or len(self.description) > 1_000
        ):
            raise ValueError(
                "criterion description must contain between 1 and 1000 safe characters"
            )

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.criterion_id,
            "label": self.label,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RubricCriterion:
        if not isinstance(data, Mapping):
            raise ValueError("each rubric criterion must be an object")
        _exact(data, {"id", "label", "description"}, "rubric criterion")
        return cls(
            criterion_id=_identifier_value(data.get("id"), "criterion id"),
            label=_string(data, "label", maximum=128),
            description=_string(data, "description", maximum=1_000),
        )


@dataclass(frozen=True)
class EvaluationTreatment:
    """One named run bundle in a pairwise case."""

    treatment_id: str
    run_bundle: str

    def __post_init__(self) -> None:
        _identifier_value(self.treatment_id, "treatment id")
        _portable_path(self.run_bundle)

    def to_dict(self) -> dict[str, str]:
        return {"id": self.treatment_id, "run_bundle": self.run_bundle}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EvaluationTreatment:
        if not isinstance(data, Mapping):
            raise ValueError("each treatment must be an object")
        _exact(data, {"id", "run_bundle"}, "treatment")
        return cls(
            treatment_id=_identifier_value(data.get("id"), "treatment id"),
            run_bundle=_portable_path(data.get("run_bundle")),
        )


@dataclass(frozen=True)
class EvaluationCase:
    """Exactly two treatments evaluated against one creative brief."""

    case_id: str
    treatments: tuple[EvaluationTreatment, EvaluationTreatment]

    def __post_init__(self) -> None:
        _identifier_value(self.case_id, "case id")
        if not isinstance(self.treatments, tuple) or len(self.treatments) != 2:
            raise ValueError("each evaluation case must contain exactly two treatments")
        if any(not isinstance(item, EvaluationTreatment) for item in self.treatments):
            raise ValueError("case treatments must be EvaluationTreatment values")
        ids = tuple(item.treatment_id for item in self.treatments)
        if len(set(ids)) != 2:
            raise ValueError("case treatment identifiers must be unique")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.case_id,
            "treatments": [item.to_dict() for item in self.treatments],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EvaluationCase:
        if not isinstance(data, Mapping):
            raise ValueError("each evaluation case must be an object")
        _exact(data, {"id", "treatments"}, "evaluation case")
        raw_treatments = data.get("treatments")
        if not isinstance(raw_treatments, list) or len(raw_treatments) != 2:
            raise ValueError("each evaluation case must contain exactly two treatments")
        treatments = tuple(EvaluationTreatment.from_dict(item) for item in raw_treatments)
        return cls(
            case_id=_identifier_value(data.get("id"), "case id"),
            treatments=(treatments[0], treatments[1]),
        )


@dataclass(frozen=True)
class EvaluationManifest:
    """Portable definition of a reproducible pairwise evaluation."""

    evaluation_id: str
    title: str
    seed: str
    rubric: tuple[RubricCriterion, ...]
    cases: tuple[EvaluationCase, ...]

    def __post_init__(self) -> None:
        _identifier_value(self.evaluation_id, "evaluation id")
        if (
            not self.title.strip()
            or "\x00" in self.title
            or "\r" in self.title
            or "\n" in self.title
            or len(self.title) > 160
        ):
            raise ValueError("evaluation title must contain between 1 and 160 safe characters")
        if not isinstance(self.seed, str) or not 1 <= len(self.seed) <= 256 or "\x00" in self.seed:
            raise ValueError("evaluation seed must contain between 1 and 256 safe characters")
        if not isinstance(self.rubric, tuple) or not 1 <= len(self.rubric) <= 8:
            raise ValueError("evaluation rubric must contain between 1 and 8 criteria")
        if not isinstance(self.cases, tuple) or not 1 <= len(self.cases) <= 100:
            raise ValueError("evaluation must contain between 1 and 100 cases")
        if any(not isinstance(item, RubricCriterion) for item in self.rubric):
            raise ValueError("rubric values must be RubricCriterion instances")
        if any(not isinstance(item, EvaluationCase) for item in self.cases):
            raise ValueError("case values must be EvaluationCase instances")
        criterion_ids = tuple(item.criterion_id for item in self.rubric)
        case_ids = tuple(item.case_id for item in self.cases)
        if len(set(criterion_ids)) != len(criterion_ids):
            raise ValueError("rubric criterion identifiers must be unique")
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("evaluation case identifiers must be unique")
        expected_treatments = {treatment.treatment_id for treatment in self.cases[0].treatments}
        for case in self.cases[1:]:
            actual = {treatment.treatment_id for treatment in case.treatments}
            if actual != expected_treatments:
                raise ValueError("every case must compare the same two treatment identifiers")

    @property
    def fingerprint(self) -> str:
        return _canonical_digest(self.to_dict())

    @property
    def treatment_ids(self) -> tuple[str, str]:
        items = sorted(treatment.treatment_id for treatment in self.cases[0].treatments)
        return items[0], items[1]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": EVALUATION_SCHEMA,
            "id": self.evaluation_id,
            "title": self.title,
            "seed": self.seed,
            "rubric": [criterion.to_dict() for criterion in self.rubric],
            "cases": [case.to_dict() for case in self.cases],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EvaluationManifest:
        if not isinstance(data, Mapping):
            raise ValueError("evaluation manifest must be an object")
        _exact(data, {"schema", "id", "title", "seed", "rubric", "cases"}, "manifest")
        if data.get("schema") != EVALUATION_SCHEMA:
            raise ValueError(f"evaluation schema must be '{EVALUATION_SCHEMA}'")
        raw_rubric = data.get("rubric")
        raw_cases = data.get("cases")
        if not isinstance(raw_rubric, list):
            raise ValueError("rubric must be an array")
        if not isinstance(raw_cases, list):
            raise ValueError("cases must be an array")
        return cls(
            evaluation_id=_identifier_value(data.get("id"), "evaluation id"),
            title=_string(data, "title", maximum=160),
            seed=_string(data, "seed", maximum=256),
            rubric=tuple(RubricCriterion.from_dict(item) for item in raw_rubric),
            cases=tuple(EvaluationCase.from_dict(item) for item in raw_cases),
        )


@dataclass(frozen=True)
class PreparedEvaluation:
    """Blinded packet, private key, and editable score sheet."""

    evidence_fingerprint: str
    packet_markdown: str
    key_json: str
    scores_json: str


@dataclass(frozen=True)
class EvaluationReport:
    """Unblinded JSON evidence and a human-readable report."""

    evidence_fingerprint: str
    markdown: str
    json_text: str


def load_evaluation_manifest(path: str | Path) -> EvaluationManifest:
    """Load and strictly validate one evaluation manifest."""

    data = _read_json_object(path, "evaluation manifest")
    try:
        return EvaluationManifest.from_dict(data)
    except ValueError as error:
        raise InputValidationError(f"invalid evaluation manifest: {error}") from error


def _resolve_run_bundle(base_directory: Path, portable_path: str) -> Path:
    root = base_directory.resolve()
    selected = root.joinpath(*PurePosixPath(portable_path).parts).resolve()
    try:
        selected.relative_to(root)
    except ValueError as error:
        raise InputValidationError(
            "run_bundle resolves outside the evaluation directory"
        ) from error
    return selected


def _run_evidence(treatment_id: str, run_bundle: str, base_directory: Path) -> dict[str, Any]:
    result = load_run_bundle(_resolve_run_bundle(base_directory, run_bundle))
    canonical_bundle = dumps_run_bundle(result)
    providers = sorted({stage.provider for stage in result.stages})
    models = sorted({stage.model for stage in result.stages})
    return {
        "treatment_id": treatment_id,
        "generation_id": result.generation_id,
        "run_digest": f"sha256:{hashlib.sha256(canonical_bundle.encode('utf-8')).hexdigest()}",
        "content_digest": f"sha256:{hashlib.sha256(result.content.encode('utf-8')).hexdigest()}",
        "workflow_id": result.workflow_id,
        "workflow_fingerprint": result.workflow_fingerprint,
        "calls": len(result.stages),
        "max_requested_output_tokens": sum(stage.max_output_tokens for stage in result.stages),
        "duration_ms": sum(stage.duration_ms for stage in result.stages),
        "usage": result.usage.to_dict(),
        "providers": providers,
        "models": models,
        "_creative_brief": result.creative_brief,
        "_content": result.content,
    }


def _blind_order(seed: str, case_id: str, records: Sequence[Mapping[str, Any]]) -> list[int]:
    def rank(index: int) -> tuple[bytes, str]:
        treatment_id = str(records[index]["treatment_id"])
        material = f"{seed}\x00{case_id}\x00{treatment_id}".encode()
        return hashlib.sha256(material).digest(), treatment_id

    return sorted(range(len(records)), key=rank)


def _fenced(value: str) -> str:
    longest = max((len(item) for item in re.findall(r"`+", value)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}text\n{value.rstrip()}\n{fence}"


def prepare_evaluation(
    manifest: EvaluationManifest,
    base_directory: str | Path,
) -> PreparedEvaluation:
    """Create deterministic blind materials from validated completed run bundles."""

    if not isinstance(manifest, EvaluationManifest):
        raise TypeError("manifest must be an EvaluationManifest")
    base = Path(base_directory)
    prepared_cases: list[dict[str, Any]] = []
    evidence_cases: list[dict[str, Any]] = []
    for case in manifest.cases:
        records = [
            _run_evidence(treatment.treatment_id, treatment.run_bundle, base)
            for treatment in case.treatments
        ]
        briefs = {str(record["_creative_brief"]) for record in records}
        if len(briefs) != 1:
            raise InputValidationError(
                f"case '{case.case_id}' treatments must use the same creative brief"
            )
        brief = next(iter(briefs))
        order = _blind_order(manifest.seed, case.case_id, records)
        assignments: dict[str, dict[str, Any]] = {}
        outputs: dict[str, str] = {}
        for label, record_index in zip(("A", "B"), order, strict=True):
            record = records[record_index]
            outputs[label] = str(record.pop("_content"))
            record.pop("_creative_brief")
            assignments[label] = record
        prepared_cases.append(
            {
                "id": case.case_id,
                "creative_brief": brief,
                "outputs": outputs,
                "assignments": assignments,
            }
        )
        evidence_cases.append(
            {
                "id": case.case_id,
                "treatments": sorted(
                    assignments.values(),
                    key=lambda item: str(item["treatment_id"]),
                ),
            }
        )

    rubric_data = [criterion.to_dict() for criterion in manifest.rubric]
    treatment_ids = list(manifest.treatment_ids)
    evidence_fingerprint = _canonical_digest(
        {
            "evaluation_fingerprint": manifest.fingerprint,
            "evaluation_id": manifest.evaluation_id,
            "title": manifest.title,
            "rubric": rubric_data,
            "treatments": treatment_ids,
            "cases": evidence_cases,
        }
    )
    key = {
        "schema": EVALUATION_KEY_SCHEMA,
        "evaluation_id": manifest.evaluation_id,
        "title": manifest.title,
        "evaluation_fingerprint": manifest.fingerprint,
        "evidence_fingerprint": evidence_fingerprint,
        "rubric": rubric_data,
        "treatments": treatment_ids,
        "cases": [
            {
                "id": case["id"],
                "assignments": case["assignments"],
            }
            for case in prepared_cases
        ],
    }
    scores = {
        "schema": SCORES_SCHEMA,
        "evidence_fingerprint": evidence_fingerprint,
        "reviewer": "",
        "cases": [
            {
                "id": case["id"],
                "ratings": {
                    label: {criterion.criterion_id: None for criterion in manifest.rubric}
                    for label in ("A", "B")
                },
                "preference": None,
                "notes": "",
            }
            for case in prepared_cases
        ],
    }
    packet = _render_packet(manifest, evidence_fingerprint, prepared_cases)
    return PreparedEvaluation(
        evidence_fingerprint=evidence_fingerprint,
        packet_markdown=packet,
        key_json=json.dumps(key, ensure_ascii=False, indent=2) + "\n",
        scores_json=json.dumps(scores, ensure_ascii=False, indent=2) + "\n",
    )


def _render_packet(
    manifest: EvaluationManifest,
    evidence_fingerprint: str,
    prepared_cases: Sequence[Mapping[str, Any]],
) -> str:
    rows = [
        f"# {manifest.title} — blinded review packet",
        "",
        f"Evaluation ID: `{manifest.evaluation_id}`  ",
        f"Evidence fingerprint: `{evidence_fingerprint}`",
        "",
        "Score every output from 1 (poor) to 5 (excellent) for each criterion. Judge only",
        "the supplied creative material and output. Record one overall preference—A, B, or tie—per",
        "case in the separate score sheet. Treatment, provider, model, and workflow metadata are",
        "intentionally omitted.",
        "",
        "## Rubric",
        "",
        "| Criterion | Description |",
        "| --- | --- |",
    ]
    rows.extend(
        f"| {_table_cell(criterion.label)} (`{criterion.criterion_id}`) | "
        f"{_table_cell(criterion.description)} |"
        for criterion in manifest.rubric
    )
    for case in prepared_cases:
        rows.extend(
            (
                "",
                f"## Case: {case['id']}",
                "",
                "### Creative material",
                "",
                _fenced(str(case["creative_brief"])),
            )
        )
        outputs = case["outputs"]
        if not isinstance(outputs, Mapping):
            raise AssertionError("prepared outputs must be a mapping")
        for label in ("A", "B"):
            rows.extend(("", f"### Output {label}", "", _fenced(str(outputs[label]))))
    return "\n".join(rows).rstrip() + "\n"


def _validate_key(data: Mapping[str, Any]) -> tuple[list[RubricCriterion], list[str]]:
    _exact(
        data,
        {
            "schema",
            "evaluation_id",
            "title",
            "evaluation_fingerprint",
            "evidence_fingerprint",
            "rubric",
            "treatments",
            "cases",
        },
        "evaluation key",
    )
    if data.get("schema") != EVALUATION_KEY_SCHEMA:
        raise ValueError(f"evaluation key schema must be '{EVALUATION_KEY_SCHEMA}'")
    for field in ("evaluation_fingerprint", "evidence_fingerprint"):
        value = data.get(field)
        if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
            raise ValueError(f"{field} must be a sha256 digest")
    _identifier_value(data.get("evaluation_id"), "evaluation id")
    _string(data, "title", maximum=160)
    raw_rubric = data.get("rubric")
    if not isinstance(raw_rubric, list) or not 1 <= len(raw_rubric) <= 8:
        raise ValueError("evaluation key rubric must contain between 1 and 8 criteria")
    rubric = [RubricCriterion.from_dict(item) for item in raw_rubric]
    criterion_ids = [criterion.criterion_id for criterion in rubric]
    if len(set(criterion_ids)) != len(criterion_ids):
        raise ValueError("evaluation key criterion identifiers must be unique")
    raw_treatments = data.get("treatments")
    if (
        not isinstance(raw_treatments, list)
        or len(raw_treatments) != 2
        or any(not isinstance(item, str) for item in raw_treatments)
    ):
        raise ValueError("evaluation key treatments must contain two identifiers")
    treatments = [_identifier_value(item, "treatment id") for item in raw_treatments]
    if len(set(treatments)) != 2:
        raise ValueError("evaluation key treatment identifiers must be unique")
    if treatments != sorted(treatments):
        raise ValueError("evaluation key treatment identifiers must be sorted")
    return rubric, treatments


def _validated_key_cases(
    data: Mapping[str, Any],
    treatments: Sequence[str],
) -> dict[str, Mapping[str, Any]]:
    raw_cases = data.get("cases")
    if not isinstance(raw_cases, list) or not 1 <= len(raw_cases) <= 100:
        raise ValueError("evaluation key must contain between 1 and 100 cases")
    cases: dict[str, Mapping[str, Any]] = {}
    evidence_fields = {
        "treatment_id",
        "generation_id",
        "run_digest",
        "content_digest",
        "workflow_id",
        "workflow_fingerprint",
        "calls",
        "max_requested_output_tokens",
        "duration_ms",
        "usage",
        "providers",
        "models",
    }
    for raw_case in raw_cases:
        if not isinstance(raw_case, Mapping):
            raise ValueError("each evaluation key case must be an object")
        _exact(raw_case, {"id", "assignments"}, "evaluation key case")
        case_id = _identifier_value(raw_case.get("id"), "case id")
        if case_id in cases:
            raise ValueError("evaluation key case identifiers must be unique")
        assignments = raw_case.get("assignments")
        if not isinstance(assignments, Mapping) or set(assignments) != {"A", "B"}:
            raise ValueError("evaluation key assignments must contain A and B")
        assignment_treatments: set[str] = set()
        for label in ("A", "B"):
            evidence = assignments[label]
            if not isinstance(evidence, Mapping):
                raise ValueError("each evaluation assignment must be an object")
            _exact(evidence, evidence_fields, "evaluation assignment")
            treatment_id = _identifier_value(evidence.get("treatment_id"), "treatment id")
            assignment_treatments.add(treatment_id)
            _string(evidence, "generation_id", maximum=128)
            _identifier_value(evidence.get("workflow_id"), "workflow id")
            for digest_field in (
                "run_digest",
                "content_digest",
                "workflow_fingerprint",
            ):
                digest = evidence.get(digest_field)
                if not isinstance(digest, str) or _DIGEST.fullmatch(digest) is None:
                    raise ValueError(f"{digest_field} must be a sha256 digest")
            for integer_field in (
                "calls",
                "max_requested_output_tokens",
                "duration_ms",
            ):
                value = evidence.get(integer_field)
                minimum = 0 if integer_field == "duration_ms" else 1
                if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
                    raise ValueError(
                        f"{integer_field} must be an integer greater than or equal to {minimum}"
                    )
            usage = evidence.get("usage")
            if not isinstance(usage, Mapping):
                raise ValueError("assignment usage must be an object")
            _exact(
                usage,
                {"input_tokens", "output_tokens", "total_tokens"},
                "assignment usage",
            )
            for value in usage.values():
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    raise ValueError("assignment usage values must be nonnegative integers")
            for list_field in ("providers", "models"):
                values = evidence.get(list_field)
                if (
                    not isinstance(values, list)
                    or not values
                    or any(
                        not isinstance(item, str) or not item or "\x00" in item or len(item) > 256
                        for item in values
                    )
                ):
                    raise ValueError(f"{list_field} must be an array of safe strings")
                if values != sorted(set(values)):
                    raise ValueError(f"{list_field} must contain sorted unique values")
        if assignment_treatments != set(treatments):
            raise ValueError("each key case must assign both treatments exactly once")
        cases[case_id] = assignments
    return cases


def _verify_evidence_fingerprint(
    key: Mapping[str, Any],
    key_cases: Mapping[str, Mapping[str, Any]],
) -> None:
    evidence_cases = []
    for case_id, assignments in key_cases.items():
        evidence_cases.append(
            {
                "id": case_id,
                "treatments": sorted(
                    (assignments["A"], assignments["B"]),
                    key=lambda item: str(item["treatment_id"]),
                ),
            }
        )
    expected = _canonical_digest(
        {
            "evaluation_fingerprint": key["evaluation_fingerprint"],
            "evaluation_id": key["evaluation_id"],
            "title": key["title"],
            "rubric": key["rubric"],
            "treatments": key["treatments"],
            "cases": evidence_cases,
        }
    )
    if key.get("evidence_fingerprint") != expected:
        raise ValueError("evaluation key evidence_fingerprint does not match its evidence")


def _validated_scores(
    data: Mapping[str, Any],
    evidence_fingerprint: str,
    case_ids: set[str],
    criterion_ids: Sequence[str],
) -> tuple[str, dict[str, Mapping[str, Any]]]:
    _exact(data, {"schema", "evidence_fingerprint", "reviewer", "cases"}, "score sheet")
    if data.get("schema") != SCORES_SCHEMA:
        raise ValueError(f"score sheet schema must be '{SCORES_SCHEMA}'")
    if data.get("evidence_fingerprint") != evidence_fingerprint:
        raise ValueError("score sheet evidence_fingerprint does not match the key")
    reviewer = _string(data, "reviewer", minimum=0, maximum=128)
    if "\r" in reviewer or "\n" in reviewer:
        raise ValueError("reviewer must be a single-line alias")
    raw_cases = data.get("cases")
    if not isinstance(raw_cases, list):
        raise ValueError("score sheet cases must be an array")
    scores: dict[str, Mapping[str, Any]] = {}
    for raw_case in raw_cases:
        if not isinstance(raw_case, Mapping):
            raise ValueError("each score case must be an object")
        _exact(raw_case, {"id", "ratings", "preference", "notes"}, "score case")
        case_id = _identifier_value(raw_case.get("id"), "case id")
        if case_id in scores:
            raise ValueError("score case identifiers must be unique")
        ratings = raw_case.get("ratings")
        if not isinstance(ratings, Mapping) or set(ratings) != {"A", "B"}:
            raise ValueError("ratings must contain A and B")
        for label in ("A", "B"):
            label_scores = ratings[label]
            if not isinstance(label_scores, Mapping) or set(label_scores) != set(criterion_ids):
                raise ValueError("each label must score every rubric criterion exactly once")
            for score in label_scores.values():
                if not isinstance(score, int) or isinstance(score, bool) or not 1 <= score <= 5:
                    raise ValueError("all rubric scores must be integers from 1 through 5")
        if raw_case.get("preference") not in {"A", "B", "tie"}:
            raise ValueError("preference must be A, B, or tie")
        notes = raw_case.get("notes")
        if not isinstance(notes, str) or "\x00" in notes or len(notes) > 5_000:
            raise ValueError("notes must be a safe string of at most 5000 characters")
        scores[case_id] = raw_case
    if set(scores) != case_ids:
        raise ValueError("score sheet must contain every evaluation case exactly once")
    return reviewer, scores


def build_evaluation_report(
    key_path: str | Path,
    scores_path: str | Path,
) -> EvaluationReport:
    """Validate, unblind, and aggregate one complete score sheet."""

    key = _read_json_object(key_path, "evaluation key")
    scores_data = _read_json_object(scores_path, "score sheet")
    try:
        rubric, treatments = _validate_key(key)
        key_cases = _validated_key_cases(key, treatments)
        _verify_evidence_fingerprint(key, key_cases)
        evidence_fingerprint = str(key["evidence_fingerprint"])
        reviewer, scores = _validated_scores(
            scores_data,
            evidence_fingerprint,
            set(key_cases),
            [criterion.criterion_id for criterion in rubric],
        )
    except ValueError as error:
        raise InputValidationError(f"invalid evaluation evidence: {error}") from error

    aggregates: dict[str, dict[str, Any]] = {
        treatment: {
            "criterion_scores": {criterion.criterion_id: [] for criterion in rubric},
            "preferences": 0,
            "calls": 0,
            "max_requested_output_tokens": 0,
            "duration_ms": 0,
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        }
        for treatment in treatments
    }
    report_cases: list[dict[str, Any]] = []
    ties = 0
    for case_id in key_cases:
        assignments = key_cases[case_id]
        score_case = scores[case_id]
        ratings = score_case["ratings"]
        case_ratings: dict[str, dict[str, int]] = {}
        for label in ("A", "B"):
            evidence = assignments[label]
            treatment = str(evidence["treatment_id"])
            treatment_ratings = {
                criterion.criterion_id: int(ratings[label][criterion.criterion_id])
                for criterion in rubric
            }
            case_ratings[treatment] = treatment_ratings
            aggregate = aggregates[treatment]
            for criterion_id, score in treatment_ratings.items():
                aggregate["criterion_scores"][criterion_id].append(score)
            for field in ("calls", "max_requested_output_tokens", "duration_ms"):
                aggregate[field] += int(evidence[field])
            for usage_field in ("input_tokens", "output_tokens", "total_tokens"):
                aggregate["usage"][usage_field] += int(evidence["usage"][usage_field])
        preference = str(score_case["preference"])
        if preference == "tie":
            preferred_treatment: Optional[str] = None
            ties += 1
        else:
            preferred_treatment = str(assignments[preference]["treatment_id"])
            aggregates[preferred_treatment]["preferences"] += 1
        report_cases.append(
            {
                "id": case_id,
                "ratings": case_ratings,
                "preference": preferred_treatment or "tie",
                "notes": score_case["notes"],
            }
        )

    treatment_reports: list[dict[str, Any]] = []
    for treatment in treatments:
        aggregate = aggregates[treatment]
        criteria = {
            criterion.criterion_id: round(
                math.fsum(aggregate["criterion_scores"][criterion.criterion_id])
                / len(aggregate["criterion_scores"][criterion.criterion_id]),
                3,
            )
            for criterion in rubric
        }
        treatment_reports.append(
            {
                "id": treatment,
                "criterion_means": criteria,
                "overall_mean": round(math.fsum(criteria.values()) / len(criteria), 3),
                "preferences": aggregate["preferences"],
                "calls": aggregate["calls"],
                "max_requested_output_tokens": aggregate["max_requested_output_tokens"],
                "duration_ms": aggregate["duration_ms"],
                "usage": aggregate["usage"],
            }
        )
    report_data = {
        "schema": EVALUATION_REPORT_SCHEMA,
        "evaluation_id": key["evaluation_id"],
        "title": key["title"],
        "evaluation_fingerprint": key["evaluation_fingerprint"],
        "evidence_fingerprint": evidence_fingerprint,
        "reviewer": reviewer,
        "case_count": len(key_cases),
        "rubric": [criterion.to_dict() for criterion in rubric],
        "treatments": treatment_reports,
        "ties": ties,
        "cases": report_cases,
    }
    return EvaluationReport(
        evidence_fingerprint=evidence_fingerprint,
        markdown=_render_report(report_data),
        json_text=json.dumps(report_data, ensure_ascii=False, indent=2) + "\n",
    )


def _render_report(report: Mapping[str, Any]) -> str:
    rubric = report["rubric"]
    treatments = report["treatments"]
    if not isinstance(rubric, list) or not isinstance(treatments, list):
        raise AssertionError("report collections must be lists")
    headings = (
        ["Treatment"]
        + [_table_cell(str(item["label"])) for item in rubric]
        + [
            "Overall",
            "Preferred",
            "Calls",
            "Reported tokens",
            "Duration ms",
        ]
    )
    rows = [
        f"# {report['title']} — evaluation report",
        "",
        f"Cases: {report['case_count']}  ",
        f"Ties: {report['ties']}  ",
        f"Reviewer alias: {report['reviewer'] or 'not supplied'}  ",
        f"Evidence fingerprint: `{report['evidence_fingerprint']}`",
        "",
        "| " + " | ".join(headings) + " |",
        "| " + " | ".join("---" for _ in headings) + " |",
    ]
    for treatment in treatments:
        criterion_means = treatment["criterion_means"]
        usage = treatment["usage"]
        values = [str(treatment["id"])]
        values.extend(str(criterion_means[item["id"]]) for item in rubric)
        values.extend(
            (
                str(treatment["overall_mean"]),
                str(treatment["preferences"]),
                str(treatment["calls"]),
                str(usage["total_tokens"]) if usage["total_tokens"] else "unreported",
                str(treatment["duration_ms"]),
            )
        )
        rows.append("| " + " | ".join(values) + " |")
    rows.extend(
        (
            "",
            "Scores are arithmetic summaries of this completed blinded review, not statistical",
            "proof of general quality or productivity. Provider-reported token counts may be",
            "unavailable;",
            "requested output caps are ceilings rather than actual spend.",
            "",
            "## Case outcomes",
            "",
        )
    )
    for case in report["cases"]:
        notes = str(case["notes"]).strip()
        rows.append(f"- `{case['id']}`: preferred **{case['preference']}**.")
        if notes:
            single_line_notes = notes.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
            rows.append(f"  Notes: {single_line_notes}")
    return "\n".join(rows).rstrip() + "\n"
