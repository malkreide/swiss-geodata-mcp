# Beitragen zu swiss-geodata-mcp

[🇬🇧 English Version](CONTRIBUTING.md)

Vielen Dank für Ihr Interesse an einem Beitrag zu `swiss-geodata-mcp`! Dieses Projekt ist Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide).

---

## Möglichkeiten zum Mitwirken

### Fehler melden

Eröffnen Sie ein [GitHub-Issue](https://github.com/malkreide/swiss-geodata-mcp/issues) und geben Sie an:

- Eine klare Beschreibung des Problems
- Schritte zur Reproduktion (idealerweise mit den betroffenen LV95-Koordinaten oder dem Layer)
- Erwartetes vs. tatsächliches Verhalten
- Python-Version und Betriebssystem

### Einen neuen Layer oder eine Datenquelle vorschlagen

Der Bundesgeodaten-Katalog umfasst ~700 Layer. Wenn Sie einen Layer finden, der
ein eigenes Tool verdient (statt generischem `geo_identify`-Zugriff):

1. Eröffnen Sie ein Issue mit dem Titel `[Layer] <layer_id>: <kurze Beschreibung>`
2. Geben Sie die Layer-ID, einen Beispiel-Aufruf gegen `api3.geo.admin.ch` und eine Beschreibung der enthaltenen Daten an
3. Verifizieren Sie den Layer idealerweise vor dem Einreichen gegen die Live-API

### Dokumentation verbessern

Tippfehler, unklare Erklärungen oder fehlende Beispiele sind als Pull Requests immer willkommen — kein Issue nötig.

### Code beitragen

1. Forken Sie das Repository
2. Erstellen Sie einen Feature-Branch: `git checkout -b feat/mein-feature`
3. Halten Sie sich an den Code-Stil (Ruff für Linting/Formatierung)
4. Ergänzen oder aktualisieren Sie Tests in `tests/`
5. Führen Sie die Test-Suite vor dem Einreichen aus: `PYTHONPATH=src pytest tests/ -m "not live"`
6. Reichen Sie einen Pull Request mit einer klaren Beschreibung Ihrer Änderungen ein

---

## Entwicklungs-Setup

```bash
git clone https://github.com/malkreide/swiss-geodata-mcp.git
cd swiss-geodata-mcp
pip install -e ".[dev]"
```

**Tests ausführen:**

```bash
# Unit-Tests (keine Netzwerkverbindung erforderlich, respx-gemockt)
PYTHONPATH=src pytest tests/ -m "not live"

# Integrationstests (Live-geo.admin.ch-API)
PYTHONPATH=src pytest tests/ -m "live"
```

**Linten und formatieren:**

```bash
ruff check src/ tests/
ruff format src/ tests/
```

---

## Commit-Konvention

Dieses Projekt verwendet [Conventional Commits](https://www.conventionalcommits.org/):

| Präfix | Verwendung |
|---|---|
| `feat:` | Neues Tool oder neuer Geodaten-Layer |
| `fix:` | Fehlerbehebung |
| `docs:` | Nur Dokumentation |
| `test:` | Tests hinzufügen oder aktualisieren |
| `refactor:` | Code-Umstrukturierung ohne Verhaltensänderung |
| `chore:` | Build, Abhängigkeiten, CI |

---

## Verhaltenskodex

Seien Sie respektvoll und konstruktiv. Dies ist ein kleines Open-Source-Projekt, das in der Freizeit gepflegt wird — Geduld wird geschätzt.

---

## Lizenz

Mit Ihrem Beitrag erklären Sie sich damit einverstanden, dass Ihre Beiträge unter der [MIT-Lizenz](LICENSE) lizenziert werden.
