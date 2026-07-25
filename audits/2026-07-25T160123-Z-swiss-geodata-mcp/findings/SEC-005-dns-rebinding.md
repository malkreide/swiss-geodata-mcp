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
