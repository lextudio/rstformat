"""Configuration discovery and loading for rstformat.

Search order (highest to lowest priority):
  1. CLI flags (handled in cli.py)
  2. [tool.rstformat] in pyproject.toml
  3. .rstfmt.toml
  4. Built-in defaults (FormatterSettings())
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

from .formatter import FormatterSettings

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib  # type: ignore[no-redef]
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            tomllib = None  # type: ignore[assignment]

_CONFIG_FILENAMES = ("pyproject.toml", ".rstfmt.toml")


def _find_config(start: Path) -> Optional[tuple[Path, str]]:
    """Walk *start* and its parents looking for a config file.

    Returns ``(path, key)`` where *key* is ``"tool.rstformat"`` for
    ``pyproject.toml`` or ``""`` for ``.rstfmt.toml``, or ``None`` if not found.
    """
    for directory in [start, *start.parents]:
        candidate = directory / "pyproject.toml"
        if candidate.is_file():
            return candidate, "tool.rstformat"
        candidate = directory / ".rstfmt.toml"
        if candidate.is_file():
            return candidate, ""
    return None


def _load_table(path: Path, key: str) -> dict[str, Any]:
    if tomllib is None:
        return {}

    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    if key:
        # Navigate nested keys: "tool.rstformat" → data["tool"]["rstformat"]
        for part in key.split("."):
            if not isinstance(data, dict):
                return {}
            data = data.get(part, {})

    return data if isinstance(data, dict) else {}


def load_settings(
    config_path: Optional[Path] = None,
    search_from: Optional[Path] = None,
) -> FormatterSettings:
    """Return a :class:`FormatterSettings` loaded from the nearest config file.

    Parameters
    ----------
    config_path:
        Explicit path to a TOML config file (overrides auto-discovery).
    search_from:
        Directory to start the upward config search from.  Defaults to
        ``Path.cwd()``.
    """
    if config_path is not None:
        table = _load_table(config_path, "")
    else:
        result = _find_config(search_from or Path.cwd())
        table = _load_table(*result) if result else {}

    settings = FormatterSettings()

    if "adornments" in table:
        settings.adornments = str(table["adornments"])
    if "insert_final_newline" in table:
        settings.insert_final_newline = bool(table["insert_final_newline"])
    if "max_consecutive_blank_lines" in table:
        settings.max_consecutive_blank_lines = max(
            0, int(table["max_consecutive_blank_lines"])
        )
    if "normalize_section_spacing" in table:
        settings.normalize_section_spacing = bool(table["normalize_section_spacing"])
    if "normalize_section_underlines" in table:
        settings.normalize_section_underlines = bool(table["normalize_section_underlines"])
    if "trim_trailing_whitespace" in table:
        settings.trim_trailing_whitespace = bool(table["trim_trailing_whitespace"])

    return settings
