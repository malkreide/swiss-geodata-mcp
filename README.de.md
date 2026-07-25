> 🇨🇭 **Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide)**

# 🗺️ swiss-geodata-mcp

[![CI](https://github.com/malkreide/swiss-geodata-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/malkreide/swiss-geodata-mcp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/swiss-geodata-mcp)](https://pypi.org/project/swiss-geodata-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/swiss-geodata-mcp)](https://pypi.org/project/swiss-geodata-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![swiss-public-data-mcp](https://img.shields.io/badge/portfolio-swiss--public--data--mcp-blue)](https://github.com/malkreide/swiss-public-data-mcp)

**MCP-Server für die Schweizer Bundesgeodaten (geo.admin.ch).**

Verbindet KI-Modelle mit der Bundesgeodaten-Infrastruktur: ~700 Layer per Stichwort auffindbar, räumliches Identify an jedem Punkt, Bauzonen (ARE), Gemeinde-Lookup (swissBOUNDARIES3D), Geländehöhen und Höhenprofile (swissALTI3D) sowie WGS84↔LV95-Koordinatenumrechnung. Teil des [swiss-public-data-mcp](https://github.com/malkreide/swiss-public-data-mcp) Portfolios. **Privates Projekt, unabhängig von jeglichem Arbeitgeber oder institutioneller Zugehörigkeit.**

🇬🇧 [English Version](README.md)

---

## Demo-Query (Anchor-Beispiel)

```
In welcher Bauzone liegt das Schulhaus am Seilergraben 76 in Zürich,
und wie hoch liegt es über Meer?
```

→ `geo_zoning_at(2683531, 1247914)` + `geo_height(2683531, 1247914)` liefert die harmonisierte ARE-Zone und 411 m ü. M. — live verifiziert am 24.07.2026.

**Kombiniert mit [swiss-housing-mcp](https://github.com/malkreide/swiss-housing-mcp):**

```
Was gilt an dieser Adresse?
```

→ `address_to_egid("Seilergraben 76 Zürich")` (housing) liefert die LV95-Koordinaten → `geo_zoning_at` + `geo_municipality_at` (geodata) liefern Zone und Gemeinde. Wenn das GWR das *Adressbuch* ist, ist geo.admin.ch der *Atlas*.

---

## Tools (9)

| Tool | Beschreibung | Datenquelle |
|------|-------------|-------------|
| `geo_search_layers` | Stichwortsuche über den ~700-Layer-Bundeskatalog | geo.admin.ch SearchServer |
| `geo_identify` | Was ist an diesem LV95-Punkt? (beliebiger Layer) | geo.admin.ch MapServer identify |
| `geo_find` | Features eines Layers nach Attributwert finden | geo.admin.ch MapServer find |
| `geo_municipality_at` | Gemeinde + Kanton zu einem Punkt | swissBOUNDARIES3D |
| `geo_zoning_at` | Bauzone(n) an einem Punkt | ch.are.bauzonen (ARE) |
| `geo_height` | Geländehöhe an einem Punkt | swissALTI3D-Höhenservice |
| `geo_elevation_profile` | Höhenprofil entlang einer Linie | geo.admin.ch Profilservice |
| `geo_layer_info` | Abfragbare Felder + Legende (Klartext) eines Layers | geo.admin.ch MapServer |
| `geo_convert_coordinates` | WGS84 ↔ LV95-Umrechnung | geodesy.geo.admin.ch reframe |

`geo_search_layers` ist der Discovery-Einstieg, der den ganzen Katalog skaliert, ohne pro Layer ein Tool zu bauen; `geo_layer_info` zeigt danach die abfragbaren Felder für `geo_find`.

### Tool-Annotations (MCP-Hints)

Alle Tools sind read-only (`readOnlyHint: ✅`, `destructiveHint: ✗`) und fragen Live-Dienste ab (`openWorldHint: ✅`). Keines ist im strengen Caching-Sinn idempotent, da sich Upstream-Daten zwischen Aufrufen ändern können.

## Architektur-Entscheid

Dieser Server verwendet **Architektur A (Live-API-only)** — eine bewusste Abweichung vom Dump-first-Standard des Portfolios, gemäss Portfolio-Konvention dokumentiert:

- Die Bundesgeodaten-Infrastruktur umfasst ~700 Layer und Terabytes; Dump-Caching ist weder machbar noch sinnvoll.
- `api3.geo.admin.ch` ist genau für Punkt-/Feature-Abfragen gebaut und hat jede Probe zuverlässig ohne Authentifizierung beantwortet (Live-Probe 24.07.2026: SearchServer, identify, find, height, profile, legend, Layer-Metadaten, reframe — alle HTTP 200, No-Auth).
- Konsequenz: kein lokaler Cache, keine TTL-Logik; jede Response trägt `provenance: live_api`.

### Live-Probe-Befunde (24.07.2026)

| Endpoint | HTTP | Status | Bemerkung |
|---|---|---|---|
| SearchServer `type=layers` | 200 | ✅ funktioniert | Katalog volltextsuchbar |
| MapServer identify (Bauzonen, Grenzen) | 200 | ✅ funktioniert | Toleranz 0 funktioniert für Polygon-Layer |
| Höhenservice | 200 | ✅ funktioniert | Wert kommt als JSON-*String* |
| profile.json (GET + geom) | 200 | ✅ funktioniert | COMB/DTM2/DTM25-Höhen |
| MapServer `{layer}/legend` | 200 | ⚠️ HTML | in `geo_layer_info` zu Klartext reduziert |
| reframe wgs84↔lv95 | 200 | ✅ funktioniert | Koordinaten kommen als JSON-*Strings* |
| Miss auf identify/find | 200 | ⚠️ Soft | leeres `results`-Array — kein HTTP-Fehler |

## Quickstart

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

## Konfiguration

| Variable | Default | Zweck |
|---|---|---|
| `SWISS_GEODATA_TRANSPORT` | `stdio` | `stdio` \| `streamable-http` \| `sse` |
| `HOST` / `PORT` | `127.0.0.1` / `8000` | HTTP-Binding (nur Cloud-Transporte). Standardmässig Loopback; für Cloud-Deployments `HOST=0.0.0.0` explizit setzen, um alle Interfaces freizugeben. |

Keine API-Keys — Phase 1 ist authentifizierungsfrei.

## Beispiel-Queries

### Schulraumplanung

- «In welcher Bauzone liegt der geplante Erweiterungsstandort unseres Schulhauses?» → `geo_zoning_at`
- «In welcher Gemeinde und welchem Kanton liegt diese Koordinate?» → `geo_municipality_at` (Brücke zu den BFS-Nummern, die `swiss-statistics-mcp` und `swiss-housing-mcp` verwenden)
- «Wie steil ist der Schulweg zwischen diesen zwei Punkten?» → `geo_elevation_profile`

### Layer-Discovery

- «Gibt es Bundesdaten zur Lärmbelastung?» → `geo_search_layers("lärm")` → `geo_layer_info` → `geo_identify`

Siehe [EXAMPLES.md](EXAMPLES.md) für Anwendungsfälle nach Zielgruppe (Schulen, Eltern, Öffentlichkeit, Entwickler:innen) und eine Tabelle zur Tool-Auswahl.

## Testing

```bash
PYTHONPATH=src pytest tests/ -m "not live"   # CI-tauglich (respx-gemockt)
PYTHONPATH=src pytest tests/ -m live         # gegen echte Quellen
```

## Projektstruktur

```
swiss-geodata-mcp/
├── src/swiss_geodata_mcp/
│   ├── server.py      # FastMCP-Tools (9, Präfix geo_*)
│   ├── geoadmin.py    # geo.admin.ch-Client + Retry + Normalisierung
│   ├── models.py      # Pydantic-v2-Envelopes (source + provenance)
│   └── __main__.py    # Dual-Transport-Entry-Point
├── tests/             # respx-gemockt + @pytest.mark.live
└── .github/workflows/ # CI + OIDC-PyPI-Publish
```

## Known Limitations

- **Register wohnen anderswo:** Gebäude-/Wohnungs-Entitäten (EGID/EWID) gehören zu [`swiss-housing-mcp`](https://github.com/malkreide/swiss-housing-mcp); dieser Server ist die *Raum-Schicht* (Zonen, Grenzen, Höhen). Bewusste Trennung gegen Zwillings-Server.
- Der harmonisierte Bauzonen-Layer (ch.are.bauzonen) ist eine ARE-Synthese; rechtsverbindlich ist nur die kantonale/kommunale Nutzungsplanung (in jeder `geo_zoning_at`-Response vermerkt).
- Schulkreis-Polygone sind städtische Daten (→ `zurich-opendata-mcp`), keine Bundesdaten; dieser Server liefert Gemeinde-, nicht Schulkreisgrenzen.
- `geo_identify`-Resultate sind upstream limitiert; flächige Aggregationen sind hier out of scope (für den Register-Fall siehe `buildings_in_bbox` in swiss-housing-mcp).
- Koordinaten müssen LV95 sein; WGS84-Eingaben scheitern früh mit Verweis auf `geo_convert_coordinates`.

## Changelog

Siehe [CHANGELOG.md](CHANGELOG.md)

## Mitwirken

Beiträge sind willkommen — siehe [CONTRIBUTING.de.md](CONTRIBUTING.de.md): Fehler melden, einen neuen Layer vorschlagen oder Code beitragen.

## Sicherheit

Dies ist ein rein lesender, PII-freier Server für öffentliche Open Data. Siehe [SECURITY.de.md](SECURITY.de.md) für die Sicherheitslage und die Meldung von Schwachstellen.

## Lizenz

MIT License — siehe [LICENSE](LICENSE). Daten: Bundesgeodaten-Infrastruktur (geo.admin.ch / swisstopo und publizierende Bundesämter), Open Government Data mit Quellenangabe.

## Credits & Verwandte Projekte

- Daten & Dienste: [geo.admin.ch](https://api3.geo.admin.ch/) (swisstopo), [ARE](https://www.are.admin.ch/), [swisstopo Geodäsie](https://geodesy.geo.admin.ch/)
- Portfolio-Geschwister: [`swiss-housing-mcp`](https://github.com/malkreide/swiss-housing-mcp) (Register-Schicht), [`swiss-statistics-mcp`](https://github.com/malkreide/swiss-statistics-mcp) (Statistik-Schicht), [`zurich-opendata-mcp`](https://github.com/malkreide/zurich-opendata-mcp) (städtische Schicht)

## Autor

malkreide · [GitHub](https://github.com/malkreide)
