# Security Policy

## Reporting a vulnerability

If you believe you have found a security vulnerability in the Cloud Locksmith Assessment CLI, please report it responsibly.

- **Email:** support.cloudlocksmith@gmail.com
- **Do not** open a public GitHub issue for security-sensitive reports.

Please include:

- a description of the issue and its potential impact,
- steps to reproduce (a minimal proof of concept if possible),
- the version/commit you tested,
- any relevant environment details.

We aim to acknowledge reports within a few business days and to keep you updated as we investigate. We will credit reporters who wish to be credited once a fix is available. Please give us reasonable time to remediate before any public disclosure.

## Scope

This is a **local, read-only** CLI. It uses delegated Microsoft Graph permissions, performs only `GET` requests, holds tokens in memory only, and transmits no data to Cloud Locksmith. Security reports of particular interest include:

- any path by which the tool could perform a **write** or modification against a tenant,
- any way tokens or tenant data could be **persisted or exfiltrated** unexpectedly,
- dependency vulnerabilities affecting the CLI,
- authentication handling flaws.

## What is not a vulnerability

- The tool reporting that your tenant has a weak posture — that is the tool working as intended.
- A control being `SKIPPED` because your tenant lacks Entra ID P1/P2 or admin consent.
- Approximate license pricing differing from your actual contract — these are clearly labeled estimates.

## Supported versions

Security fixes target the latest released version. Please test against `main` or the most recent release before reporting.
