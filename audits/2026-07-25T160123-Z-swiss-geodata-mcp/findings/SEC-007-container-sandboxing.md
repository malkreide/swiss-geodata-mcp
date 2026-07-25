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
