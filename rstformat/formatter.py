"""Core line-based reStructuredText formatter.

Mirrors the logic of src/formatter/engine.ts so that the Python CLI and the
VS Code extension produce identical output for the same settings.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Optional


DEFAULT_ADORNMENTS = "#*=-^\"'`:.~_+"


class FormatterError(Exception):
    """Raised when the formatter encounters an unrecoverable problem."""


@dataclass
class FormatterSettings:
    adornments: str = DEFAULT_ADORNMENTS
    insert_final_newline: bool = True
    max_consecutive_blank_lines: int = 2
    normalize_section_spacing: bool = True
    normalize_section_underlines: bool = True
    trim_trailing_whitespace: bool = True

    def __post_init__(self) -> None:
        if not self.adornments:
            raise ValueError("adornments must not be empty")
        if self.max_consecutive_blank_lines < 0:
            raise ValueError(
                "max_consecutive_blank_lines must be >= 0, "
                f"got {self.max_consecutive_blank_lines}"
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_width(text: str) -> int:
    """Return the display width of *text* in a fixed-width terminal.

    East Asian wide/fullwidth characters count as 2 columns; all others as 1.
    Equivalent to the ``meaw.computeWidth`` call in the TypeScript engine.
    """
    width = 0
    for ch in unicodedata.normalize("NFC", text):
        eaw = unicodedata.east_asian_width(ch)
        width += 2 if eaw in ("W", "F") else 1
    return width


def _normalize_eol(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _is_blank(line: str) -> bool:
    return line.strip() == ""


def _adornment_char(line: str, adornments: str) -> Optional[str]:
    """Return the adornment character if *line* is a pure adornment line."""
    if not line:
        return None
    ch = line[0]
    if ch not in adornments:
        return None
    if all(c == ch for c in line):
        return ch
    return None


def _get(lines: list[str], index: int) -> str:
    return lines[index] if index < len(lines) else ""


def _is_overline_heading(
    lines: list[str], index: int, adornments: str
) -> Optional[str]:
    """Return the adornment char for an overline heading at *index*."""
    top = _adornment_char(_get(lines, index), adornments)
    title = _get(lines, index + 1)
    bottom = _adornment_char(_get(lines, index + 2), adornments)

    if not top or not bottom or top != bottom or _is_blank(title):
        return None
    return top


def _is_underline_heading(
    lines: list[str],
    index: int,
    adornments: str,
    prev_consumed: int = -1,
) -> Optional[str]:
    """Return the adornment char for an underline heading at *index*.

    *prev_consumed* is the index of the last line already consumed by a
    previous heading.  Lines at or before that index are never treated as
    an overline for the current candidate, avoiding false negatives when
    two consecutive headings share the same adornment character.
    """
    if _is_blank(_get(lines, index)):
        return None

    underline = _adornment_char(_get(lines, index + 1), adornments)
    if not underline:
        return None

    # Avoid misidentifying the bottom half of an overline heading, but
    # only when lines[index-1] has not already been consumed.
    if index > 0 and (index - 1) > prev_consumed:
        overline = _adornment_char(lines[index - 1], adornments)
        if overline == underline:
            return None

    return underline


def _push_normalized(output: list[str], line: str, max_blanks: int) -> None:
    if not _is_blank(line):
        output.append(line)
        return

    blank_count = 0
    for existing in reversed(output):
        if not _is_blank(existing):
            break
        blank_count += 1

    if blank_count < max_blanks:
        output.append("")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def format_restructuredtext(
    text: str,
    settings: Optional[FormatterSettings] = None,
) -> str:
    """Format *text* according to *settings* and return the result.

    Raises
    ------
    ValueError
        If *settings* contains invalid values.
    FormatterError
        If an unrecoverable structural problem is detected at runtime.
    """
    if settings is None:
        settings = FormatterSettings()

    normalized = _normalize_eol(text)
    had_trailing_newline = normalized.endswith("\n")
    lines = normalized.split("\n")

    if had_trailing_newline:
        lines.pop()

    if settings.trim_trailing_whitespace:
        lines = [line.rstrip(" \t") for line in lines]

    output: list[str] = []
    index = 0
    prev_consumed = -1  # index of the last line consumed by a heading
    max_blanks = settings.max_consecutive_blank_lines

    while index < len(lines):
        overline_ch = _is_overline_heading(lines, index, settings.adornments)
        if overline_ch is not None:
            title = lines[index + 1]
            width = (
                _compute_width(title)
                if settings.normalize_section_underlines
                else len(lines[index])
            )

            if (
                settings.normalize_section_spacing
                and output
                and not _is_blank(output[-1])
            ):
                _push_normalized(output, "", max_blanks)

            output.extend([overline_ch * width, title, overline_ch * width])
            prev_consumed = index + 2
            index += 3

            if (
                settings.normalize_section_spacing
                and index < len(lines)
                and not _is_blank(lines[index])
            ):
                _push_normalized(output, "", max_blanks)
            continue

        underline_ch = _is_underline_heading(
            lines, index, settings.adornments, prev_consumed
        )
        if underline_ch is not None:
            title = lines[index]
            width = (
                _compute_width(title)
                if settings.normalize_section_underlines
                else len(lines[index + 1])
            )

            if (
                settings.normalize_section_spacing
                and output
                and not _is_blank(output[-1])
            ):
                _push_normalized(output, "", max_blanks)

            output.extend([title, underline_ch * width])
            prev_consumed = index + 1
            index += 2

            if (
                settings.normalize_section_spacing
                and index < len(lines)
                and not _is_blank(lines[index])
            ):
                _push_normalized(output, "", max_blanks)
            continue

        _push_normalized(output, lines[index], max_blanks)
        prev_consumed = index
        index += 1

    # Strip trailing blank lines.
    while output and _is_blank(output[-1]):
        output.pop()

    result = "\n".join(output)
    if settings.insert_final_newline:
        result += "\n"
    return result
