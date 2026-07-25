# Contributing to swiss-geodata-mcp

[🇩🇪 Deutsche Version](CONTRIBUTING.de.md)

Thank you for your interest in contributing to `swiss-geodata-mcp`! This project is part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide).

---

## Ways to Contribute

### Report a Bug

Open a [GitHub Issue](https://github.com/malkreide/swiss-geodata-mcp/issues) and include:

- A clear description of the problem
- Steps to reproduce (ideally with the LV95 coordinates or layer involved)
- Expected vs. actual behaviour
- Python version and OS

### Suggest a New Layer or Data Source

The federal geodata catalogue spans ~700 layers. If you find a layer that
deserves a dedicated tool (rather than generic `geo_identify` access):

1. Open an issue with the title `[Layer] <layer_id>: <short description>`
2. Include the layer ID, a sample `api3.geo.admin.ch` call, and a description of the data it contains
3. Ideally, verify it against the live API before submitting

### Improve Documentation

Typos, unclear explanations, or missing examples are always welcome as pull requests — no issue needed.

### Contribute Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Follow the code style (Ruff for linting/formatting)
4. Add or update tests in `tests/`
5. Run the test suite before submitting: `PYTHONPATH=src pytest tests/ -m "not live"`
6. Submit a pull request with a clear description of your changes

---

## Development Setup

```bash
git clone https://github.com/malkreide/swiss-geodata-mcp.git
cd swiss-geodata-mcp
pip install -e ".[dev]"
```

**Run tests:**

```bash
# Unit tests (no network required, respx-mocked)
PYTHONPATH=src pytest tests/ -m "not live"

# Integration tests (live geo.admin.ch API)
PYTHONPATH=src pytest tests/ -m "live"
```

**Lint and format:**

```bash
ruff check src/ tests/
ruff format src/ tests/
```

---

## Commit Convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | When to use |
|---|---|
| `feat:` | New tool or new geodata layer |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `test:` | Adding or updating tests |
| `refactor:` | Code restructuring without behaviour change |
| `chore:` | Build, dependencies, CI |

---

## Code of Conduct

Be respectful and constructive. This is a small open-source project maintained in spare time — patience is appreciated.

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
