# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-07-26

Initial release.

### Added
- MCP server for the Swiss federal geodata (geo.admin.ch) with 9 tools:
  `geo_search_layers`, `geo_identify`, `geo_find`, `geo_municipality_at`,
  `geo_zoning_at`, `geo_height`, `geo_elevation_profile`, `geo_layer_info`,
  `geo_convert_coordinates`
- Live-API-only design (Architecture A), verified live 2026-07-24 — a
  deliberate deviation from the portfolio's dump-first default (documented in
  the README)
- LV95 plausibility validation with actionable error messages pointing to the
  coordinate conversion tool
- Dual transport: stdio (Claude Desktop) + streamable-http/SSE (cloud), via the
  `SWISS_GEODATA_TRANSPORT` entry point
- Retry with exponential backoff and a provenance envelope in every response
- Server implementation under `src/swiss_geodata_mcp/`: the geo.admin.ch client
  (`geoadmin.py`, egress allow-list + retry + string/HTML normalisation), the
  Pydantic response envelope (`models.py`), the FastMCP `geo_*` tools
  (`server.py`), and the dual-transport entry point (`__main__.py`)
- Test suite under `tests/`: respx-mocked unit tests (`test_unit.py`, CI-safe)
  and gated live tests against geo.admin.ch (`test_live.py`, `-m live`); parsing
  verified against live upstream shapes probed 2026-07-25
- MCP best-practice audit scorecard under `audits/` (25 pass / 7 partial /
  0 fail across 32 applicable checks; production-ready) — referenced from
  `SECURITY.md`/`.de.md`, which record the accepted risks
- Repository docs: `README.md`/`README.de.md`, `CONTRIBUTING.md`/`.de.md`,
  `SECURITY.md`/`.de.md`, `EXAMPLES.md`, and `server.json` (MCP Registry
  manifest)
- CI (`.github/workflows/ci.yml`): `test` (matrix 3.11–3.13), `lint`
  (pinned ruff), and nightly-only `live` jobs
- Publishing (`.github/workflows/publish.yml`): OIDC PyPI publish + MCP Registry
  publishing on `v*` tags (version derived from the tag, or from `server.json`
  on manual dispatch)

### Security
- HTTP transports default `HOST` to `127.0.0.1` (loopback) rather than
  `0.0.0.0`; exposing all interfaces requires an explicit `HOST=0.0.0.0`
  (SEC-016 / NeighborJack, found by the first MCP best-practice audit run)

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

[Unreleased]: https://github.com/malkreide/swiss-geodata-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/malkreide/swiss-geodata-mcp/releases/tag/v0.1.0
