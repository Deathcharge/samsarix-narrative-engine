# Samsarix Narrative Engine roadmap

This roadmap separates four gates: merge, release, publication, and flagship adoption. Passing one does not imply the next.

## Product boundary

Product role: **local-first narrative operations SDK** for developers, studios, and editorial teams that need inspectable workflows rather than an opaque writing surface. Promotion to a supported release still requires real users and a measured advantage over a simpler single-call baseline.

Current disposition: build the differentiated workflow, artifact, and evaluation layers on a verified default branch; release and adoption remain separate decisions.

Near-term product wedge:

- Treat narrative plans and drafts as versioned artifacts that people can review, edit, branch, and resume.
- Let teams define bounded, validated workflows for concrete editorial and game-narrative jobs.
- Make provider, prompt, cost, latency, and output comparisons reproducible without claiming an automatic quality win.
- Remain provider-neutral and local-first so unpublished intellectual property need not enter a Samsarix service.

## Stabilize the productized default

- Keep the default branch buildable from a clean checkout with exact-head CI and package-build evidence.
- Keep Samsarix LLC branding, package identity, MPL-2.0 metadata, compatibility aliases, and support contacts consistent.
- Preserve historical refs and use reviewable commits; do not rewrite or delete legacy history.
- Run capped live-adapter smokes only with owner-funded accounts and explicit spend approval.
- Keep the evidence inventory current in [COMPETITIVE_RESEARCH.md](docs/COMPETITIVE_RESEARCH.md).

## Release candidate

- Keep the shipped custom workflow contract and manuscript/game-narrative examples backward compatible.
- Run the implemented blinded evaluation workflow against a simpler single-call baseline.
- Publish fixtures, limits, digests, and reproducible results without overstating conclusions.
- Complete one documented pilot with a real consumer and capture measured time, cost, and acceptance signals.
- Tag a release only after wheel installation, CLI/API smoke, security, and hosted CI gates pass.

Current hardening backlog:

- Ownership-chain review remains an external legal step even though the repository now uses standard MPL-2.0 terms.
- Provider adapters are tested with injected clients, not owner-funded live calls against current models and accounts.
- No comparative corpus, regression evaluation, real user pilot, or evidence yet shows that staged workflows outperform a simpler baseline enough to justify their cost.
- Input-token cost is not bounded; model, API, and pricing churn require ongoing maintenance.
- Versioned run bundles, edit/resume branching, custom workflows, and blinded pairwise evaluation are
  implemented; a representative corpus and real pilot results remain.
- Final-stage streaming remains unimplemented and should follow demonstrated user demand.
- Consumer writing products are crowded; differentiation depends on the narrative-operations workflow, not built-in presets alone.

## Samsarix adoption

- Define a public API, event, schema, artifact, or deployment contract before connecting to Samsarix Unified.
- Add a consumer-owned contract fixture covering authentication, privacy, limits, errors, and version compatibility.
- Make one implementation canonical; remove or freeze duplicate behavior only after parity and rollback are proven.
- Record an owner, support level, compatibility window, and measurable adoption signal.

## Completion evidence

A milestone is complete only when its exact commit, commands and results, artifact digest, consumer or deployment, and rollback path are recorded in a pull request or release record. README claims must not exceed that evidence.
