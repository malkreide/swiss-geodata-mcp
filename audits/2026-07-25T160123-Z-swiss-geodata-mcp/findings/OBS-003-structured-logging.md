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
