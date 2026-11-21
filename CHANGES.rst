Revision 0.1.1, released on Nov 21, 2026
-----------------------------------------

- Read stdin and write stdout as UTF-8 regardless of the console encoding,
  fixing incorrect section underline lengths for CJK text on Windows (#1).
- Emit ``--diff`` output as UTF-8.
- Report invalid UTF-8 stdin with a clear error instead of a traceback.
- Add CLI encoding regression tests.
- Add GitHub Actions CI for Linux, macOS, and Windows.

Revision 0.1.0, released on Apr 01, 2026
-----------------------------------------

- Initial release with core line-based formatter.
- Supports heading normalization, blank-line limits, trailing-whitespace trimming.
- East Asian wide-character support for adornment sizing.
- CLI with ``--check``, ``--diff``, and ``--in-place`` modes.
- Configuration via ``pyproject.toml`` or ``.rstfmt.toml``.
- Extension system design documented for future code-block formatting support.
