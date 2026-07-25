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
