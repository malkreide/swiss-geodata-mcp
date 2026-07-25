# MCP-Server Audit-Report — `swiss-geodata-mcp`

**Audit-Datum:** 
**Skill-Version:** 1.0.0
**Catalog-Version:** ?

---

## 1. Executive Summary

Server `swiss-geodata-mcp` wurde gegen 32 anwendbare Best-Practice-Checks geprüft. 25 bestanden, 7 Findings dokumentiert (0 critical, 4 high, 3 medium, 0 low). Production-Readiness: erreicht.

**Production-Readiness:** YES

---

## 2. Profil-Snapshot

| Feld | Wert |
|---|---|
| Server-Name | `swiss-geodata-mcp` |
| Audit-Datum | ? |
| Skill-Version | 1.0.0 |
| Catalog-Version | ? |

---

## 3. Applicability

### Status pro Kategorie

| Kategorie | Pass | Fail | Partial | Todo | N/A |
|---|---|---|---|---|---|
| ARCH | 10 | 0 | 1 | 0 | 0 |
| CH | 1 | 0 | 0 | 0 | 0 |
| OBS | 2 | 0 | 2 | 0 | 0 |
| OPS | 3 | 0 | 0 | 0 | 0 |
| SCALE | 1 | 0 | 0 | 0 | 0 |
| SEC | 8 | 0 | 4 | 0 | 0 |
| **Total** | **25** | **0** | **7** | **0** | **0** |

---

## 4. Findings-Übersicht

_Policy: `fail-or-partial`_

| ID | Category | Severity | Status |
|---|---|---|---|
| OBS-001 | OBS | high | partial |
| SEC-005 | SEC | high | partial |
| SEC-007 | SEC | high | partial |
| SEC-018 | SEC | high | partial |
| ARCH-008 | ARCH | medium | partial |
| OBS-003 | OBS | medium | partial |
| SEC-008 | SEC | medium | partial |

**Gesamt:** 7 Findings

---

## 5. Detail-Findings

### ARCH-008

## Finding: ARCH-008 — Drei Primitive nutzen: Tools, Resources und Prompts

**Severity:** medium
**Status:** accepted-risk
**Server:** swiss-geodata-mcp
**Check-Reference:** ARCH-008
**PDF-Reference:** Sec 2

### Observed Behavior
The server exposes only the Tools primitive (9 `@mcp.tool`). No MCP Resources or Prompts are registered (`grep '@mcp.resource'/'@mcp.prompt'` over `src/` is empty).

### Expected Behavior
The best-practice catalogue encourages using all three primitives where natural — e.g. exposing the layer catalogue or a layer's metadata as a Resource, or shipping canned Prompts for common workflows.

### Evidence
- File: `src/swiss_geodata_mcp/server.py` — only `@mcp.tool` decorators present.

### Risk Description
None security-relevant. Purely a capability-completeness gap; discovery still works via `geo_search_layers` + `geo_layer_info`.

### Remediation
Optional: expose the layer catalogue as a Resource and add a discovery Prompt. Deferred to keep parity with the portfolio's tools-only convention until the pattern is standardised across servers.

### Effort Estimate
M (1-3d)


### OBS-001

## Finding: OBS-001 — Protocol vs. Execution Errors: korrekte Trennung

**Severity:** high
**Status:** accepted-risk
**Server:** swiss-geodata-mcp
**Check-Reference:** OBS-001
**PDF-Reference:** Sec 6

### Observed Behavior
Tools return user-friendly, sanitised error **strings** via `_handle_error()` rather than an explicit `isError` execution-error envelope.

### Expected Behavior
The catalogue's strict pattern distinguishes protocol errors from tool-execution errors via the MCP `isError` envelope.

### Evidence
- File: `src/swiss_geodata_mcp/server.py:116` — `_handle_error` returns `str`.
- FastMCP converts string returns into the proper MCP envelope, so the client still interprets errors correctly.

### Risk Description
No behavioural impact for the client. The strict pass-pattern would touch every tool body with no functional benefit.

### Remediation
Accepted risk — identical posture to `swiss-snb-mcp`. Revisit if a client needs to programmatically distinguish error classes.

### Effort Estimate
M (1-3d)


### OBS-003

## Finding: OBS-003 — Structured Logging mit RFC 5424 Severity-Stufen

**Severity:** medium
**Status:** accepted-risk
**Server:** swiss-geodata-mcp
**Check-Reference:** OBS-003
**PDF-Reference:** Sec 6 / Anhang B10

### Observed Behavior
Logging is plain-text to stderr via `logging.basicConfig(stream=sys.stderr, level=INFO, ...)`.

### Expected Behavior
JSON-structured logs with RFC 5424 severities and trace IDs for SIEM ingestion.

### Evidence
- File: `src/swiss_geodata_mcp/server.py:34` — `basicConfig(stream=sys.stderr, ...)`.

### Risk Description
None for a stdio server consumed by a local client. Structured logging matters only under a centralised log pipeline.

