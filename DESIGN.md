# rstformat — Design Notes

## Goals

1. Format `.rst` files consistently so that automated diffs contain only
   meaningful content changes.
2. Integrate with pre-commit hooks, CI pipelines, and editors (VS Code, etc.).
3. Produce output that is byte-for-byte identical whether formatting is done
   by the VS Code extension (TypeScript engine) or the CLI (Python engine).
4. Be configurable per-project; ship with safe, widely-accepted defaults.
5. Abort clearly on bad configuration or structural problems; never silently
   corrupt a file.
6. Support a plugin system so that embedded code blocks can be delegated to
   language-specific formatters, with a set of built-in extensions shipped
   out of the box.

---

## Approach: line-based, not AST-based

### Why not use docutils as the output serializer?

docutils can parse RST into a document tree and write it back. This would be
the most "correct" approach in theory, but in practice it has serious drawbacks
for a formatter:

| Concern | Detail |
| ------- | ------ |
| **Round-trip fidelity** | docutils discards comments that appear inside directives, exact blank-line counts, non-standard adornment sequences, and other details that are invisible to the document model but matter to authors. |
| **Directives and roles** | Custom directives (Sphinx `.. toctree::`, `.. autoclass::`, etc.) may not be registered, so the parser raises warnings or errors instead of passing them through. |
| **Inline markup** | Re-serializing inline markup changes spacing around backticks, asterisks, and roles in ways that are difficult to control. |
| **Streaming** | The AST approach requires loading the entire document into memory and re-emitting it, making incremental/range formatting harder. |

### Why use docutils at all?

docutils **is** useful for:

- **Structural validation** — detecting malformed headings, unclosed
  directives, or unknown roles before we write back to disk (abort-on-error
  behavior requested in the design goals).
- **Section level inference** — determining which adornment character
  corresponds to which heading depth, which enables future features such as
  enforcing a consistent adornment order.

The intended integration model is therefore **hybrid**:

```text
Input RST
   │
   ├─► docutils parser ──► structural errors? → FormatterError / abort
   │
   └─► line-based formatter ──► code-block extension hooks ──► formatted RST
```

docutils is declared as an optional dependency (`pip install rstformat[lint]`).
When absent, structural validation is skipped and formatting still works.

---

## Extension system

### Motivation

No single tool formats all languages that can appear in RST code blocks.
The existing landscape (as of 2026):

| Tool | Languages | Works with RST? |
| ---- | --------- | --------------- |
| **blacken-docs** | Python only | Yes — targets `.. code-block:: python` and `::` blocks |
| **Ruff formatter** | Python only | Docstrings only; open issue to extend to RST files |
| **prettier** | JS/TS/CSS/HTML/… | No RST support (issue open since 2019, unimplemented) |
| **sqlfluff** | SQL dialects | CLI only; no RST integration |
| **shfmt** | Shell | CLI only; no RST integration |
| **mdformat** | Markdown | Plugin system for per-language blocks, but Markdown-only |

rstformat fills the RST gap with a plugin architecture modeled on mdformat:
each extension handles one or more languages and is completely independent of
the core formatter.

### Extension interface

An extension is a Python class that implements `CodeBlockExtension`:

```python
# rstformat/ext/base.py

class CodeBlock:
    language: str       # e.g. "python", "sql", "bash"
    lines: list[str]    # content lines without leading/trailing blank lines
    indent: str         # indentation string used in the source (e.g. "    ")
    source_line: int    # 1-based line number of the first content line

class CodeBlockExtension:
    #: Languages this extension handles, lower-cased.
    languages: tuple[str, ...]

    def format(self, block: CodeBlock) -> list[str]:
        """Return the reformatted lines (same indentation, no trailing blank).

        Raise FormatterError to abort the entire formatting run.
        Raise CodeBlockSkipped to leave the block unchanged.
        """
```

`CodeBlockSkipped` is a sentinel exception — not an error — that tells the
formatter to emit the block as-is.  This allows extensions to skip blocks
that fail to parse rather than aborting (e.g. a Python block with a syntax
error).

