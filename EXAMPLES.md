# Use Cases & Examples — swiss-geodata-mcp

Real-world queries by audience. Every tool in this server queries the public
geo.admin.ch infrastructure — **no API key is ever required.** Coordinates are
LV95 (EPSG:2056); use `geo_convert_coordinates` to convert from WGS84.

## 🏫 Bildung & Schule

Lehrpersonen, Schulbehörden, Fachreferent:innen

### Bauzone eines geplanten Schulhaus-Standorts

«In welcher Bauzone liegt der geplante Erweiterungsstandort unseres Schulhauses am Seilergraben 76 in Zürich, und wie hoch liegt er über Meer?»

**API-Key nötig:** Nein

→ `geo_zoning_at(2683531, 1247914)`
→ `geo_height(2683531, 1247914)`

Warum nützlich: Schulbehörden können den harmonisierten ARE-Zonentyp und die Geländehöhe mit offiziellen Bundesdaten belegen, bevor sie in die rechtsverbindliche kommunale Nutzungsplanung einsteigen.

### Steigung eines Schulwegs beurteilen

«Wie steil ist der Schulweg zwischen diesen zwei Punkten, und welche Höhenmeter sind zu überwinden?»

**API-Key nötig:** Nein

→ `geo_elevation_profile` entlang der Verbindungslinie (swissALTI3D)

Warum nützlich: Für Verkehrssicherheit, Barrierefreiheit oder die Planung von Exkursionen liefert das Höhenprofil eine faktenbasierte Grundlage statt einer Schätzung.

### Bundesdaten zu einem Umweltthema finden

«Gibt es Bundesdaten zur Lärmbelastung an unserem Schulstandort?»

**API-Key nötig:** Nein

→ `geo_search_layers("lärm")` → `geo_layer_info(<layer_id>)` → `geo_identify(<layer_id>, x, y)`

Warum nützlich: Der Discovery-Einstieg macht den ~700-Layer-Katalog durchsuchbar, ohne dass pro Thema ein eigenes Tool nötig ist. Lehrpersonen finden so Daten zu Lärm, Gefahren, Natur und mehr.

## 👨‍👩‍👧 Eltern & Schulgemeinde

Elternräte, interessierte Erziehungsberechtigte

### Gemeinde und Kanton zu einer Koordinate

«In welcher Gemeinde und welchem Kanton liegt dieser Standort?»

**API-Key nötig:** Nein

→ `geo_municipality_at(2683531, 1247914)` (swissBOUNDARIES3D)

Warum nützlich: Die Gemeinde liefert die BFS-Nummer — die Brücke zu Statistik- und Registerdaten, die `swiss-statistics-mcp` und `swiss-housing-mcp` verwenden.

### Was gilt an einer Adresse? (Portfolio-Kombination)

«Was gilt an der Adresse Seilergraben 76, Zürich — Bauzone und Gemeinde?»

**API-Key nötig:** Nein

→ `address_to_egid("Seilergraben 76 Zürich")` liefert LV95-Koordinaten (via https://github.com/malkreide/swiss-housing-mcp)
→ `geo_zoning_at(x, y)` + `geo_municipality_at(x, y)` liefern Zone und Gemeinde

Warum nützlich: Wenn das GWR das *Adressbuch* ist, ist geo.admin.ch der *Atlas*. Eltern und Schulgemeinden können aus einer Adresse die räumliche Einordnung ableiten.

## 🗳️ Bevölkerung & öffentliches Interesse

Allgemeine Öffentlichkeit, politisch und gesellschaftlich Interessierte

### Höhe eines Standorts über Meer

«Wie hoch über Meer liegt dieser Ort, und wie ändert sich die Höhe entlang dieser Strecke?»

**API-Key nötig:** Nein

→ `geo_height(x, y)` für den Einzelpunkt
→ `geo_elevation_profile` für den Verlauf

Warum nützlich: Höhenangaben aus swissALTI3D sind offiziell und präzise — nützlich für Wanderungen, Hochwasser-Einordnung oder einfach Neugier.

### Koordinaten umrechnen

«Ich habe GPS-Koordinaten (WGS84) — wie lauten die entsprechenden LV95-Koordinaten für eine Bundesabfrage?»

**API-Key nötig:** Nein

→ `geo_convert_coordinates` (geodesy.geo.admin.ch reframe)

Warum nützlich: Alle Bundes-Geoabfragen erwarten LV95. Die offizielle reframe-Umrechnung von swisstopo ist genauer als eine Näherungsformel.

## 🤖 KI-Interessierte & Entwickler:innen

MCP-Enthusiast:innen, Forscher:innen, Prompt Engineers, öffentliche Verwaltung

### Tool-Discovery für robuste Prompts

«Welche Felder eines Layers kann ich mit `geo_find` abfragen, und wie finde ich den passenden Layer?»

**API-Key nötig:** Nein

→ `geo_search_layers("<stichwort>")` → `geo_layer_info(<layer_id>)` → `geo_find(<layer_id>, <feld>, <wert>)`

Warum nützlich: `geo_layer_info` legt die abfragbaren Felder eines Layers offen, sodass Agenten `geo_find`-Aufrufe zuverlässig konstruieren statt zu raten.

### Portfolio-Kombination: Raum, Register und Statistik

«Für einen Standort: Welche Bauzone, welche Gebäude (EGID) und welche Gemeindestatistik?»

**API-Key nötig:** Nein

→ `geo_zoning_at(x, y)` + `geo_municipality_at(x, y)` (geodata)
→ `buildings_in_bbox(...)` via https://github.com/malkreide/swiss-housing-mcp (Register-Schicht)
→ BFS-Nummer aus der Gemeinde → Statistik-Abfrage via https://github.com/malkreide/swiss-statistics-mcp

Warum nützlich: Die Trennung in Raum-, Register- und Statistik-Schicht vermeidet Zwillings-Server. Ein Agent kombiniert die Schichten über die gemeinsame LV95-/BFS-Brücke.

## 🔧 Technische Referenz: Tool-Auswahl nach Anwendungsfall

| Ich möchte… | Tool(s) | Auth nötig? |
|---|---|---|
| Im ~700-Layer-Bundeskatalog per Stichwort suchen | `geo_search_layers` | Nein |
| Wissen, was an einem LV95-Punkt liegt (beliebiger Layer) | `geo_identify` | Nein |
| Features eines Layers nach Attributwert finden | `geo_find` | Nein |
| Gemeinde und Kanton zu einem Punkt bestimmen | `geo_municipality_at` | Nein |
| Die Bauzone(n) an einem Punkt ermitteln | `geo_zoning_at` | Nein |
| Die Geländehöhe an einem Punkt abrufen | `geo_height` | Nein |
| Ein Höhenprofil entlang einer Linie erzeugen | `geo_elevation_profile` | Nein |
| Abfragbare Felder und Legende eines Layers verstehen | `geo_layer_info` | Nein |
| Koordinaten zwischen WGS84 und LV95 umrechnen | `geo_convert_coordinates` | Nein |
