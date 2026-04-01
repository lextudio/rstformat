"""Tests for the core formatter, mirroring the TypeScript engine tests."""

import pytest
from rstformat.formatter import FormatterSettings, format_restructuredtext as fmt


def test_passthrough_plain_text():
    text = "Hello world.\n"
    assert fmt(text) == text


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


# --- Underline headings ---

def test_underline_heading_normalization():
    text = "Title\n=====\n"
    assert fmt(text) == "Title\n=====\n"


def test_underline_heading_resize():
    text = "Hi\n=====\n"
    assert fmt(text) == "Hi\n==\n"


def test_underline_heading_spacing_before():
    text = "Some text\nTitle\n=====\n"
    result = fmt(text)
    assert result == "Some text\n\nTitle\n=====\n"


def test_underline_heading_spacing_after():
    text = "Title\n=====\nSome text\n"
    result = fmt(text)
    assert result == "Title\n=====\n\nSome text\n"


# --- Overline headings ---

def test_overline_heading_normalization():
    text = "#####\nTitle\n#####\n"
    assert fmt(text) == "#####\nTitle\n#####\n"


def test_overline_heading_resize():
    text = "#######\nTitle\n#######\n"
    assert fmt(text) == "#####\nTitle\n#####\n"


def test_overline_heading_spacing_before():
    # Blank line is required to separate plain text from an overline heading;
    # without it "Some text\n#####" is parsed as an underline heading.
    text = "Some text\n\n#####\nTitle\n#####\n"
    result = fmt(text)
    assert result == "Some text\n\n#####\nTitle\n#####\n"


def test_overline_heading_spacing_after():
    text = "#####\nTitle\n#####\nSome text\n"
    result = fmt(text)
    assert result == "#####\nTitle\n#####\n\nSome text\n"


# --- Blank line limits ---

def test_max_consecutive_blank_lines():
    text = "a\n\n\n\nb\n"
    assert fmt(text) == "a\n\n\nb\n"


def test_custom_max_consecutive_blank_lines():
    s = FormatterSettings(max_consecutive_blank_lines=1)
    assert fmt("a\n\n\nb\n", s) == "a\n\nb\n"


def test_trailing_blank_lines_stripped():
    assert fmt("Hello\n\n\n") == "Hello\n"


# --- No-normalize modes ---

def test_no_normalize_section_underlines():
    s = FormatterSettings(normalize_section_underlines=False)
    text = "Hi\n=====\n"
    assert fmt(text, s) == "Hi\n=====\n"


def test_no_normalize_section_spacing():
    s = FormatterSettings(normalize_section_spacing=False)
    text = "text\nTitle\n=====\nmore\n"
    assert fmt(text, s) == "text\nTitle\n=====\nmore\n"


# --- East Asian width ---

def test_east_asian_width_underline():
    # Each CJK character is 2 columns wide, so "标题" = 4 display columns.
    # The adornment char (#) is preserved; only the length is resized.
    title = "标题"  # 2 chars × 2 = 4 columns
    text = f"{title}\n######\n"
    result = fmt(text)
    assert result == f"{title}\n####\n"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
