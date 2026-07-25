# Sicherheitsrichtlinie & Sicherheitslage

[🇬🇧 English Version](SECURITY.md)

`swiss-geodata-mcp` wurde gegen den internen MCP-Best-Practice-Audit-Katalog
(68 Checks, 8 Kategorien) geprüft. Der jüngste Lauf
(`audits/2026-07-25T160123-Z-swiss-geodata-mcp/`) ergab **25 pass / 7 partial /
0 fail** über die 32 anwendbaren Checks — **produktionsreif, ohne offenes
Finding mit Sicherheits-Impact**. Dieses Dokument fasst die Sicherheitslage
zusammen sowie die **akzeptierten Risiken** für Kontrollen, die für dieses rein
lesende, PII-freie Public-Open-Data-Profil bewusst zurückgestellt werden.

## Schwachstelle melden

Bitte eröffnen Sie ein privates Security Advisory im GitHub-Repository oder
kontaktieren Sie die in `README.md` genannte verantwortliche Person. Erstellen Sie
für ausnutzbare Schwachstellen **keine** öffentlichen Issues.

## Zusammenfassung der Sicherheitslage

Alle Tools **fragen** die Bundesgeodaten-Infrastruktur nur ab — es gibt keinen
Schreibpfad, keine Authentifizierung und keine Personendaten. Bereits umgesetzte
Härtung:

| Bereich | Kontrolle |
|---|---|
| Egress | HTTPS-erzwungene Allow-List für die geo.admin.ch-Hosts (`api3.geo.admin.ch`, `geodesy.geo.admin.ch`), durch `_assert_host_allowed` vor jeder ausgehenden Anfrage durchgesetzt |
| TLS | Zertifikatsprüfung standardmässig aktiv (httpx-Standard; nie deaktiviert) |
| Transport | Standardmässig stdio — stdout für den JSON-RPC-Stream reserviert; HTTP-Transporte binden an Loopback (`127.0.0.1`), ausser `HOST=0.0.0.0` wird explizit gesetzt (SEC-016) |
| Input | Pydantic-v2-Validierung für jedes Tool-Input; LV95-Koordinaten werden auf Plausibilität geprüft, mit umsetzbarem Fehlerhinweis auf `geo_convert_coordinates` |
| Secrets | Keine API-Keys oder Zugangsdaten — geo.admin.ch ist vollständig öffentlich, es gibt nichts zu speichern oder zu leaken |
| Fehler | Upstream-Antworten und Stack-Traces werden nur nach stderr geloggt; das Modell sieht eine generische, bereinigte Meldung (`_handle_error`) |
| Stdout | Reserviert für den JSON-RPC-Stream; Logging via `basicConfig` fest auf stderr |
| Verbindungen | Ein gemeinsamer `httpx.AsyncClient` über die Server-Lifespan geöffnet, nicht pro Aufruf |
| Tests | respx-mockierte Unit-Suite bei jedem PR (3.11/3.12/3.13); Live-API-Tests auf einen Nightly-Job beschränkt |

Die vollständigen Berichte finden Sie unter `audits/`, die Härtungshistorie in
`CHANGELOG.md`.

### Im ersten Audit-Lauf behobenes Finding

**SEC-016 (0.0.0.0-Binding / NeighborJack)** — die HTTP-Transporte setzten `HOST`
zuvor auf `0.0.0.0` und exponierten damit alle Interfaces. Behoben: Standard ist
jetzt `127.0.0.1`; alle Interfaces freizugeben erfordert ein explizites
`HOST=0.0.0.0`. stdio (der Standard-Transport) bindet gar nicht.

## Akzeptierte Risiken

Die folgenden Kontrollen sind für einen reinen stdio-Public-Open-Data-Server
bewusst **out of scope**. Keine hat einen Sicherheits-Impact für dieses Profil.

### Container-Sandboxing

**Status:** akzeptiertes Risiko.
Kein `Dockerfile`. Akzeptabel für lokale stdio-Public-Data-Server —
Defense-in-Depth liegt auf der OS-Benutzerebene. Ein gehärtetes Image
ausliefern, falls sich das Deployment-Profil je in die Cloud verschiebt.

### Strukturiertes Logging

**Status:** akzeptiertes Risiko.
Logging nach stderr genügt für einen stdio-Server. JSON-strukturierte Logs mit
Trace-IDs sind hier nicht gerechtfertigt; neu zu bewerten, falls der Server auf
ein Cloud-/SSE-Deployment gehoben wird.

### Rate-Limiting / Quota

**Status:** akzeptiertes Risiko.
geo.admin.ch ist ein öffentlicher Dienst ohne Pro-Key-Quota; der Server setzt auf
Retry-with-Backoff statt auf clientseitiges Rate-Limiting.

## Re-Evaluierungs-Auslöser

Diese Akzeptanzen sollten neu bewertet werden, falls der Server jemals:

- **Schreib**-Funktionalität erhält oder beginnt, **PII** zu verarbeiten, oder
- Tools **dynamisch** / aus entfernten Quellen registriert, oder
- auf ein **Cloud-/SSE**-Deployment verschoben wird (dann werden strukturiertes
  Logging, Container-Sandboxing und die Netzwerk-Binding-Checks relevant), oder
- hinter einem gemeinsamen MCP-Gateway aggregiert wird (dann Tool-Allow-Listing
  und Poisoning-Erkennung auf Gateway-Ebene umsetzen).
