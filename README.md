# rstformat

A formatter for reStructuredText files.

## Installation

```bash
pip install rstformat
```

Or with uv:

```bash
uv tool install rstformat
```

## Usage

```bash
# Format files in-place
rstformat file.rst

# Check mode (exit 1 if any file would change)
rstformat --check file.rst

# Show diff without writing
rstformat --diff file.rst

# Read from stdin, write to stdout
echo "Title\n=====" | rstformat

# Force Windows line endings
rstformat --line-ending crlf file.rst

# Preserve the original line endings of each file
rstformat --line-ending auto file.rst
```

## Configuration

Add to `pyproject.toml`:

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

Or create `.rstfmt.toml` in the project root with the same keys (no
`[tool.rstformat]` wrapper needed).

### `line_ending`

| Value | Behaviour |
| ----- | --------- |
| `"lf"` | Always write Unix line endings (`\n`). Default. |
| `"crlf"` | Always write Windows line endings (`\r\n`). |
| `"auto"` | Detect from the input file: use CRLF if CRLF outnumbers bare LF, otherwise LF. |

## Exit codes

| Code | Meaning |
| ---- | ------- |
| 0 | All files are already formatted (or `--check` found no changes). |
| 1 | `--check` found files that would be reformatted. |
| 2 | Error (bad arguments, unreadable file, invalid config). |
