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
