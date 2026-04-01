"""Tests for the core formatter, mirroring the TypeScript engine tests."""

import pytest
from rstformat.formatter import (
    FormatterError,
    FormatterSettings,
    format_restructuredtext as fmt,
)


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------

def test_passthrough_plain_text():
    assert fmt("Hello world.\n") == "Hello world.\n"


def test_inserts_final_newline():
    assert fmt("Hello") == "Hello\n"


def test_no_insert_final_newline():
    s = FormatterSettings(insert_final_newline=False)
    assert fmt("Hello", s) == "Hello"


def test_trim_trailing_whitespace():
    assert fmt("Hello   \n") == "Hello\n"


def test_no_trim_trailing_whitespace():
    s = FormatterSettings(trim_trailing_whitespace=False)
    assert fmt("Hello   \n", s) == "Hello   \n"


def test_normalize_eol_crlf():
    assert fmt("a\r\nb\r\n") == "a\nb\n"


def test_normalize_eol_cr():
    assert fmt("a\rb\r") == "a\nb\n"


def test_empty_document_with_final_newline():
    # insert_final_newline=True (default) still adds \n to empty content,
    # matching the TypeScript engine's behaviour.
    assert fmt("") == "\n"


def test_empty_document_no_final_newline():
    s = FormatterSettings(insert_final_newline=False)
    assert fmt("", s) == ""


def test_only_blank_lines():
    # All blank lines are stripped; then the final newline is appended.
    assert fmt("\n\n\n") == "\n"


def test_only_blank_lines_no_final_newline():
    s = FormatterSettings(insert_final_newline=False)
    assert fmt("\n\n\n", s) == ""


def test_trailing_blank_lines_stripped():
    assert fmt("Hello\n\n\n") == "Hello\n"


# ---------------------------------------------------------------------------
# Underline headings
# ---------------------------------------------------------------------------

def test_underline_heading_passthrough():
    assert fmt("Title\n=====\n") == "Title\n=====\n"


def test_underline_heading_resize():
    assert fmt("Hi\n=====\n") == "Hi\n==\n"


def test_underline_heading_spacing_before():
    assert fmt("Some text\nTitle\n=====\n") == "Some text\n\nTitle\n=====\n"


def test_underline_heading_spacing_after():
    assert fmt("Title\n=====\nSome text\n") == "Title\n=====\n\nSome text\n"


def test_underline_heading_at_start_no_leading_blank():
    # First heading in the document: no blank line should be prepended.
    assert fmt("Title\n=====\n\nBody.\n") == "Title\n=====\n\nBody.\n"
    # Shorter form: heading only.
    assert fmt("Title\n=====\n") == "Title\n=====\n"


def test_underline_heading_spacing_both_sides():
    text = "Intro.\nFirst\n=====\nBody.\n"
    expected = "Intro.\n\nFirst\n=====\n\nBody.\n"
    assert fmt(text) == expected


# ---------------------------------------------------------------------------
# Overline headings
# ---------------------------------------------------------------------------

def test_overline_heading_passthrough():
    assert fmt("#####\nTitle\n#####\n") == "#####\nTitle\n#####\n"


def test_overline_heading_resize():
    assert fmt("#######\nTitle\n#######\n") == "#####\nTitle\n#####\n"


def test_overline_heading_spacing_before():
    text = "Some text\n\n#####\nTitle\n#####\n"
    assert fmt(text) == "Some text\n\n#####\nTitle\n#####\n"


def test_overline_heading_spacing_after():
    text = "#####\nTitle\n#####\nSome text\n"
    assert fmt(text) == "#####\nTitle\n#####\n\nSome text\n"


def test_overline_heading_at_start_no_leading_blank():
    text = "#####\nTitle\n#####\n\nBody.\n"
    assert fmt(text) == text


# ---------------------------------------------------------------------------
# Multiple headings / realistic document structure
# ---------------------------------------------------------------------------

def test_multiple_underline_headings():
    text = (
        "Chapter One\n"
        "===========\n"
        "Content of chapter one.\n"
        "Chapter Two\n"
        "===========\n"
        "Content of chapter two.\n"
    )
    expected = (
        "Chapter One\n"
        "===========\n"
        "\n"
        "Content of chapter one.\n"
        "\n"
        "Chapter Two\n"
        "===========\n"
        "\n"
        "Content of chapter two.\n"
    )
    assert fmt(text) == expected


def test_mixed_overline_and_underline_headings():
    text = (
        "#############\n"
        "Document Title\n"
        "#############\n"
        "Introduction\n"
        "============\n"
        "Some intro text.\n"
        "Details\n"
        "-------\n"
        "Detail text.\n"
    )
    expected = (
        "##############\n"
        "Document Title\n"
        "##############\n"
        "\n"
        "Introduction\n"
        "============\n"
        "\n"
        "Some intro text.\n"
        "\n"
        "Details\n"
        "-------\n"
        "\n"
        "Detail text.\n"
    )
    assert fmt(text) == expected


def test_consecutive_headings_no_body():
    text = (
        "Part One\n"
        "========\n"
        "Chapter One\n"
        "===========\n"
        "Content.\n"
    )
    expected = (
        "Part One\n"
        "========\n"
        "\n"
        "Chapter One\n"
        "===========\n"
        "\n"
        "Content.\n"
    )
    assert fmt(text) == expected


