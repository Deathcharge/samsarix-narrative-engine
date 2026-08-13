# Copyright 2026 Samsarix LLC and contributors.
# SPDX-License-Identifier: MPL-2.0

"""Deterministic blinded-evaluation workflow and evidence-integrity tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from samsarix_narrative_engine import (
    EVALUATION_REPORT_SCHEMA,
    EVALUATION_SCHEMA,
    SCORES_SCHEMA,
    EvaluationCase,
    EvaluationManifest,
    EvaluationTreatment,
    InputValidationError,
    NarrativeResult,
    RubricCriterion,
    StageResult,
    TokenUsage,
    build_evaluation_report,
    dumps_run_bundle,
    load_evaluation_manifest,
    prepare_evaluation,
    workflow_for_preset,
)
from samsarix_narrative_engine.cli import main


def _result(
    generation_id: str,
    brief: str,
    output: str,
    *,
    provider: str,
    input_tokens: int,
    output_tokens: int,
    duration_ms: int,
) -> NarrativeResult:
    workflow = workflow_for_preset("quick")
    return NarrativeResult(
        generation_id=generation_id,
        created_at="2026-08-10T12:00:00+00:00",
        preset="quick",
        title="Evaluation fixture",
        content=output,
        stages=(
            StageResult(
                stage_id="architect",
                role="Story architect",
                content="A structured plan.",
                provider=provider,
                model=f"{provider}-model",
                usage=TokenUsage(input_tokens, output_tokens, input_tokens + output_tokens),
                duration_ms=duration_ms,
                max_output_tokens=1_000,
            ),
            StageResult(
                stage_id="writer",
                role="Draft writer",
                content=output,
                provider=provider,
                model=f"{provider}-model",
                usage=TokenUsage(input_tokens, output_tokens, input_tokens + output_tokens),
                duration_ms=duration_ms,
                max_output_tokens=2_600,
            ),
        ),
        creative_brief=brief,
        workflow_fingerprint=workflow.fingerprint,
        workflow=workflow,
    )


def _manifest() -> EvaluationManifest:
    return EvaluationManifest(
        evaluation_id="fixture-comparison",
        title="Fixture comparison",
        seed="recorded-seed",
        rubric=(
            RubricCriterion(
                "continuity",
                "Continuity",
                "Preserves facts, motives, and causal links.",
            ),
            RubricCriterion(
                "readiness",
                "Production readiness",
                "Needs little editorial repair.",
            ),
        ),
        cases=(
            EvaluationCase(
                "harbor",
                (
                    EvaluationTreatment("baseline", "runs/harbor-baseline.json"),
                    EvaluationTreatment("candidate", "runs/harbor-candidate.json"),
                ),
            ),
            EvaluationCase(
                "observatory",
                (
                    EvaluationTreatment("baseline", "runs/observatory-baseline.json"),
                    EvaluationTreatment("candidate", "runs/observatory-candidate.json"),
                ),
            ),
        ),
    )


def _write_fixture_runs(root: Path) -> None:
    runs = root / "runs"
    runs.mkdir()
    fixtures = (
        (
            "harbor-baseline.json",
            _result(
                "harbor_baseline",
                "Write a harbor quest.",
                "# Harbor Bells\nThe old version.",
                provider="provider-one",
                input_tokens=10,
                output_tokens=5,
                duration_ms=11,
            ),
        ),
        (
            "harbor-candidate.json",
            _result(
                "harbor_candidate",
                "Write a harbor quest.",
                "# Harbor Bells\nThe revised version.",
                provider="provider-two",
                input_tokens=20,
                output_tokens=8,
                duration_ms=17,
            ),
        ),
        (
            "observatory-baseline.json",
            _result(
                "observatory_baseline",
                "Write an observatory quest.",
                "# Last Light\nThe older scene.",
                provider="provider-one",
                input_tokens=12,
                output_tokens=6,
                duration_ms=13,
            ),
        ),
        (
            "observatory-candidate.json",
            _result(
                "observatory_candidate",
                "Write an observatory quest.",
                "# Last Light\nThe polished scene.",
                provider="provider-two",
                input_tokens=22,
                output_tokens=9,
                duration_ms=19,
            ),
        ),
    )
    for filename, result in fixtures:
        (runs / filename).write_text(dumps_run_bundle(result), encoding="utf-8")


def _write_manifest(root: Path, manifest: EvaluationManifest | None = None) -> Path:
    path = root / "manifest.json"
    path.write_text(
        json.dumps((manifest or _manifest()).to_dict(), indent=2),
        encoding="utf-8",
    )
    return path


def _completed_scores(prepared_key: str, score_sheet: str) -> dict[str, Any]:
    key = json.loads(prepared_key)
    scores = json.loads(score_sheet)
    scores["reviewer"] = "reviewer-7"
    assignments_by_case = {case["id"]: case["assignments"] for case in key["cases"]}
    for case in scores["cases"]:
        assignments = assignments_by_case[case["id"]]
        for label in ("A", "B"):
            treatment_id = assignments[label]["treatment_id"]
            value = 5 if treatment_id == "candidate" else 2
            case["ratings"][label] = {"continuity": value, "readiness": value}
        case["preference"] = next(
            label for label in ("A", "B") if assignments[label]["treatment_id"] == "candidate"
        )
        case["notes"] = "Candidate required less repair."
    return scores


def test_manifest_round_trip_checked_in_template_and_published_schemas(
    tmp_path: Path,
) -> None:
    manifest_path = _write_manifest(tmp_path)
    loaded = load_evaluation_manifest(manifest_path)
    assert loaded == _manifest()
    assert loaded.treatment_ids == ("baseline", "candidate")
    assert loaded.fingerprint.startswith("sha256:")
    assert loaded.to_dict()["schema"] == EVALUATION_SCHEMA

    repository = Path(__file__).parents[1]
    template = load_evaluation_manifest(
        repository / "examples" / "evaluations" / "manifest.template.json"
    )
    assert len(template.cases) == 2
    for filename, schema_id in (
        ("evaluation-v1.schema.json", EVALUATION_SCHEMA),
        ("scores-v1.schema.json", SCORES_SCHEMA),
    ):
        schema = json.loads((repository / "schemas" / filename).read_text("utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["properties"]["schema"]["const"] == schema_id


@pytest.mark.parametrize(
    ("mutate", "message"),
    (
        (lambda data: data.pop("title"), "missing fields"),
        (lambda data: data.update(schema="other"), "schema"),
        (lambda data: data.update(extra=True), "unknown fields"),
        (lambda data: data.update(id="Upper"), "evaluation id"),
        (lambda data: data.update(title=""), "title"),
        (lambda data: data.update(title="bad\nheading"), "title"),
        (lambda data: data.update(seed=""), "seed"),
        (lambda data: data.update(rubric=[]), "rubric"),
        (lambda data: data.update(rubric="invalid"), "array"),
        (lambda data: data["rubric"].__setitem__(0, "invalid"), "criterion.*object"),
        (lambda data: data["rubric"][0].update(extra=True), "unknown fields"),
        (lambda data: data["rubric"][0].update(id="Upper"), "criterion id"),
        (lambda data: data["rubric"][0].update(label=""), "label"),
        (lambda data: data["rubric"][0].update(description=""), "description"),
        (lambda data: data["rubric"].append(dict(data["rubric"][0])), "criterion.*unique"),
        (lambda data: data.update(cases=[]), "cases"),
        (lambda data: data.update(cases="invalid"), "array"),
        (lambda data: data["cases"].__setitem__(0, "invalid"), "case.*object"),
        (lambda data: data["cases"][0].update(extra=True), "unknown fields"),
        (lambda data: data["cases"][0].update(treatments=[]), "two treatments"),
        (
            lambda data: data["cases"][0]["treatments"].__setitem__(0, "invalid"),
            "treatment.*object",
        ),
        (lambda data: data["cases"].append(dict(data["cases"][0])), "case.*unique"),
        (
            lambda data: data["cases"][0]["treatments"][0].update(run_bundle="../run.json"),
            "stay within",
        ),
        (
            lambda data: data["cases"][0]["treatments"][0].update(run_bundle="."),
            "stay within",
        ),
        (
            lambda data: data["cases"][0]["treatments"][0].update(run_bundle="./run.json"),
            "stay within",
        ),
        (
            lambda data: data["cases"][0]["treatments"][0].update(run_bundle="C:/run.json"),
            "drive",
        ),
        (
            lambda data: data["cases"][0]["treatments"][0].update(run_bundle="/run.json"),
            "stay within",
        ),
        (
            lambda data: data["cases"][0]["treatments"][0].update(run_bundle="runs\\run.json"),
            "portable",
        ),
        (
            lambda data: data["cases"][0]["treatments"][0].update(id="candidate"),
            "unique",
        ),
        (
            lambda data: data["cases"][1]["treatments"][1].update(id="challenger"),
            "same two",
        ),
    ),
)
def test_manifest_loader_strictly_rejects_invalid_contracts(
    tmp_path: Path,
    mutate: Any,
    message: str,
) -> None:
    data = _manifest().to_dict()
    mutate(data)
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(InputValidationError, match=message):
        load_evaluation_manifest(path)


def test_manifest_loader_sanitizes_file_json_and_size_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    with pytest.raises(InputValidationError, match="line 1, column 2"):
        load_evaluation_manifest(malformed)
    wrong_shape = tmp_path / "array.json"
    wrong_shape.write_text("[]", encoding="utf-8")
    with pytest.raises(InputValidationError, match="JSON object"):
        load_evaluation_manifest(wrong_shape)
    invalid_utf8 = tmp_path / "invalid.json"
    invalid_utf8.write_bytes(b"\xff")
    with pytest.raises(InputValidationError, match="cannot read UTF-8"):
        load_evaluation_manifest(invalid_utf8)
    with pytest.raises(InputValidationError, match="cannot read UTF-8"):
        load_evaluation_manifest(tmp_path / "missing.json")

    manifest_path = _write_manifest(tmp_path)
    monkeypatch.setattr("samsarix_narrative_engine.evaluation.MAX_EVALUATION_BYTES", 10)
    with pytest.raises(InputValidationError, match="exceeds 10 bytes"):
        load_evaluation_manifest(manifest_path)


def test_prepare_is_deterministic_blind_and_evidence_backed(tmp_path: Path) -> None:
    _write_fixture_runs(tmp_path)
    prepared = prepare_evaluation(_manifest(), tmp_path)
    repeated = prepare_evaluation(_manifest(), tmp_path)
    assert prepared == repeated
    assert prepared.evidence_fingerprint.startswith("sha256:")
    assert "provider-one" not in prepared.packet_markdown
    assert "provider-two" not in prepared.packet_markdown
    assert "baseline" not in prepared.packet_markdown
    assert "candidate" not in prepared.packet_markdown
    assert "quick" not in prepared.packet_markdown
    assert "# Harbor Bells" in prepared.packet_markdown

    key = json.loads(prepared.key_json)
    scores = json.loads(prepared.scores_json)
    assert key["evidence_fingerprint"] == prepared.evidence_fingerprint
    assert key["treatments"] == ["baseline", "candidate"]
    assert scores["evidence_fingerprint"] == prepared.evidence_fingerprint
    assert scores["cases"][0]["preference"] is None
    assert scores["cases"][0]["ratings"]["A"]["continuity"] is None
    assignments = key["cases"][0]["assignments"]
    assert {item["treatment_id"] for item in assignments.values()} == {
        "baseline",
        "candidate",
    }
    assert all(item["run_digest"].startswith("sha256:") for item in assignments.values())


def test_prepare_rejects_mismatched_briefs_and_wrong_runtime_type(
    tmp_path: Path,
) -> None:
    _write_fixture_runs(tmp_path)
    candidate = tmp_path / "runs" / "harbor-candidate.json"
    changed = _result(
        "changed",
        "A different brief.",
        "# Different\nOutput.",
        provider="provider-two",
        input_tokens=1,
        output_tokens=1,
        duration_ms=1,
    )
    candidate.write_text(dumps_run_bundle(changed), encoding="utf-8")
    with pytest.raises(InputValidationError, match="same creative brief"):
        prepare_evaluation(_manifest(), tmp_path)
    with pytest.raises(TypeError, match="EvaluationManifest"):
        prepare_evaluation(object(), tmp_path)  # type: ignore[arg-type]


def test_report_unblinds_scores_and_operational_evidence(tmp_path: Path) -> None:
    _write_fixture_runs(tmp_path)
    prepared = prepare_evaluation(_manifest(), tmp_path)
    key_path = tmp_path / "private-key.json"
    scores_path = tmp_path / "scores.json"
    key_path.write_text(prepared.key_json, encoding="utf-8")
    scores_path.write_text(
        json.dumps(_completed_scores(prepared.key_json, prepared.scores_json)),
        encoding="utf-8",
    )

    report = build_evaluation_report(key_path, scores_path)
    data = json.loads(report.json_text)
    assert data["schema"] == EVALUATION_REPORT_SCHEMA
    assert data["case_count"] == 2
    assert data["reviewer"] == "reviewer-7"
    assert data["ties"] == 0
    treatment_data = {item["id"]: item for item in data["treatments"]}
    assert treatment_data["candidate"]["overall_mean"] == 5.0
    assert treatment_data["candidate"]["preferences"] == 2
    assert treatment_data["candidate"]["calls"] == 4
    assert treatment_data["candidate"]["max_requested_output_tokens"] == 7_200
    assert treatment_data["candidate"]["duration_ms"] == 72
    assert treatment_data["candidate"]["usage"]["total_tokens"] == 118
    assert treatment_data["baseline"]["overall_mean"] == 2.0
    assert "not statistical" in report.markdown
    assert "proof of general quality" in report.markdown
    assert "Candidate required less repair." in report.markdown


def test_report_counts_ties_without_awarding_a_preference(tmp_path: Path) -> None:
    _write_fixture_runs(tmp_path)
    prepared = prepare_evaluation(_manifest(), tmp_path)
    scores = _completed_scores(prepared.key_json, prepared.scores_json)
    scores["cases"][0]["preference"] = "tie"
    scores["cases"][0]["notes"] = "Both\nwere usable."
    key_path = tmp_path / "key.json"
    scores_path = tmp_path / "scores.json"
    key_path.write_text(prepared.key_json, encoding="utf-8")
    scores_path.write_text(json.dumps(scores), encoding="utf-8")

    report = build_evaluation_report(key_path, scores_path)
    data = json.loads(report.json_text)
    assert data["ties"] == 1
    assert data["cases"][0]["preference"] == "tie"
    candidate = next(item for item in data["treatments"] if item["id"] == "candidate")
    assert candidate["preferences"] == 1
    assert "Both were usable." in report.markdown


def test_report_fingerprint_binds_blind_assignment_labels(tmp_path: Path) -> None:
    _write_fixture_runs(tmp_path)
    prepared = prepare_evaluation(_manifest(), tmp_path)
    key = json.loads(prepared.key_json)
    scores = _completed_scores(prepared.key_json, prepared.scores_json)
    assignments = key["cases"][0]["assignments"]
    assignments["A"], assignments["B"] = assignments["B"], assignments["A"]
    key_path = tmp_path / "key.json"
    scores_path = tmp_path / "scores.json"
    key_path.write_text(json.dumps(key), encoding="utf-8")
    scores_path.write_text(json.dumps(scores), encoding="utf-8")

    with pytest.raises(InputValidationError, match="evidence_fingerprint"):
        build_evaluation_report(key_path, scores_path)


@pytest.mark.parametrize(
    ("target", "mutate", "message"),
    (
        (
            "scores",
            lambda data: data.update(schema="other"),
            "score sheet schema",
        ),
        (
            "scores",
            lambda data: data.update(evidence_fingerprint="sha256:" + "0" * 64),
            "does not match",
        ),
        (
            "scores",
            lambda data: data.update(reviewer="two\nlines"),
            "single-line",
        ),
        (
            "scores",
            lambda data: data["cases"][0]["ratings"]["A"].update(continuity=None),
            "integers from 1 through 5",
        ),
        (
            "scores",
            lambda data: data["cases"][0]["ratings"].pop("B"),
            "ratings must contain",
        ),
        (
            "scores",
            lambda data: data["cases"][0]["ratings"]["A"].pop("continuity"),
            "every rubric criterion",
        ),
        (
            "scores",
            lambda data: data["cases"][0].update(notes=None),
            "notes",
        ),
        (
            "scores",
            lambda data: data["cases"][0].update(preference=None),
            "preference",
        ),
        (
            "scores",
            lambda data: data["cases"].pop(),
            "every evaluation case",
        ),
        (
            "scores",
            lambda data: data["cases"].append(data["cases"][0]),
            "case identifiers must be unique",
        ),
        (
            "key",
            lambda data: data.update(schema="other"),
            "evaluation key schema",
        ),
        (
            "key",
            lambda data: data.update(evaluation_fingerprint="invalid"),
            "sha256 digest",
        ),
        (
            "key",
            lambda data: data["treatments"].reverse(),
            "must be sorted",
        ),
        (
            "key",
            lambda data: data["cases"][0]["assignments"].pop("B"),
            "assignments must contain",
        ),
        (
            "key",
            lambda data: data["cases"][0]["assignments"]["A"].update(duration_ms=999),
            "evidence_fingerprint",
        ),
        (
            "key",
            lambda data: data["cases"][0]["assignments"]["A"].update(calls=0),
            "greater than or equal to 1",
        ),
        (
            "key",
            lambda data: data["cases"][0]["assignments"]["A"]["usage"].update(total_tokens=-1),
            "usage values",
        ),
        (
            "key",
            lambda data: data["cases"][0]["assignments"]["A"].update(providers=[]),
            "array of safe strings",
        ),
        (
            "key",
            lambda data: data["cases"][0]["assignments"]["A"].update(providers=["z", "a"]),
            "sorted unique",
        ),
        (
            "key",
            lambda data: data["rubric"][0].update(label="Changed criterion"),
            "evidence_fingerprint",
        ),
        (
            "key",
            lambda data: data["cases"][0]["assignments"]["A"].update(extra=True),
            "unknown fields",
        ),
        (
            "key",
            lambda data: data["cases"].append(data["cases"][0]),
            "case identifiers must be unique",
        ),
    ),
)
def test_report_rejects_incomplete_mismatched_or_tampered_evidence(
    tmp_path: Path,
    target: str,
    mutate: Any,
    message: str,
) -> None:
    _write_fixture_runs(tmp_path)
    prepared = prepare_evaluation(_manifest(), tmp_path)
    key = json.loads(prepared.key_json)
    scores = _completed_scores(prepared.key_json, prepared.scores_json)
    mutate(key if target == "key" else scores)
    key_path = tmp_path / "key.json"
    scores_path = tmp_path / "scores.json"
    key_path.write_text(json.dumps(key), encoding="utf-8")
    scores_path.write_text(json.dumps(scores), encoding="utf-8")
    with pytest.raises(InputValidationError, match=message):
        build_evaluation_report(key_path, scores_path)


def test_cli_prepares_and_reports_without_constructing_a_provider(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_fixture_runs(tmp_path)
    manifest_path = _write_manifest(tmp_path)
    packet = tmp_path / "out" / "packet.md"
    key = tmp_path / "out" / "key.json"
    scores = tmp_path / "out" / "scores.json"
    provider_calls = 0

    def provider_factory(*_args: Any, **_kwargs: Any) -> Any:
        nonlocal provider_calls
        provider_calls += 1
        raise AssertionError("evaluation must not construct a provider")

    assert (
        main(
            (
                "evaluate",
                "prepare",
                "--manifest",
                str(manifest_path),
                "--packet",
                str(packet),
                "--key",
                str(key),
                "--scores",
                str(scores),
            ),
            provider_factory=provider_factory,
        )
        == 0
    )
    assert provider_calls == 0
    assert packet.exists() and key.exists() and scores.exists()
    assert "keep the key, manifest, and source bundles" in capsys.readouterr().err

    completed = _completed_scores(
        key.read_text("utf-8"),
        scores.read_text("utf-8"),
    )
    scores.write_text(json.dumps(completed), encoding="utf-8")
    markdown_report = tmp_path / "out" / "report.md"
    json_report = tmp_path / "out" / "report.json"
    assert (
        main(
            (
                "evaluate",
                "report",
                "--key",
                str(key),
                "--scores",
                str(scores),
                "--output",
                str(markdown_report),
                "--json-output",
                str(json_report),
            ),
            provider_factory=provider_factory,
        )
        == 0
    )
    assert provider_calls == 0
    assert "evaluation report" in markdown_report.read_text("utf-8")
    assert json.loads(json_report.read_text("utf-8"))["case_count"] == 2
    assert "Wrote unblinded" in capsys.readouterr().err


def test_cli_evaluation_preflights_all_paths_before_reading_or_writing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    collision = tmp_path / "same.json"
    assert (
        main(
            (
                "evaluate",
                "prepare",
                "--manifest",
                str(collision),
                "--packet",
                str(collision),
                "--key",
                str(tmp_path / "key.json"),
                "--scores",
                str(tmp_path / "scores.json"),
            )
        )
        == 4
    )
    assert "different files" in capsys.readouterr().err
    assert not (tmp_path / "key.json").exists()

    _write_fixture_runs(tmp_path)
    manifest = _write_manifest(tmp_path)
    existing = tmp_path / "existing.md"
    existing.write_text("keep", encoding="utf-8")
    key = tmp_path / "key.json"
    scores = tmp_path / "scores.json"
    assert (
        main(
            (
                "evaluate",
                "prepare",
                "--manifest",
                str(manifest),
                "--packet",
                str(existing),
                "--key",
                str(key),
                "--scores",
                str(scores),
            )
        )
        == 4
    )
    assert existing.read_text("utf-8") == "keep"
    assert not key.exists()
    assert not scores.exists()
    assert "--force" in capsys.readouterr().err


def test_evaluation_value_objects_enforce_runtime_types() -> None:
    with pytest.raises(ValueError, match="between 1 and 8"):
        replace(_manifest(), rubric=[])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="RubricCriterion"):
        replace(_manifest(), rubric=("bad",))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="EvaluationCase"):
        replace(_manifest(), cases=("bad",))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="exactly two"):
        replace(_manifest().cases[0], treatments=[])  # type: ignore[arg-type]
