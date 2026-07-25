# Security Policy & Posture

[🇩🇪 Deutsche Version](SECURITY.de.md)

`swiss-geodata-mcp` was audited against the internal MCP best-practice
catalogue (68 checks, 8 categories). The latest run
(`audits/2026-07-25T160123-Z-swiss-geodata-mcp/`) scored **25 pass / 7 partial /
0 fail** across the 32 applicable checks — **production-ready, no
security-impacting findings open**. This document summarises the security
posture and the **accepted-risk** decisions for controls that are deliberately
deferred for this read-only, no-PII, public-open-data server profile.

## Reporting a vulnerability

Please open a private security advisory on the GitHub repository, or contact the
maintainer listed in `README.md`. Do not file public issues for exploitable
vulnerabilities.

## Posture summary

All tools only **query** the federal geodata infrastructure — there is no write
path, no authentication, and no personal data. Hardening in place:

| Area | Control |
|---|---|
| Egress | HTTPS-only allow-list to the geo.admin.ch hosts (`api3.geo.admin.ch`, `geodesy.geo.admin.ch`), enforced by `_assert_host_allowed` before every outbound request |
| TLS | Certificate verification on by default (httpx default; never disabled) |
| Transport | stdio by default — stdout reserved for the JSON-RPC stream; HTTP transports bind to loopback (`127.0.0.1`) unless `HOST=0.0.0.0` is set explicitly (SEC-016) |
| Input | Pydantic v2 validation on every tool input; LV95 coordinates plausibility-checked with an actionable error pointing to `geo_convert_coordinates` |
| Secrets | No API keys or credentials — geo.admin.ch is fully public, so there is nothing to store or leak |
| Errors | Upstream bodies and stack traces logged to stderr only; the model sees a generic, sanitised message (`_handle_error`) |
| Stdout | Reserved for the JSON-RPC stream; logging pinned to stderr via `basicConfig` |
| Connections | One shared `httpx.AsyncClient` opened via the server lifespan, not per call |
| Tests | respx-mocked unit suite on every PR (3.11/3.12/3.13); live API tests gated to a nightly job |

See `audits/` for the full report and `CHANGELOG.md` for the hardening history.

### Audit finding fixed in the first run

**SEC-016 (0.0.0.0 binding / NeighborJack)** — the HTTP transports previously
defaulted `HOST` to `0.0.0.0`, exposing all interfaces. Fixed to default to
`127.0.0.1`; exposing all interfaces now requires an explicit `HOST=0.0.0.0`
opt-in. stdio (the default transport) does not bind at all.

## Accepted risks

The following controls are deliberately **out of scope** for a stdio-only
public-open-data server. None has a security impact for this profile.

### Container sandboxing

**Status:** accepted risk.
No `Dockerfile`. Acceptable for local-stdio public-data servers — defense-in-depth
lives at the OS user level. Ship a hardened image if the deployment profile ever
moves to the cloud.

### Structured logging

**Status:** accepted risk.
Logging to stderr is sufficient for a stdio server. JSON-structured logs with
trace IDs are not justified here; revisit if the server is lifted to a
cloud/SSE deployment.

### Rate limiting / quota

**Status:** accepted risk.
geo.admin.ch is a public service without per-key quota; the server relies on
retry-with-backoff rather than client-side rate limiting.

## Re-evaluation triggers

These acceptances should be revisited if the server ever:

- gains **write** capability or starts processing **PII**, or
- registers tools **dynamically** / from remote sources, or
- is moved to a **cloud / SSE** deployment (then structured logging, container
  sandboxing and the network-binding checks become relevant), or
- is aggregated behind a shared MCP gateway (then implement gateway-level tool
  allow-listing and poisoning detection there).
