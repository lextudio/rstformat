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

# Show diff
rstformat --diff file.rst

# Read from stdin, write to stdout
echo "Title\n=====" | rstformat
```

## Configuration

Add to `pyproject.toml`:

```toml
[tool.rstformat]
adornments = "#*=-^\"'`:.~_+"
insert_final_newline = true
max_consecutive_blank_lines = 2
normalize_section_spacing = true
normalize_section_underlines = true
trim_trailing_whitespace = true
```
