from __future__ import annotations

import argparse
from collections.abc import Sequence

import nbformat


def test_no_errors_or_warnings_in_output(notebook):
    """checks if all example Jupyter notebooks have clear std-err output
    (i.e., no errors or warnings) visible; except acceptable
    diagnostics from the joblib package"""
    for cell in notebook.cells:
        if cell.cell_type == "code":
            for output in cell.outputs:
                if "name" in output and output["name"] == "stderr":
                    if not output["text"].startswith("[Parallel(n_jobs="):
                        raise AssertionError(output["text"])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    args = parser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        with open(filename, encoding="utf8") as notebook_file:
            notebook = nbformat.read(notebook_file, nbformat.NO_CONVERT)
            try:
                test_no_errors_or_warnings_in_output(notebook)
            except ValueError as exc:
                retval = 1
    return retval


if __name__ == "__main__":
    raise SystemExit(main())
