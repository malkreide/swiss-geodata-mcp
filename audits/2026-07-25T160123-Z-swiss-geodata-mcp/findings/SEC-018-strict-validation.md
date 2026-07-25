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
