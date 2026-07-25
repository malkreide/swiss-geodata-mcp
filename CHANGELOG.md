# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security
- **SEC-016 (0.0.0.0 binding / NeighborJack):** the HTTP transports defaulted
  `HOST` to `0.0.0.0`, binding all interfaces. Now default to `127.0.0.1`;
  exposing all interfaces requires an explicit `HOST=0.0.0.0`. Found by the first
  MCP best-practice audit run.

### Added
- MCP best-practice audit scorecard under `audits/` (25 pass / 7 partial /
  0 fail across 32 applicable checks; production-ready). `SECURITY.md`/`.de.md`
  now reference the report and record the accepted risks.
- Server implementation under `src/swiss_geodata_mcp/`: the geo.admin.ch client
  (`geoadmin.py`, egress allow-list + retry + string/HTML normalisation), the
  Pydantic response envelope (`models.py`), the 9 FastMCP `geo_*` tools
  (`server.py`), and the dual-transport entry point (`__main__.py`) — the code
  the repo's docs and CI already described
- Test suite under `tests/`: respx-mocked unit tests (`test_unit.py`, CI-safe)
  and gated live tests against geo.admin.ch (`test_live.py`, `-m live`); parsing
  verified against live upstream shapes probed 2026-07-25
- Portfolio-standard repository docs: `CONTRIBUTING.md`/`CONTRIBUTING.de.md`,
  `SECURITY.md`/`SECURITY.de.md`, `EXAMPLES.md`, and `server.json` (MCP Registry
  manifest), aligning the repo with the sibling `*-mcp` servers
- `.github/workflows/publish.yml` — OIDC PyPI publish + MCP Registry publishing
  on `v*` tags (version derived from the tag, or from `server.json` on manual
  dispatch so branch dispatches don't write a branch name as the version)

### Changed
- CI workflow (`.github/workflows/ci.yml`) split into `test` / `lint` / `live`
  jobs, matching the portfolio convention (pinned ruff, matrix 3.11–3.13,
  nightly-only live tests)
- `pyproject.toml` aligned to portfolio standards: `requires-python >=3.11`,
  `mcp[cli]` upper-bounded (`<2.0.0`), explicit `[tool.ruff.lint]` rule set with
  German-typography exceptions, `testpaths`, and a `Changelog` project URL
- READMEs link the new `EXAMPLES`, `CONTRIBUTING`, and `SECURITY` docs

### Fixed
- Restored two misnamed files committed at import: the `.gitignore` (was
  `download`) and `.github/workflows/ci.yml` (was `geoadmin.py`)

## [0.1.0] - 2026-07-24

### Added
- Initial release with 9 tools: `geo_search_layers`, `geo_identify`, `geo_find`,
  `geo_municipality_at`, `geo_zoning_at`, `geo_height`, `geo_elevation_profile`,
  `geo_layer_info`, `geo_convert_coordinates`
- Architecture A (Live-API-only), verified live 2026-07-24 — deliberate
  deviation from the portfolio's dump-first default (documented in README)
- LV95 plausibility validation with actionable error messages pointing to
  the coordinate conversion tool
- Dual transport: stdio (Claude Desktop) + streamable-http/SSE (cloud)
- Retry with exponential backoff, provenance envelope in every response

### Known findings
- The reframe service (geodesy.geo.admin.ch) returns coordinates as JSON
  *strings*, not numbers — normalised to float in the client layer.
- The height service likewise returns the height value as a string.
- The legend endpoint serves HTML, not JSON — stripped to plain text for
  LLM consumption.
- identify/find answer HTTP 200 with an empty `results` array for misses
  (soft "not found", not an upstream error) — consistent with the GWR-layer
  behaviour documented in swiss-housing-mcp.
- SearchServer swaps axes in location results: `y` = LV95 east, `x` = LV95 north.
