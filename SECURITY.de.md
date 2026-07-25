# Sicherheitsrichtlinie & Sicherheitslage

[🇬🇧 English Version](SECURITY.md)

`swiss-geodata-mcp` folgt demselben Sicherheitsprofil wie das übrige
[Swiss Public Data MCP Portfolio](https://github.com/malkreide): ein **rein
lesender**, **PII-freier** MCP-Server für **öffentliche Open Data**. Dieses
Dokument hält die angestrebte Sicherheitslage fest sowie die **akzeptierten
Risiken** für Kontrollen, die für ein reines stdio-Profil eines
Public-Open-Data-Servers bewusst zurückgestellt werden.

## Schwachstelle melden

Bitte eröffnen Sie ein privates Security Advisory im GitHub-Repository oder
kontaktieren Sie die in `README.md` genannte verantwortliche Person. Erstellen Sie
für ausnutzbare Schwachstellen **keine** öffentlichen Issues.

## Zusammenfassung der Sicherheitslage

Alle Tools **fragen** die Bundesgeodaten-Infrastruktur nur ab — es gibt keinen
Schreibpfad, keine Authentifizierung und keine Personendaten. Die angestrebte
Härtung für dieses Profil:

| Bereich | Kontrolle |
|---|---|
| Egress | HTTPS-erzwungene Allow-List für die geo.admin.ch-Hosts (`api3.geo.admin.ch`, `geodesy.geo.admin.ch`), vor jeder ausgehenden Anfrage durchgesetzt |
| TLS | Zertifikatsprüfung standardmässig aktiv (httpx-Standard; nie deaktiviert) |
| Transport | Standardmässig stdio — stdout ist für den JSON-RPC-Stream reserviert |
| Input | Pydantic-v2-Validierung für jedes Tool-Input; LV95-Koordinaten werden auf Plausibilität geprüft, mit umsetzbarem Fehlerhinweis auf `geo_convert_coordinates` |
| Secrets | Keine API-Keys oder Zugangsdaten — geo.admin.ch ist vollständig öffentlich, es gibt nichts zu speichern oder zu leaken |
| Fehler | Upstream-Antworten und Stack-Traces werden nur nach stderr geloggt; das Modell sieht eine generische, bereinigte Meldung |
| Stdout | Reserviert für den JSON-RPC-Stream; Logging fest auf stderr |
| Verbindungen | Ein gemeinsamer `httpx.AsyncClient` über die Server-Lebensdauer, nicht pro Aufruf |
| Tests | respx-mockierte Unit-Suite bei jedem PR; Live-API-Tests auf einen Nightly-Job beschränkt |

> **Audit-Status:** Das formale MCP-Best-Practice-Audit (der `audits/`-Ordner und
> das pass/partial/fail-Scorecard, das Geschwister-Server wie `swiss-snb-mcp` und
> `swiss-statistics-mcp` verwenden) wurde für diesen Server **noch nicht
> durchgeführt**. Es wird ergänzt, sobald die Implementierung vorliegt, und dieser
> Abschnitt dann auf den Audit-Bericht verweisen.

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
