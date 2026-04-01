# Repository Notes

## For AI Agents (Claude, etc.)

Welcome! Here are the key conventions for this repository:

### Development Environment

- Use `uv run` for all Python commands.
- Prefer [`scripts/`](./scripts) over ad hoc invocations:
  - `python scripts/prepare.py [VERSION]` — pin Python version and sync environment
  - `python scripts/tests.py [--coverage] [--verbose]` — run the test suite
  - `python scripts/build.py` — build wheels and sdists
  - `python scripts/publish.py` — publish to PyPI (requires `~/.pypirc`)
  - `python scripts/bump.py [--major|--minor|--patch]` — bump version

### Project Structure

```
rstformat/
  __init__.py       public API + __version__
  formatter.py      core formatting engine
  config.py         TOML config discovery & loading
  cli.py            argparse CLI
  __main__.py       python -m rstformat entry point
  ext/
    base.py         extension system ABC
    registry.py     extension loader
    python.py       Python code-block extension
    shell.py        shell code-block extension
    sql.py          SQL extension (planned)

tests/              pytest test suite (49 tests, all passing)
DESIGN.md           architecture, roadmap, extension API
CHANGES.rst         changelog
SECURITY.md         security policy
```

### Testing

Run tests before submitting changes:

```bash
python scripts/tests.py --coverage
```

### Version Bumping

Update the version **before** submitting a PR (not after):

```bash
python scripts/bump.py --minor  # 0.1.x → 0.2.0
```

This updates `pyproject.toml` and `rstformat/__init__.py` automatically.

### Configuration Files

- `.bumpversion.cfg` — version numbering rules
- `.python-version` — Python version pin (currently 3.13)
- `pyproject.toml` — package metadata, dependencies, build config
- `.editorconfig` — not used by rstformat itself, but honored if present

### Code Style

- Use `ruff format` (via `uv run`) for formatting
- Follow PEP 8; ruff is configured in `pyproject.toml`
- Add tests for any new features or bug fixes
- Keep the formatter idempotent: formatting twice should give the same result
