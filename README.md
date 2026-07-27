<!-- mcp-name: io.github.malkreide/swiss-geodata-mcp -->

> # ⚠️ DEPRECATED — use [`swisstopo-mcp`](https://github.com/malkreide/swisstopo-mcp) instead
>
> This server has been **consolidated into [`swisstopo-mcp`](https://github.com/malkreide/swisstopo-mcp)**
> and is no longer maintained. Every capability it offered now exists there,
> including the one it used to have exclusively — the official REFRAME
> coordinate conversion.
>
> **Why:** both servers wrapped the same `api3.geo.admin.ch` endpoints and
> overlapped in five core tools (layer search, identify, find, height,
> elevation profile). Maintaining two servers for one data source meant double
> the audits, double the CVE bumps, and an unclear choice for users. The
> rationale and the migration steps are documented in
> [`docs/merge-plan-swiss-geodata-mcp.md`](https://github.com/malkreide/swisstopo-mcp/blob/master/docs/merge-plan-swiss-geodata-mcp.md).
>
> **This repository will be archived.** The code below still works, but it
> receives no further fixes or dependency updates. See
> [Migration](#migration-to-swisstopo-mcp) below.

> 🇨🇭 **Part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide)**

# 🗺️ swiss-geodata-mcp

[![CI](https://github.com/malkreide/swiss-geodata-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/malkreide/swiss-geodata-mcp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/swiss-geodata-mcp)](https://pypi.org/project/swiss-geodata-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/swiss-geodata-mcp)](https://pypi.org/project/swiss-geodata-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![swiss-public-data-mcp](https://img.shields.io/badge/portfolio-swiss--public--data--mcp-blue)](https://github.com/malkreide/swiss-public-data-mcp)

**MCP server for Swiss federal geodata (geo.admin.ch).**

Connects AI models to the federal geodata infrastructure: ~700 layers discoverable by keyword, spatial identify at any point, building zones (ARE), municipality lookup (swissBOUNDARIES3D), terrain heights and elevation profiles (swissALTI3D), and WGS84↔LV95 coordinate conversion. Part of the [swiss-public-data-mcp](https://github.com/malkreide/swiss-public-data-mcp) portfolio. **Private project, independent of any employer or institutional affiliation.**

🇩🇪 [Deutsche Version](README.de.md)

---

## Demo query (anchor example)

```
In which building zone is the school building at Seilergraben 76 in Zurich,
and how high above sea level is it?
```

→ `geo_zoning_at(2683531, 1247914)` + `geo_height(2683531, 1247914)` returns the harmonised ARE zone and 411 m a.s.l. — verified live 2026-07-24.

**Combined with [swiss-housing-mcp](https://github.com/malkreide/swiss-housing-mcp):**

```
What applies at this address?
```

→ `address_to_egid("Seilergraben 76 Zürich")` (housing) delivers the LV95 coordinates → `geo_zoning_at` + `geo_municipality_at` (geodata) deliver zone and municipality. If the GWR is the *address book*, geo.admin.ch is the *atlas*.

---

## Tools (9)

| Tool | Description | Data source |
|------|-------------|-------------|
| `geo_search_layers` | Keyword search over the ~700-layer federal catalogue | geo.admin.ch SearchServer |
| `geo_identify` | What is at this LV95 point? (any layer) | geo.admin.ch MapServer identify |
| `geo_find` | Find features on a layer by attribute value | geo.admin.ch MapServer find |
| `geo_municipality_at` | Municipality + canton containing a point | swissBOUNDARIES3D |
| `geo_zoning_at` | Building zone(s) at a point | ch.are.bauzonen (ARE) |
| `geo_height` | Terrain height at a point | swissALTI3D height service |
| `geo_elevation_profile` | Elevation profile along a line | geo.admin.ch profile service |
| `geo_layer_info` | Queryable fields + legend (plain text) for a layer | geo.admin.ch MapServer |
| `geo_convert_coordinates` | WGS84 ↔ LV95 conversion | geodesy.geo.admin.ch reframe |

`geo_search_layers` is the discovery entry point that scales the whole catalogue without one tool per layer; `geo_layer_info` then reveals a layer's queryable fields for `geo_find`.

### Tool annotations (MCP hints)

All tools are read-only (`readOnlyHint: ✅`, `destructiveHint: ✗`) and query live upstream services (`openWorldHint: ✅`). None are idempotent in the strict caching sense, as upstream data may change between calls.

## Architecture decision

This server uses **Architecture A (Live-API-only)** — a deliberate deviation from the portfolio's dump-first default, documented per portfolio convention:

- The federal geodata infrastructure spans ~700 layers and terabytes; dump-caching is neither feasible nor useful.
- `api3.geo.admin.ch` is built exactly for point/feature queries and answered every probe reliably without authentication (live probe 2026-07-24: SearchServer, identify, find, height, profile, legend, layer metadata, reframe — all HTTP 200, No-Auth).
- Consequence: no local cache, no TTL logic; every response carries `provenance: live_api`.

### Live probe findings (2026-07-24)

| Endpoint | HTTP | Status | Note |
|---|---|---|---|
| SearchServer `type=layers` | 200 | ✅ works | catalogue full-text searchable |
| MapServer identify (bauzonen, boundaries) | 200 | ✅ works | tolerance 0 works for polygon layers |
| height service | 200 | ✅ works | value arrives as JSON *string* |
| profile.json (GET + geom) | 200 | ✅ works | COMB/DTM2/DTM25 altitudes |
| MapServer `{layer}/legend` | 200 | ⚠️ HTML | stripped to plain text in `geo_layer_info` |
| reframe wgs84↔lv95 | 200 | ✅ works | coordinates arrive as JSON *strings* |
| Miss on identify/find | 200 | ⚠️ soft | empty `results` array — not an HTTP error |

## Quick start

### Claude Desktop

```json
{
  "mcpServers": {
    "swiss-geodata": {
      "command": "uvx",
      "args": ["swiss-geodata-mcp"]
    }
  }
}
```

### Cloud / Render.com (Streamable HTTP)

```bash
SWISS_GEODATA_TRANSPORT=streamable-http PORT=8000 swiss-geodata-mcp
```

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `SWISS_GEODATA_TRANSPORT` | `stdio` | `stdio` \| `streamable-http` \| `sse` |
| `HOST` / `PORT` | `127.0.0.1` / `8000` | HTTP binding (cloud transports only). Defaults to loopback; set `HOST=0.0.0.0` explicitly to expose all interfaces in a cloud deployment. |

No API keys — Phase 1 is authentication-free.

## Example queries

### School planning

- «Which building zone applies at our planned school extension site?» → `geo_zoning_at`
- «Which municipality and canton is this coordinate in?» → `geo_municipality_at` (bridges to BFS numbers used by `swiss-statistics-mcp` and `swiss-housing-mcp`)
- «How steep is the school route between these two points?» → `geo_elevation_profile`

### Layer discovery

- «Is there federal data on noise exposure?» → `geo_search_layers("lärm")` → `geo_layer_info` → `geo_identify`

See [EXAMPLES.md](EXAMPLES.md) for use cases grouped by audience (schools, parents, general public, developers) and a tool-selection reference table.

## Testing

```bash
PYTHONPATH=src pytest tests/ -m "not live"   # CI-safe (respx-mocked)
PYTHONPATH=src pytest tests/ -m live         # against real upstream
```

## Project structure

```
swiss-geodata-mcp/
├── src/swiss_geodata_mcp/
│   ├── server.py      # FastMCP tools (9, prefix geo_*)
│   ├── geoadmin.py    # geo.admin.ch client + retry + normalisation
│   ├── models.py      # Pydantic v2 envelopes (source + provenance)
│   └── __main__.py    # Dual-transport entry point
├── tests/             # respx-mocked + @pytest.mark.live
└── .github/workflows/ # CI + OIDC PyPI publish
```

## Known limitations

- **Registers live elsewhere:** building/dwelling entities (EGID/EWID) belong to [`swiss-housing-mcp`](https://github.com/malkreide/swiss-housing-mcp); this server is the *spatial layer* (zones, boundaries, heights). Deliberate separation to avoid twin servers.
- The harmonised zoning layer (ch.are.bauzonen) is an ARE synthesis; legally binding is only the cantonal/communal Nutzungsplanung (noted in every `geo_zoning_at` response).
- School-district polygons are municipal data (→ `zurich-opendata-mcp`), not federal; this server provides municipality boundaries, not Schulkreise.
- `geo_identify` result counts are capped upstream; area-wide aggregations are out of scope here (see `buildings_in_bbox` in swiss-housing-mcp for the register case).
- Coordinates must be LV95; WGS84 input fails fast with a pointer to `geo_convert_coordinates`.

## Changelog

See [CHANGELOG.md](CHANGELOG.md)

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for how to report bugs, suggest a new layer, or submit code.

## Security

This is a read-only, no-PII, public-open-data server. See [SECURITY.md](SECURITY.md) for the security posture and how to report a vulnerability.

## License

MIT License — see [LICENSE](LICENSE). Data: Swiss federal geodata infrastructure (geo.admin.ch / swisstopo and publishing federal offices), open government data with attribution.

## Credits & related projects

- Data & services: [geo.admin.ch](https://api3.geo.admin.ch/) (swisstopo), [ARE](https://www.are.admin.ch/), [swisstopo geodesy](https://geodesy.geo.admin.ch/)
- Portfolio siblings: [`swiss-housing-mcp`](https://github.com/malkreide/swiss-housing-mcp) (register layer), [`swiss-statistics-mcp`](https://github.com/malkreide/swiss-statistics-mcp) (statistics layer), [`zurich-opendata-mcp`](https://github.com/malkreide/zurich-opendata-mcp) (municipal layer)

## Author

malkreide · [GitHub](https://github.com/malkreide)

---

## Migration to `swisstopo-mcp`

Replace this server in your MCP client config:

```jsonc
// before
{ "swiss-geodata": { "command": "uvx", "args": ["swiss-geodata-mcp"] } }
// after
{ "swisstopo":     { "command": "uvx", "args": ["swisstopo-mcp"] } }
```

### Tool mapping

| this server | `swisstopo-mcp` | note |
|---|---|---|
| `geo_search_layers` | `swisstopo_search_layers` | — |
| `geo_identify` | `swisstopo_identify_features` | — |
| `geo_find` | `swisstopo_find_features` | — |
| `geo_height` | `swisstopo_get_height` | — |
| `geo_elevation_profile` | `swisstopo_elevation_profile` | takes a coordinate string; set `coordinate_system="lv95"` for LV95 support points |
| `geo_zoning_at` | `swisstopo_zoning_at` | the non-binding ARE caveat now travels on every result record |
| `geo_municipality_at` | `swisstopo_municipality_at` | BFS number is named `bfs_commune_number` and normalised to `int` |
| `geo_layer_info` | `swisstopo_layer_info` | — |
| `geo_convert_coordinates` | `swisstopo_convert_coordinates` | same `direction` values; same REFRAME service |

### Two differences worth knowing

**Coordinates.** This server was LV95-only and rejected WGS84. `swisstopo-mcp`
accepts **either** `lat`/`lon` (WGS84) **or** `easting`/`northing` (LV95) on the
point-based tools — pass one pair, not both. Existing LV95 call sites keep
working; the argument names are the same.

**Response shape.** This server returned a JSON string (`GeoEnvelope`) with the
payload under `result`. `swisstopo-mcp` returns a structured `ToolResponse`:
records live in `results` (plural, always a list), with `count`, `match_type`,
`source`, `license` and a Markdown `summary` alongside. Code that parsed
`result` needs to read `results`.
