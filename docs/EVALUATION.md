# Blinded pairwise evaluation

Samsarix can turn completed `samsarix.run/v1` bundles into a deterministic human-review packet. This
workflow is local and provider-neutral: preparing or reporting an evaluation makes no model request and
requires no API credential.

Use it to compare exactly two named treatments across the same set of creative cases. A treatment can
represent a workflow revision, model, provider, prompt configuration, or any other deliberate change.
Every case must use the same two treatment IDs, and its two run bundles must contain exactly the same
creative brief.

## 1. Produce comparable run bundles

Run both treatments against each case and save the complete bundles. Keep all other variables as
controlled as the hypothesis requires. A useful directory looks like:

```text
evaluation/
  manifest.json
  runs/
    harbor-baseline.json
    harbor-candidate.json
    observatory-baseline.json
    observatory-candidate.json
```

The checked-in [manifest template](../examples/evaluations/manifest.template.json) demonstrates two
cases and three narrative criteria. Paths use forward slashes and are relative to the manifest
directory. Absolute paths, drive paths, backslashes, `.`, and `..` components are rejected.

## 2. Define the comparison before review

The strict `samsarix.evaluation/v1` manifest records:

- a portable evaluation ID and human title;
- a fixed seed used to assign each treatment to A or B independently per case;
- one to eight equally weighted rubric criteria;
- one to 100 cases, each containing exactly two run-bundle references.

Define the rubric and seed before looking at the compared outputs. Criteria should describe the intended
use rather than generic prose quality. For a quest handoff, for example, continuity, constraint fidelity,
branch clarity, and implementation readiness are more actionable than “good writing.”

The structural contract is [evaluation-v1.schema.json](../schemas/evaluation-v1.schema.json). The runtime
also enforces cross-case treatment identity, path containment, and matching creative briefs.

## 3. Prepare blind materials

Choose three new output paths:

```bash
samsarix-narrative evaluate prepare \
  --manifest evaluation/manifest.json \
  --packet evaluation/review-packet.md \
  --key evaluation/private-key.json \
  --scores evaluation/scores.json
```

The command writes:

- `review-packet.md`: creative material and outputs labeled only A and B;
- `private-key.json`: treatment assignments plus run, content, workflow, usage, and timing evidence;
- `scores.json`: an editable blinded score sheet.

Keep the key away from the reviewer until scoring is complete. The packet deliberately omits treatment,
provider, model, workflow, and generation identifiers. It still contains private creative material and
generated output, so it is not a public-safe redaction.

Preparation is reproducible for identical manifest and run-bundle evidence. A recorded SHA-256 evidence
fingerprint covers the manifest fingerprint and canonical evidence for every compared run. Formatting
changes to a valid run-bundle file do not change its canonical run digest.

All destinations are preflighted before the manifest is loaded. Existing files are preserved unless
`--force` is explicit, and every input/output path in one command must be distinct.

## 4. Complete the score sheet

Do not change IDs, labels, criteria, case order, or `evidence_fingerprint`. Fill:

- `reviewer` with a non-sensitive alias if desired;
- every null rubric score with an integer from 1 (poor) through 5 (excellent);
- each `preference` with `"A"`, `"B"`, or `"tie"`;
- optional case notes.

The generated sheet conforms structurally to [scores-v1.schema.json](../schemas/scores-v1.schema.json).
The report command additionally requires a complete score for every criterion and rejects missing,
unknown, duplicated, mismatched, or type-coerced values.

## 5. Unblind and report

After review:

```bash
samsarix-narrative evaluate report \
  --key evaluation/private-key.json \
  --scores evaluation/scores.json \
  --output evaluation/report.md \
  --json-output evaluation/report.json
```

The Markdown and JSON reports contain:

- per-treatment mean score for each criterion and an equal-weight overall mean;
- preference counts and ties;
- completed provider calls and requested output-token caps;
- provider-reported token totals and observed stage durations;
- unblinded case ratings, preferences, and reviewer notes.

Before reporting, Samsarix recomputes the key's evidence fingerprint. Editing an assignment, digest,
usage total, timing value, provider/model identity, or workflow fingerprint without regenerating the
evidence is rejected. This is an integrity check, not a digital signature, timestamp, authorship proof,
or defense against someone who can replace both evidence and software.

## Interpretation limits

The report is a descriptive arithmetic summary, not statistical proof that one treatment is generally
better. Creative-model outputs are variable; one run per case does not separate treatment effects from
sampling noise. A serious pilot should predeclare its hypothesis, cases, rubric, provider settings,
repetition policy, evaluator population, and stopping rule.

Useful follow-up measures include reviewer minutes, accepted/reused stages, invalid-output rate, full
rerun versus suffix-resume cost, and qualitative production notes. Provider-reported token counts can be
unavailable, and requested output-token caps are ceilings rather than actual spend.

The implementation starts with human pairwise review because direct comparison is often more practical
than an absolute score for creative output. Current LangSmith guidance likewise documents pairwise
comparison and randomized order as a positional-bias mitigation, while Anthropic's evaluation guidance
recommends specific, measurable, multidimensional success criteria:

- [LangSmith pairwise evaluation](https://docs.langchain.com/langsmith/evaluate-pairwise)
- [LangSmith evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts)
- [Anthropic: define success criteria](https://docs.anthropic.com/en/docs/test-and-evaluate/define-success)
- [OpenAI Evals API](https://platform.openai.com/docs/api-reference/evals)

Those hosted systems cover broader automated and online evaluation use cases. Samsarix's narrower value
is a dependency-free, local file workflow tied directly to portable narrative run provenance.