def test_heading_with_surrounding_blank_lines_unchanged():
    text = (
        "Intro.\n"
        "\n"
        "Title\n"
        "=====\n"
        "\n"
        "Body.\n"
    )
    assert fmt(text) == text


# ---------------------------------------------------------------------------
# Directives and code blocks (must pass through untouched)
# ---------------------------------------------------------------------------

def test_directive_block_preserved():
    text = (
        "Title\n"
        "=====\n"
        "\n"
        ".. note::\n"
        "\n"
        "   This is a note.\n"
        "   It spans two lines.\n"
        "\n"
        "More text.\n"
    )
    assert fmt(text) == text


def test_code_block_indentation_preserved():
    text = (
        "Example\n"
        "-------\n"
        "\n"
        "Usage::\n"
        "\n"
        "    rstformat --check file.rst\n"
        "    rstformat file.rst\n"
        "\n"
        "Done.\n"
    )
    assert fmt(text) == text


def test_literal_block_with_trailing_spaces_trimmed():
    # Trailing whitespace is trimmed even inside literal blocks (line-based).
    s = FormatterSettings(trim_trailing_whitespace=True)
    text = "Usage::\n\n    cmd   \n\nDone.\n"
    assert fmt(text, s) == "Usage::\n\n    cmd\n\nDone.\n"


# ---------------------------------------------------------------------------
# Blank-line limiting
# ---------------------------------------------------------------------------

def test_max_consecutive_blank_lines_default():
    assert fmt("a\n\n\n\nb\n") == "a\n\n\nb\n"


def test_max_consecutive_blank_lines_one():
    s = FormatterSettings(max_consecutive_blank_lines=1)
    assert fmt("a\n\n\nb\n", s) == "a\n\nb\n"


def test_max_consecutive_blank_lines_zero():
    s = FormatterSettings(max_consecutive_blank_lines=0)
    assert fmt("a\n\nb\n", s) == "a\nb\n"


# ---------------------------------------------------------------------------
# No-normalise modes
# ---------------------------------------------------------------------------

def test_no_normalize_section_underlines():
    s = FormatterSettings(normalize_section_underlines=False)
    assert fmt("Hi\n=====\n", s) == "Hi\n=====\n"


def test_no_normalize_section_spacing():
    s = FormatterSettings(normalize_section_spacing=False)
    assert fmt("text\nTitle\n=====\nmore\n", s) == "text\nTitle\n=====\nmore\n"


# ---------------------------------------------------------------------------
# East Asian (wide character) width
# ---------------------------------------------------------------------------

def test_east_asian_width_underline():
    # "标题" = 2 CJK chars × 2 columns = 4 display columns.
    title = "标题"
    assert fmt(f"{title}\n######\n") == f"{title}\n####\n"


def test_east_asian_width_overline():
    title = "标题"
    assert fmt(f"########\n{title}\n########\n") == f"####\n{title}\n####\n"


def test_mixed_ascii_and_wide_chars():
    # "AB标" = 2 + 2 = 4 display columns (A=1, B=1, 标=2).
    title = "AB标"
    assert fmt(f"{title}\n######\n") == f"{title}\n####\n"


# ---------------------------------------------------------------------------
# Line ending control
# ---------------------------------------------------------------------------

def test_line_ending_default_is_lf():
    assert fmt("a\nb\n") == "a\nb\n"


def test_line_ending_crlf():
    s = FormatterSettings(line_ending="crlf")
    assert fmt("a\nb\n", s) == "a\r\nb\r\n"


def test_line_ending_crlf_heading():
    s = FormatterSettings(line_ending="crlf")
    result = fmt("Title\n=====\n\nBody.\n", s)
    assert result == "Title\r\n=====\r\n\r\nBody.\r\n"


def test_line_ending_crlf_input_normalized_before_processing():
    # CRLF input is normalized to LF for processing, then CRLF is re-applied.
    s = FormatterSettings(line_ending="crlf")
    assert fmt("a\r\nb\r\n", s) == "a\r\nb\r\n"


def test_line_ending_auto_detects_crlf():
    s = FormatterSettings(line_ending="auto")
    # Input is predominantly CRLF.
    assert fmt("a\r\nb\r\n", s) == "a\r\nb\r\n"


def test_line_ending_auto_detects_lf():
    s = FormatterSettings(line_ending="auto")
    assert fmt("a\nb\n", s) == "a\nb\n"


def test_line_ending_auto_mixed_prefers_majority():
    s = FormatterSettings(line_ending="auto")
    # 2 CRLF vs 1 LF → CRLF wins.
    assert fmt("a\r\nb\r\nc\n", s) == "a\r\nb\r\nc\r\n"


def test_line_ending_invalid_raises():
    with pytest.raises(ValueError, match="line_ending"):
        FormatterSettings(line_ending="cr")


# ---------------------------------------------------------------------------
# Settings validation — abort on invalid config
# ---------------------------------------------------------------------------

def test_empty_adornments_raises():
    with pytest.raises(ValueError, match="adornments"):
        FormatterSettings(adornments="")


def test_negative_max_blank_lines_raises():
    with pytest.raises(ValueError, match="max_consecutive_blank_lines"):
        FormatterSettings(max_consecutive_blank_lines=-1)


def test_formatter_error_is_exported():
    # FormatterError must be importable for callers that want to catch it.
    assert issubclass(FormatterError, Exception)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
