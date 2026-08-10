# Custom workflows

`samsarix.workflow/v1` is the portable contract for narrative operations that do not fit the three
built-in story presets. It deliberately describes a bounded ordered pipeline, not an open-ended agent
graph.

## Smallest valid definition

```json
{
  "schema": "samsarix.workflow/v1",
  "id": "studio.scene-pass",
  "name": "Studio scene pass",
  "stages": [
    {
      "id": "diagnosis",
      "role": "Scene editor",
      "system_prompt": "Identify the scene objective, conflict, turn, and revision risks.",
      "max_output_tokens": 600,
      "context_from": []
    },
    {
      "id": "revision",
      "role": "Scene reviser",
      "system_prompt": "Return the complete revised scene with one Markdown H1 title.",
      "max_output_tokens": 1800,
      "context_from": ["diagnosis"]
    }
  ]
}
```

The creative brief is sent to every stage. `context_from` selects which completed stage artifacts are
also sent. The engine serializes this author-controlled material as JSON and tells the model not to
treat it as commands or external evidence. It does not expose tools, retrieval, shell access, or files
to a stage.

The last stage is the run's primary `content`. Earlier results remain addressable in `stages` and in the
persisted run bundle.

## Validation and limits

The runtime rejects a definition before provider construction unless all of these hold:

- the workflow contains 1–20 stages and no unknown or missing fields;
- workflow and stage IDs use their documented lowercase portable forms and are unique;
- every `context_from` value names a unique earlier stage—never the current or a future stage;
- roles and prompts are nonempty, bounded strings without null bytes;
- every stage output cap is 1–32,768 and the aggregate is at most 100,000;
- the UTF-8 JSON file is at most 1 MiB.

The default `WorkflowRunOptions` is intentionally tighter: seven calls and 10,000 requested output
tokens. A larger valid workflow still requires the caller to raise both limits explicitly.

The companion [JSON Schema](../schemas/workflow-v1.schema.json) handles structural validation in editors
and external tools. The Python loader remains authoritative for dependency order and aggregate caps,
which JSON Schema cannot express cleanly.

## Plan before execution

```bash
samsarix-narrative plan --workflow path/to/workflow.json
samsarix-narrative plan --workflow path/to/workflow.json --from-stage revision --json
```

Planning loads and validates the definition but does not construct a provider, read a key, or make a
network request. Use the output as an approval artifact for the exact call count and requested output
ceiling. Input tokens remain provider-dependent.

Run through the CLI:

```bash
samsarix-narrative generate --workflow path/to/workflow.json --prompt-file brief.md --output result.md --artifacts run.json --max-calls 4 --max-total-output-tokens 5500
```

Or through Python:

```python
from samsarix_narrative_engine import (
    NarrativeEngine,
    WorkflowRunOptions,
    load_workflow,
)

workflow = load_workflow("path/to/workflow.json")
result = await NarrativeEngine(provider).run(
    creative_material,
    workflow,
    WorkflowRunOptions(max_calls=4, max_total_output_tokens=5_500),
)
```

## Review and evolution

Every `samsarix.run/v1` bundle embeds the exact workflow and its fingerprint. A normal resume needs no
separate workflow file:

```bash
samsarix-narrative resume --artifacts-in reviewed-run.json --from-stage revision --artifacts-out branch.json --max-calls 1 --max-total-output-tokens 1800
```

To migrate a run, pass a reviewed replacement definition and `--allow-workflow-change`. Reused stages
before `--from-stage` must remain identical; otherwise their artifacts would be falsely attributed to a
prompt or role that did not produce them. If an earlier stage changed, resume from that earliest changed
stage.

The fingerprint detects drift but is not a digital signature, ownership proof, or tamper-proof ledger.
Git signatures or an external artifact store can add those properties when a deployment requires them.

## Starting points

- [Editorial scene revision](../examples/workflows/editorial-scene-revision.json) ends in revised prose.
- [Game quest production](../examples/workflows/game-quest-production.json) ends in an implementation
  packet with explicit state and edge-case notes.

Copy one under a new ID, keep the final deliverable as the last stage, and add only context edges that
the receiving stage genuinely needs. Smaller context reduces input cost and limits accidental coupling.

Workflow files contain executable system prompts. Structural validity does not imply trust: review
third-party definitions like source code before sending private narrative material through them.
