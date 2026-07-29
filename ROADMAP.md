# Samsarix Narrative Engine roadmap

This roadmap separates four gates: merge, release, publication, and flagship adoption. Passing one does not imply the next.

## Product boundary

Portfolio role: **experiment or learning project**. Keep this as an evidence-producing experiment or reference. Promotion to a supported product requires a real consumer and a measured advantage over the simpler alternative.

Current disposition: Merge the productization branch after exact-head verification and rollback-ref creation; release and adoption remain separate decisions.

## Stabilize the productized default

- Keep the default branch buildable from a clean checkout and preserve exact-head CI evidence.
- Keep Samsarix LLC branding, package identity, license metadata, and compatibility aliases internally consistent.
- Preserve the pre-productization default under a rollback ref before merging; do not delete legacy history.
- Review priority: Authorize license.
- Review priority: verify hosted CI/wheel.
- Review priority: run capped live adapter smokes and blinded multi-stage-versus-single-call evaluation.

## Release candidate

- Define a falsifiable evaluation against a simpler baseline.
- Publish fixtures, limits, and reproducible results without overstating conclusions.
- Tag and freeze a useful reference if the experiment does not earn adoption.

Current hardening backlog:

- Material BSL-to-MPL relicensing is unresolved.
- Provider adapters are tested with injected clients, not owner-funded live calls against current models/accounts.
- No comparative output corpus, regression evaluation, real writer pilot, or evidence that multiple editorial calls improve results enough to justify cost.
- Input-token cost is not bounded, and model/API/pricing churn creates ongoing maintenance.
- No resume-from-stage, final-stage streaming, or artifact replay/edit workflow exists.
- The market is crowded and the preset orchestration is only weak-to-moderately differentiated.

## Samsarix adoption

- Define a public API, event, schema, artifact, or deployment contract before connecting to Samsarix Unified.
- Add a consumer-owned contract fixture covering authentication, privacy, limits, errors, and version compatibility.
- Make one implementation canonical; remove or freeze duplicate behavior only after parity and rollback are proven.
- Record an owner, support level, compatibility window, and measurable adoption signal.

## Completion evidence

A milestone is complete only when its exact commit, commands and results, artifact digest, consumer or deployment, and rollback path are recorded in a pull request or release record. README claims must not exceed that evidence.