### Registration

Extensions are registered via Python package entry points so that
third-party packages can add new languages without modifying rstformat:

```toml
# in a third-party package's pyproject.toml
[project.entry-points."rstformat.extensions"]
my-lang = "mypkg.rstformat_ext:MyLangExtension"
```

Built-in extensions are pre-registered in rstformat's own `pyproject.toml`
under the same group and are always available (subject to their optional
external tool being installed).

### Configuration

```toml
[tool.rstformat]
# Enable built-in extensions explicitly (default: all built-ins enabled).
extensions = ["python", "shell"]

# Per-extension settings.
[tool.rstformat.ext.python]
# "black" | "ruff" — which backend to use (default: auto-detect).
backend = "ruff"
line_length = 88
skip_errors = true   # leave syntactically invalid blocks unchanged

[tool.rstformat.ext.shell]
# Path to shfmt binary (default: "shfmt" on PATH).
shfmt_path = "/usr/local/bin/shfmt"
indent = 4
```

---

## Built-in extensions

### `python` — formats Python code blocks

Handles: `python`, `python3`, `py`, `pycon` (interactive sessions), `pytest`

Backends (tried in order if `backend = "auto"`):

1. **ruff** (`ruff format -`) — preferred; faster and handles more syntax.
2. **black** — fallback if ruff is not on PATH.

`pycon` / interactive blocks: strips `>>>` prompts, formats the statements,
re-inserts prompts.  Skips the block if formatting would change the output
lines of an interactive session.

When `skip_errors = true` (default), a block that Black/ruff cannot parse
raises `CodeBlockSkipped` instead of `FormatterError`.

### `shell` — formats shell script blocks

Handles: `bash`, `sh`, `shell`, `zsh`

Delegates to **shfmt** (`shfmt -`). Requires `shfmt` to be on `PATH` or
configured via `shfmt_path`. Skips the block if shfmt exits non-zero.

### `sql` — formats SQL blocks (planned)

Handles: `sql`, `postgresql`, `mysql`, `sqlite`

Delegates to **sqlfluff** (`sqlfluff format -`). Dialect must be configured:

```toml
[tool.rstformat.ext.sql]
dialect = "postgres"
```

---

## Feature roadmap

### Implemented (v0.1)

| Feature | Setting |
| ------- | ------- |
| Trim trailing whitespace | `trim_trailing_whitespace` |
| Output line ending (LF / CRLF / auto-detect from input) | `line_ending` |
| Resize section adornments to title width | `normalize_section_underlines` |
| Add/remove blank lines around headings | `normalize_section_spacing` |
| Limit consecutive blank lines | `max_consecutive_blank_lines` |
| Insert final newline | `insert_final_newline` |
| East-Asian double-width character support | (implicit) |

### Planned (v0.2)

| Feature | Mechanism |
| ------- | --------- |
| Python code-block formatting | built-in `python` extension |
| Shell code-block formatting | built-in `shell` extension |
| Normalize blank lines around code blocks | core formatter |
| Normalize code-block indentation | `normalize_code_block_indent` setting |
| Tab → space expansion (configurable indent width) | `indent_char` / `indent_width` settings |
| Preserve whitespace inside code blocks | `preserve_code_block_whitespace` setting |
| Third-party extension loading via entry points | extension registry |

### Planned (v0.3+)

| Feature | Mechanism |
| ------- | --------- |
| SQL code-block formatting | built-in `sql` extension |
| Field-list body alignment | `align_field_list_bodies` setting |
| List spacing normalization | `normalize_list_spacing` setting |
| Adornment-order enforcement | `enforce_adornment_order` setting |
| Pre-flight structural validation | `pre_check = true` via rstcheck/docutils |

---

## Using an existing linter as the foundation

Several linters exist for RST:

