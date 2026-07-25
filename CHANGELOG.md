# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
