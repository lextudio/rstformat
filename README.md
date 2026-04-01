# rstformat

A formatter for reStructuredText files.

[![Become a Sponsor](https://img.shields.io/badge/Become%20a%20Sponsor-lextudio-orange.svg?style=for-readme)](https://github.com/sponsors/lextudio)
[![PyPI](https://img.shields.io/pypi/v/rstformat.svg)](https://pypi.python.org/pypi/rstformat)
[![PyPI Downloads](https://img.shields.io/pypi/dd/rstformat)](https://pypi.python.org/pypi/rstformat/)
[![Python Versions](https://img.shields.io/pypi/pyversions/rstformat.svg)](https://pypi.python.org/pypi/rstformat/)
[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/lextudio/rstformat/master/LICENSE)

An open source and free formatter for reStructuredText (`.rst`) files, distributed under the MIT License.

## Features

| Feature | Setting |
| ------- | ------- |
| Trim trailing whitespace | `trim_trailing_whitespace` |
| Output line ending (LF / CRLF / auto-detect) | `line_ending` |
| Resize section adornments to title width | `normalize_section_underlines` |
| Add/remove blank lines around headings | `normalize_section_spacing` |
| Limit consecutive blank lines | `max_consecutive_blank_lines` |
| Insert final newline | `insert_final_newline` |
| East-Asian double-width character support | (implicit) |

**Plugin system** for delegating embedded code-block formatting to language-specific tools:

- Python code blocks → **Black** or **Ruff** formatter
- Shell script blocks → **shfmt** formatter
- SQL blocks → **sqlfluff** formatter (planned)

## Installation

Install from PyPI:

```bash
pip install rstformat
```

Or with `uv`:

```bash
uv tool install rstformat
```

To enable optional features:

```bash
pip install rstformat[editorconfig]  # Honor .editorconfig settings
pip install rstformat[lint]          # Pre-flight validation via docutils/rstcheck
pip install rstformat[dev]           # Development dependencies (tests, ruff)
```

## Usage

Format files in-place:

```bash
rstformat file.rst dir/
```

Check mode (exit 1 if any file would change):

```bash
rstformat --check file.rst
```

Show unified diff without writing:

```bash
rstformat --diff file.rst
```

Read from stdin, write to stdout:

```bash
echo "Title\n=====" | rstformat
```

Control output line endings:

```bash
rstformat --line-ending crlf file.rst    # Force Windows (CRLF)
rstformat --line-ending auto file.rst    # Preserve input style
```

For all options, run:

```bash
rstformat --help
```

## Configuration

Create `pyproject.toml` or `.rstfmt.toml` in your project:

```toml
[tool.rstformat]
adornments            = "#*=-^\"'`:.~_+"
insert_final_newline  = true
line_ending           = "lf"   # "lf" | "crlf" | "auto"
max_consecutive_blank_lines = 2
normalize_section_spacing   = true
normalize_section_underlines = true
trim_trailing_whitespace     = true
```

rstformat also respects `.editorconfig` for compatible settings:

```ini
[*.rst]
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
```

For more details, see [DESIGN.md](https://github.com/lextudio/rstformat/blob/master/DESIGN.md).

## Documentation

- [Design & Architecture](./DESIGN.md) — formatting algorithm, extension API, roadmap
- [Changelog](./CHANGES.rst) — version history
- [Security Policy](./SECURITY.md) — supported versions, reporting vulnerabilities
- [Development Notes](./AGENTS.md) — for contributors and AI agents

## License

Copyright (c) 2026 LeXtudio Inc.

Licensed under the MIT License. See [LICENSE](./LICENSE) for details.

## Community

- **GitHub Issues**: [Report bugs or request features](https://github.com/lextudio/rstformat/issues)
- **GitHub Discussions**: [Ask questions](https://github.com/lextudio/rstformat/discussions)
- **Sponsor**: [Support development](https://github.com/sponsors/lextudio)
