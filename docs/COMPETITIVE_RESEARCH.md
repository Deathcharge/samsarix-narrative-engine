# Competitive research and product direction

**Research date:** 2026-08-08
**Status:** Directional desk research, not market validation

This note records the evidence behind the near-term product direction. It deliberately avoids market-size,
quality, and adoption claims that have not been measured.

## What adjacent products make table stakes

| Category | Publicly documented capability | Implication for Samsarix |
| --- | --- | --- |
| AI fiction workspaces | Sudowrite documents a Story Bible, chapter continuity, and project support for a connected series. | Character, world, outline, and continuity context are expected; a fixed multi-agent preset is not enough differentiation. |
| Lore-driven generators | NovelAI documents Lorebook activation, story export, and branching through duplicate stories. | Portable context, export, and nondestructive branches are baseline expectations. |
| Planning software | Plottr advertises visual timelines, scene cards, story bibles, templates, and series organization. | Professional users need structured planning artifacts and cross-project continuity, not only final prose. |
| Agent infrastructure | LangGraph documents durable execution, persistence, and human-in-the-loop interrupts. | Developers already expect workflows to pause, survive, accept review, and resume deterministically. |
| Interchange and telemetry | JSON Schema 2020-12 and OpenTelemetry semantic conventions provide mature standards for validation and observability. | Samsarix should use explicit, versioned contracts and interoperable telemetry instead of bespoke claims. |

Sources:

- [Sudowrite Story Bible](https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/what-is-story-bible/jmWepHcQdJetNrE991fjJC)
- [Sudowrite chapter continuity](https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/chapter-continuity/4KL8gFeLZQ6GSBjDWtSbV6)
- [Sudowrite series support](https://docs.sudowrite.com/using-sudowrite/1ow1qkGqof9rtcyGnrWUBS/series-support/3vfbZPCB1ANLm75FXmJf28)
- [NovelAI Lorebook](https://docs.novelai.net/en/text/lorebook/) and [FAQ](https://docs.novelai.net/en/faq/)
- [Plottr features](https://plottr.com/features/) and [series bible](https://plottr.com/series-bible-software/)
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) and
  [human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)
- [JSON Schema specification](https://json-schema.org/specification)
- [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/)

These pages describe vendor capabilities, not independent evidence of product quality or customer demand.

## Chosen wedge: narrative operations

Samsarix should not compete first as a polished consumer editor. Its credible wedge is a local-first,
provider-neutral workflow SDK for teams that treat narrative work as a production process:

1. Plan the bounded calls and output ceilings before spend.
2. Capture every accepted intermediate as a versioned artifact.
3. Let a human or program revise an artifact and rerun only the affected suffix.
4. Preserve lineage, workflow identity, provider usage, and timing for every branch.
5. Compare workflows and providers through blinded, reproducible evaluations.
6. Integrate through a typed Python API, CLI, and stable JSON contracts.

The `samsarix.run/v1` bundle and edit/resume flow implement the first meaningful slice of that wedge.
They are local files, not proof of durability, collaboration, or provenance outside the current machine.

## Initial real-world use cases

### Editorial handoff and revision branches

An editor accepts an outline and character pass, corrects the continuity artifact, and regenerates only
the draft. The original run remains a rollback point and the branch records its parent.

### Game narrative and quest pipelines

A team defines stages such as quest constraints, beat design, dialogue, lore validation, and implementation
notes. Stage dependencies make the context passed to each specialist explicit, while hard ceilings make
batch jobs reviewable before provider spend.

### Studio QA and migration

A studio runs the same fixtures against two workflow revisions, providers, or models. A blinded reviewer
scores outputs without seeing the treatment, while the bundle records inputs, stage configuration, usage,
latency, and digests needed to reproduce the comparison.

### Local and IP-sensitive workflows

Teams can run the engine from their own environment and retain artifacts locally. This reduces the need
for a Samsarix-hosted content store, but provider data handling still depends on the provider and account
configuration selected by the user.

## Build sequence

1. **Implemented:** strict versioned run bundles, workflow fingerprints, edit/resume branching, lineage,
   and suffix-only budget preflight.
2. **Next:** bounded custom workflow specifications with explicit dependencies and useful checked-in
   examples.
3. **Next:** deterministic evaluation manifests, blinded review packets, scoring import, and comparison
   reports.
4. **Then:** structured story-bible/continuity artifacts and optional OpenTelemetry-compatible events,
   driven by pilot needs.
5. **Later, only with evidence:** hosted collaboration, streaming, visual editing, or vendor-specific
   optimizations.

## Validation plan

A pilot should compare Samsarix with a one-call baseline on the same fixtures and provider configuration.
Before running it, record the hypothesis, rubric, randomization method, evaluator, call caps, output caps,
and stopping rule.

Minimum signals:

- blind rubric scores and preference counts, including ties;
- reviewer minutes and number of accepted/reused stages;
- provider-reported tokens, calls, and wall-clock duration;
- revision scope: full rerun versus suffix rerun;
- failures, invalid outputs, and workflow-drift refusals;
- qualitative notes from at least one intended user.

A staged workflow earns continued investment only if the measured editorial value or operational control
justifies its additional calls and complexity. Until then, the project should make capability claims, not
quality or productivity claims.
