"""Command-line interface for rstformat."""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path
from typing import Optional, Sequence

from . import __version__
from .config import load_settings
from .formatter import FormatterSettings, format_restructuredtext


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rstformat",
        description="Format reStructuredText files.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    parser.add_argument(
        "files",
        metavar="FILE",
        nargs="*",
        help="Files to format. Use - to read from stdin (default when no files given).",
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if any file would change; do not write.",
    )
    mode.add_argument(
        "--diff",
        action="store_true",
        help="Print a unified diff for each file that would change.",
    )

    parser.add_argument(
        "--config",
        metavar="PATH",
        help="Explicit path to a TOML config file.",
    )

    # Per-setting overrides
    parser.add_argument("--adornments", metavar="CHARS")
    parser.add_argument(
        "--no-insert-final-newline",
        dest="insert_final_newline",
        action="store_false",
        default=None,
    )
    parser.add_argument(
        "--line-ending",
        choices=["lf", "crlf", "auto"],
        dest="line_ending",
        help="Output line ending: lf (default), crlf, or auto (detect from input).",
    )
    parser.add_argument(
        "--max-consecutive-blank-lines",
        metavar="N",
        type=int,
        dest="max_consecutive_blank_lines",
    )
    parser.add_argument(
        "--no-normalize-section-spacing",
        dest="normalize_section_spacing",
        action="store_false",
        default=None,
    )
    parser.add_argument(
        "--no-normalize-section-underlines",
        dest="normalize_section_underlines",
        action="store_false",
        default=None,
    )
    parser.add_argument(
        "--no-trim-trailing-whitespace",
        dest="trim_trailing_whitespace",
        action="store_false",
        default=None,
    )

    return parser


def _apply_overrides(settings: FormatterSettings, args: argparse.Namespace) -> None:
    if args.adornments is not None:
        settings.adornments = args.adornments
    if args.insert_final_newline is not None:
        settings.insert_final_newline = args.insert_final_newline
    if args.max_consecutive_blank_lines is not None:
        settings.max_consecutive_blank_lines = max(0, args.max_consecutive_blank_lines)
    if args.normalize_section_spacing is not None:
        settings.normalize_section_spacing = args.normalize_section_spacing
    if args.normalize_section_underlines is not None:
        settings.normalize_section_underlines = args.normalize_section_underlines
    if args.trim_trailing_whitespace is not None:
        settings.trim_trailing_whitespace = args.trim_trailing_whitespace
    if args.line_ending is not None:
        settings.line_ending = args.line_ending


def _format_stdin(settings: FormatterSettings, args: argparse.Namespace) -> int:
    original = sys.stdin.read()
    formatted = format_restructuredtext(original, settings)

    if args.check:
        if original != formatted:
            print("stdin: would reformat", file=sys.stderr)
            return 1
        return 0

    if args.diff:
        diff = list(
            difflib.unified_diff(
                original.splitlines(keepends=True),
                formatted.splitlines(keepends=True),
                fromfile="stdin (original)",
                tofile="stdin (formatted)",
            )
        )
        if diff:
            sys.stdout.writelines(diff)
        return 0

    sys.stdout.write(formatted)
    return 0


def _format_file(
    path: Path,
    settings: FormatterSettings,
    args: argparse.Namespace,
) -> bool:
    """Format a single file.  Returns True if the content changed."""
    try:
        original = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: {path}: {exc}", file=sys.stderr)
        return False

    formatted = format_restructuredtext(original, settings)
    changed = original != formatted

    if args.diff and changed:
        diff = list(
            difflib.unified_diff(
                original.splitlines(keepends=True),
                formatted.splitlines(keepends=True),
                fromfile=f"{path} (original)",
                tofile=f"{path} (formatted)",
            )
        )
        sys.stdout.writelines(diff)

    if not args.check and not args.diff and changed:
        path.write_text(formatted, encoding="utf-8")

    return changed


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    config_path = Path(args.config) if args.config else None
    settings = load_settings(config_path=config_path)
    _apply_overrides(settings, args)

    files = args.files or []

    # Stdin mode: no files given, or explicit "-"
    if not files or files == ["-"]:
        return _format_stdin(settings, args)

    any_changed = False
    exit_code = 0

    for file_arg in files:
        if file_arg == "-":
            rc = _format_stdin(settings, args)
            if rc:
                exit_code = rc
            continue

        path = Path(file_arg)
        if not path.is_file():
            print(f"error: {path}: not a file", file=sys.stderr)
            exit_code = 2
            continue

        # Use the file's directory as the config search root so per-directory
        # config files are picked up automatically (unless --config was given).
        if config_path is None:
            file_settings = load_settings(search_from=path.parent)
            _apply_overrides(file_settings, args)
        else:
            file_settings = settings

        changed = _format_file(path, file_settings, args)
        if changed:
            any_changed = True
            if args.check:
                print(f"would reformat: {path}", file=sys.stderr)

    if args.check and any_changed:
        exit_code = 1

    return exit_code


def entry_point() -> None:
    sys.exit(main())
