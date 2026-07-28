# Security policy

## Supported versions

Until the first published release, security fixes are made on the default development branch. A
supported-version table will be added when releases exist.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting for this repository if it is enabled. Do not place API
keys, private prompts, generated private content, or exploit details in a public issue. If private
reporting is unavailable, contact the repository owner through the private contact method published on
their GitHub profile and include only enough non-sensitive information to establish contact.

The owner still needs to configure and publish a dedicated security contact. That external release gate
is tracked in `docs/PRODUCTIZATION.md`.

## Scope and expectations

Reports about credential exposure, unsafe file replacement, dependency compromise, prompt/content
leakage, or unexpected paid-provider amplification are in scope. Model output quality and provider-side
availability are not security guarantees made by this package, but reproducible failures that bypass
documented limits are welcome.
