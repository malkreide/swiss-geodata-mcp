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
