# Security

This is an early project. Security fixes are developed against `main`; there is
no promise of maintained older release branches.

Report vulnerabilities privately through
[GitHub private vulnerability reporting](https://github.com/arjungowdal4601/everymd/security/advisories/new).
Include reproduction steps, the affected version and the likely impact.
Do not post credentials or exploit details in a public issue. The repository
owner must enable private reporting on the public repository before release;
if the link is unavailable, ask the maintainer on GitHub for a private channel.

Only pass trusted URLs. URL conversion uses a browser and follows linked
resources; it can reach internal network addresses. The converter is not a
network sandbox or a server-side URL allowlist. Isolate it and restrict network
access when integrating it into a service.

Treat downloaded documents as untrusted input. Keep Docker and the pinned
dependencies updated, run conversions in a separate process and check output
before relying on important numbers or conditions. Never include `.env`,
API keys, passwords or access tokens in a report.