| Tool | Basis | Notes |
| ---- | ----- | ----- |
| **rstcheck** | docutils | Validates RST syntax and embedded code blocks; reports errors but does not format. |
| **doc8** | docutils | Style checker (line length, trailing whitespace, etc.); no formatting. |
| **sphinx-lint** | regex | Lightweight; fast but limited structural understanding. |

### Recommended integration: rstcheck for pre-flight validation

Rather than reimplementing structural validation, rstformat can optionally
run **rstcheck** (or call docutils directly) on the input before formatting
and abort if it reports errors. This keeps the formatter's own code simple
while leveraging a mature validation layer.

```toml
[tool.rstformat]
# Abort if rstcheck finds errors in the input before formatting.
pre_check = true          # default: false (rstcheck must be installed)
pre_check_roles = ["py"]  # extra Sphinx roles to register
```

When `pre_check = true` and the document has structural errors, rstformat
exits with code 2 (error), prints the rstcheck output to stderr, and writes
nothing to disk.

---

## Configuration discovery

Settings are resolved in priority order (highest wins):

1. **CLI flags** — apply for the current invocation only.
2. **`pyproject.toml` → `[tool.rstformat]`** — searched upward from the
   target file's directory.
3. **`.rstfmt.toml`** — searched upward from the target file's directory
   (used when `pyproject.toml` is absent or has no `[tool.rstformat]` table).
4. **`.editorconfig`** — the standard per-directory config supported by most
   editors; searched upward from the target file.  Only the properties that
   overlap with rstformat settings are read (see table below).
5. **Built-in defaults** — lowest priority.

### EditorConfig mapping

rstformat reads `.editorconfig` when the optional `editorconfig` package is
installed (`pip install rstformat[editorconfig]`).  When it is absent,
`.editorconfig` is silently ignored.

| EditorConfig property | rstformat setting | Notes |
| --------------------- | ----------------- | ----- |
| `end_of_line = lf\|crlf` | `line_ending` | `cr` is treated as `lf` |
| `insert_final_newline = true\|false` | `insert_final_newline` | |
| `trim_trailing_whitespace = true\|false` | `trim_trailing_whitespace` | |
| `indent_style = space\|tab` | `indent_char` (planned) | |
| `indent_size = N` | `indent_width` (planned) | |

An explicit `[tool.rstformat]` value always overrides the EditorConfig value
for the same setting, so projects can adopt EditorConfig globally and still
fine-tune rstformat independently.

---

## Exit codes

| Code | Meaning |
| ---- | ------- |
| 0 | Success; all files already formatted (or `--check` found no changes) |
| 1 | `--check` found files that would be reformatted |
| 2 | Error: bad arguments, unreadable file, invalid config, or structural error detected by pre-flight validation |

---

## Architecture

```text
rstformat/
  __init__.py        public API: FormatterSettings, format_restructuredtext,
                                 FormatterError
  formatter.py       core line-based engine (port of engine.ts)
  config.py          TOML config discovery and loading
  cli.py             argparse CLI, --check / --diff / --in-place modes
  __main__.py        python -m rstformat entry point
  ext/
    base.py          CodeBlockExtension ABC, CodeBlock, CodeBlockSkipped
    registry.py      discovers and loads extensions via entry points
    python.py        built-in Python extension (black / ruff backend)
    shell.py         built-in shell extension (shfmt backend)
    sql.py           built-in SQL extension (sqlfluff backend) [planned]
```

### Invariants

- `format_restructuredtext(text)` is idempotent:
  `format_restructuredtext(format_restructuredtext(text)) == format_restructuredtext(text)`.
- The formatter never silently falls back to a default when configuration
  is invalid; it raises `ValueError` from `FormatterSettings.__post_init__`
  and the CLI exits with code 2.
- `FormatterError` is raised for runtime structural problems (not config
  errors), allowing callers to distinguish the two failure modes.
- An extension that cannot format a block raises `CodeBlockSkipped` to leave
  it unchanged, or `FormatterError` to abort the entire run.  It never
  silently produces subtly wrong output.
