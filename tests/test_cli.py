"""Tests for the CLI's UTF-8 handling under non-UTF-8 console encodings."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Title -> expected underline for a document formatted with default settings.
WIDTH_CASES = [
    ("标题", "===="),
    ("中文标题", "========"),
    ("Hello", "====="),
    ("ＡＢ", "===="),
    ("café", "===="),
    ("🩷", "=="),
    ("e\u0301", "="),
]


def run_cli(*args, stdin=b"", console_encoding=None):
    """Run ``python -m rstformat`` with a controlled stdio encoding."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    if console_encoding is None:
        env.pop("PYTHONIOENCODING", None)
    else:
        env["PYTHONIOENCODING"] = console_encoding
    return subprocess.run(
        [sys.executable, "-m", "rstformat", *args],
        input=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(ROOT),
        env=env,
        check=False,
    )


@pytest.mark.parametrize("console_encoding", ["gbk", "cp1252", "ascii"])
@pytest.mark.parametrize("title,underline", WIDTH_CASES)
def test_stdin_and_stdout_are_utf8(console_encoding, title, underline):
    source = f"{title}\n==\n\n正文\n"
    expected = f"{title}\n{underline}\n\n正文\n".encode("utf-8")

    result = run_cli(stdin=source.encode("utf-8"), console_encoding=console_encoding)

    assert result.returncode == 0, result.stderr
    assert result.stdout == expected


@pytest.mark.parametrize("console_encoding", ["gbk", "ascii"])
def test_diff_output_is_utf8(console_encoding):
    source = "标题\n==\n\n正文\n"

    result = run_cli(
        "--diff",
        stdin=source.encode("utf-8"),
        console_encoding=console_encoding,
    )

    assert result.returncode == 0, result.stderr
    output = result.stdout.decode("utf-8")
    assert "--- stdin (original)" in output
    assert "+++ stdin (formatted)" in output
    assert "====" in output


def test_file_mode_is_utf8(tmp_path):
    path = tmp_path / "doc.rst"
    path.write_text("标题\n==\n\n正文\n", encoding="utf-8")

    result = run_cli(str(path), console_encoding="gbk")

    assert result.returncode == 0, result.stderr
    assert path.read_text(encoding="utf-8") == "标题\n====\n\n正文\n"


def test_file_diff_output_is_utf8(tmp_path):
    path = tmp_path / "doc.rst"
    path.write_text("标题\n==\n\n正文\n", encoding="utf-8")

    result = run_cli("--diff", str(path), console_encoding="ascii")

    assert result.returncode == 0, result.stderr
    assert "====" in result.stdout.decode("utf-8")


@pytest.mark.parametrize("console_encoding", ["gbk", "ascii"])
def test_check_mode_uses_stdout_independently(console_encoding):
    formatted = "标题\n====\n\n正文\n".encode("utf-8")
    unformatted = "标题\n==\n\n正文\n".encode("utf-8")

    assert run_cli("--check", stdin=formatted, console_encoding=console_encoding).returncode == 0

    result = run_cli("--check", stdin=unformatted, console_encoding=console_encoding)
    assert result.returncode == 1
    assert b"would reformat" in result.stderr


def test_invalid_utf8_stdin_fails_cleanly():
    result = run_cli(stdin="标题".encode("gbk"), console_encoding="gbk")

    assert result.returncode != 0
    assert b"Traceback" not in result.stderr
    assert b"UTF-8" in result.stderr
