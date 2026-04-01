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
   └─► line-based formatter ──► formatted RST output
```

docutils is declared as an optional dependency (`pip install rstformat[lint]`).
When absent, structural validation is skipped and formatting still works.

---

## Feature roadmap

### Implemented (v0.1)

| Feature | Setting |
| ------- | ------- |
| Trim trailing whitespace | `trim_trailing_whitespace` |
| Normalize line endings to LF | always on |
| Resize section adornments to title width | `normalize_section_underlines` |
| Add/remove blank lines around headings | `normalize_section_spacing` |
| Limit consecutive blank lines | `max_consecutive_blank_lines` |
| Insert final newline | `insert_final_newline` |
| East-Asian double-width character support | (implicit) |

### Planned

#### Embedded code sections

RST has several ways to include code:

```rst
Example::

    code here            ← indented literal block

.. code-block:: python

    code here            ← fenced directive block

.. literalinclude:: path/to/file
```

The formatter deliberately does **not** reformat the content inside code
blocks because it has no language-specific parser. What it *can* do (planned):

- Detect the start/end of literal blocks and code-block directives.
- Normalize the blank line(s) before and after them (same as heading spacing).
- Optionally normalize the indentation of the block itself (e.g. always use 4
  spaces, never tabs) — controlled by `normalize_code_block_indent`.
- Skip trailing-whitespace trimming for code blocks when
  `preserve_code_block_whitespace = true` (useful for REPL output).

#### Field and option lists

```rst
:param x:  The x value.
:returns:  The result.
```

Planned option: `align_field_list_bodies` — pad the separator `:` so all
body text starts in the same column within a field list.

#### Bullet and enumerated lists

```rst
- Item one
- Item two
```

Planned option: `normalize_list_spacing` — ensure a blank line between
complex list items (items that contain multiple paragraphs) and no blank line
between simple items, following the RST spec.

#### Adornment-order enforcement

RST does not prescribe which character means which heading level; the first
character encountered becomes level 1, the second level 2, and so on. A
future option `enforce_adornment_order` would remap adornment characters to
match a configured sequence (e.g. `#` for parts, `*` for chapters, `=` for
sections) and rewrite the document accordingly.

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

Config is searched from the formatted file's directory upward:

1. `pyproject.toml` → `[tool.rstformat]`
2. `.rstfmt.toml` (root table)
3. Built-in defaults

CLI flags override config-file values for the current invocation only.

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
  __init__.py      public API: FormatterSettings, format_restructuredtext,
                              FormatterError
  formatter.py     core line-based engine (port of engine.ts)
  config.py        TOML config discovery and loading
  cli.py           argparse CLI, --check / --diff / --in-place modes
  __main__.py      python -m rstformat entry point
```

### Invariants

- `format_restructuredtext(text)` is idempotent:
  `format_restructuredtext(format_restructuredtext(text)) == format_restructuredtext(text)`.
- The formatter never silently falls back to a default when configuration
  is invalid; it raises `ValueError` from `FormatterSettings.__post_init__`
  and the CLI exits with code 2.
- `FormatterError` is raised for runtime structural problems (not config
  errors), allowing callers to distinguish the two failure modes.