### Remediation
Accepted risk. Introduce structured JSON logging if the server is lifted to a cloud/SSE deployment behind a SIEM.

### Effort Estimate
S (< 1d)


### SEC-005

## Finding: SEC-005 — DNS-Rebinding-Prevention: DNS-Pinning gegen TOCTOU

**Severity:** high
**Status:** accepted-risk
**Server:** swiss-geodata-mcp
**Check-Reference:** SEC-005
**PDF-Reference:** Sec 4

### Observed Behavior
Egress is restricted to a two-host allow-list (`api3.geo.admin.ch`, `geodesy.geo.admin.ch`) but there is no explicit DNS pinning against a rebinding TOCTOU.

### Expected Behavior
Pin resolved IPs (or use a resolver that forbids private ranges) so a rebind between check and connect cannot redirect the request to an internal address.

### Evidence
- File: `src/swiss_geodata_mcp/geoadmin.py:49` — `_assert_host_allowed` validates the hostname, not the resolved IP.

### Risk Description
Low: the two allow-listed hosts are fixed public swisstopo endpoints, not user-controlled, so an attacker cannot introduce a rebindable hostname. No SSRF sink beyond these hosts.

### Remediation
Accepted risk for this profile. If arbitrary user-supplied hosts were ever allowed, add IP-range validation / DNS pinning.

### Effort Estimate
M (1-3d)


### SEC-007

## Finding: SEC-007 — Container-Sandboxing: Docker / chroot mit minimalen Privilegien

**Severity:** high
**Status:** accepted-risk
**Server:** swiss-geodata-mcp
**Check-Reference:** SEC-007
**PDF-Reference:** Sec 4

### Observed Behavior
No `Dockerfile` or sandbox definition; the server runs as a local stdio process.

### Expected Behavior
Ship a hardened container (minimal base, non-root, read-only FS) for deployments.

### Evidence
- Repo root has no `Dockerfile`.

### Risk Description
Acceptable for a local-stdio public-data server — defense-in-depth lives at the OS user level. No privileged operations, no write path, no secrets.

### Remediation
Accepted risk. Ship a hardened image if the deployment profile ever moves to the cloud (already noted in `SECURITY.md`).

### Effort Estimate
M (1-3d)


### SEC-008

## Finding: SEC-008 — Pre-Configuration Consent für Local-Server-Installation

**Severity:** medium
**Status:** accepted-risk
**Server:** swiss-geodata-mcp
**Check-Reference:** SEC-008
**PDF-Reference:** Sec 4

### Observed Behavior
Installation is via `uvx`/`pip` plus the documented `claude_desktop_config.json` snippet; there is no explicit pre-configuration consent gate.

### Expected Behavior
A consent step before a local server is wired into a client.

### Evidence
- `README.md` Quick start — standard uvx/config-based install.

### Risk Description
Low impact: read-only, public-data, no credentials, no filesystem access. The MCP client (e.g. Claude Desktop) already mediates tool consent at call time.

### Remediation
Accepted risk for this profile.

### Effort Estimate
S (< 1d)


### SEC-018

## Finding: SEC-018 — Input-Validation an Tool-Boundaries (Pydantic strict / Zod)

**Severity:** high
**Status:** accepted-risk
**Server:** swiss-geodata-mcp
**Check-Reference:** SEC-018
**PDF-Reference:** Sec 4 / Anhang B

### Observed Behavior
Every tool input is a Pydantic v2 model with `extra='forbid'` and `Field` constraints (`min_length`, `ge`/`le`); LV95 coordinates get an extra plausibility check. Models do **not** set `strict=True`.

### Expected Behavior
The catalogue's strongest form is Pydantic `strict=True` (or Zod strict) at every boundary.

### Evidence
- File: `src/swiss_geodata_mcp/server.py:152+` — input models use `ConfigDict(extra="forbid", ...)`.
- File: `src/swiss_geodata_mcp/server.py:50` — `_lv95_error` fails fast on implausible (e.g. WGS84) coordinates.

### Risk Description
Low: unknown fields are rejected and ranges are bounded. `strict=True` is deliberately omitted because coordinate fields are `float` and strict mode would reject integer LV95 inputs that clients commonly send.

### Remediation
Optional tightening: type coordinate fields as `int | float` and enable `strict=True`. Deferred as polish, not a security gap.

### Effort Estimate
S (< 1d)


---

## 6. Remediation-Plan

### Empfohlene Reihenfolge

1. **OBS-001** (high, partial)
2. **SEC-005** (high, partial)
3. **SEC-007** (high, partial)
4. **SEC-018** (high, partial)
5. **ARCH-008** (medium, partial)
6. **OBS-003** (medium, partial)
7. **SEC-008** (medium, partial)

---

## 7. Audit-Metadata

| Feld | Wert |
|---|---|
| skill_version | `1.0.0` |
| policy | `fail-or-partial` |


_Generated by tools/build_report.py — do not edit by hand._
