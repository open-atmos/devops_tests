#!/usr/bin/env python3
"""
Checks whether notebooks contain badges."""
from __future__ import annotations

import argparse
from collections.abc import Sequence

import nbformat

from .utils import (
    relative_path,
    repo_path,
)

HEADER = f"""import os, sys
os.environ['NUMBA_THREADING_LAYER'] = 'omp'  # PySDM and PyMPDATA are incompatible with TBB threads
if 'google.colab' in sys.modules:
    !pip --quiet install open-atmos-jupyter-utils
    from open_atmos_jupyter_utils import pip_install_on_colab
    pip_install_on_colab('{repo_path().name}-examples')"""

HEADER_KEY_PATTERNS = [
    "install open-atmos-jupyter-utils",
    "google.colab",
    "pip_install_on_colab",
]


def is_colab_header(cell_source: str) -> bool:
    """Return True if the cell looks like a Colab header."""
    return all(pat in cell_source for pat in HEADER_KEY_PATTERNS)


def fix_colab_header(notebook_path):
    """Check Colab-magic cell and fix if is misspelled, in wrong position or not exists"""
    nb = nbformat.read(notebook_path, as_version=nbformat.NO_CONVERT)

    header_index = None
    for idx, cell in enumerate(nb.cells):
        if cell.cell_type == "code" and is_colab_header(cell.source):
            header_index = idx
            break

    modified = False
    if header_index is not None:
        if nb.cells[header_index].source != HEADER:
            nb.cells[header_index].source = HEADER
            modified = True
        if header_index != 2:
            nb.cells.insert(2, nb.cells.pop(header_index))
            modified = True
    else:
        new_cell = nbformat.v4.new_code_cell(HEADER)
        nb.cells.insert(2, new_cell)
        modified = True
    if modified:
        nbformat.write(nb, notebook_path)
    return modified


def print_hook_summary(reformatted_files, unchanged_files):
    """Print a Black-style summary."""
    for f in reformatted_files:
        print(f"\nreformatted {f}")

    total_ref = len(reformatted_files)
    total_unchanged = len(unchanged_files)
    if total_ref > 0:
        print("\nAll done! ✨ 🍰 ✨")
        print(
            f"{total_ref} file{'s' if total_ref != 1 else ''} reformatted, "
            f"{total_unchanged} file{'s' if total_unchanged != 1 else ''} left unchanged."
        )


def _preview_badge_markdown(absolute_path):
    svg_badge_url = (
        "https://img.shields.io/static/v1?"
        + "label=render%20on&logo=github&color=87ce3e&message=GitHub"
    )
    link = (
        f"https://github.com/open-atmos/{repo_path().name}/blob/main/"
        + f"{relative_path(absolute_path)}"
    )
    return f"[![preview notebook]({svg_badge_url})]({link})"


def _mybinder_badge_markdown(absolute_path):
    svg_badge_url = "https://mybinder.org/badge_logo.svg"
    link = (
        f"https://mybinder.org/v2/gh/open-atmos/{repo_path().name}.git/main?urlpath=lab/tree/"
        + f"{relative_path(absolute_path)}"
    )
    return f"[![launch on mybinder.org]({svg_badge_url})]({link})"


def _colab_badge_markdown(absolute_path):
    svg_badge_url = "https://colab.research.google.com/assets/colab-badge.svg"
    link = (
        f"https://colab.research.google.com/github/open-atmos/{repo_path().name}/blob/main/"
        + f"{relative_path(absolute_path)}"
    )
    return f"[![launch on Colab]({svg_badge_url})]({link})"


def test_notebook_has_at_least_three_cells(notebook_filename):
    """checks if all notebooks have at least three cells"""
    with open(notebook_filename, encoding="utf8") as fp:
        nb = nbformat.read(fp, nbformat.NO_CONVERT)
        if len(nb.cells) < 3:
            raise ValueError("Notebook should have at least 4 cells")


def test_first_cell_contains_three_badges(notebook_filename):
    """checks if all notebooks feature three badges in the first cell"""
    with open(notebook_filename, encoding="utf8") as fp:
        nb = nbformat.read(fp, nbformat.NO_CONVERT)
    if nb.cells[0].cell_type != "markdown":
        raise ValueError("First cell is not a markdown cell")
    lines = nb.cells[0].source.split("\n")
    if len(lines) != 3:
        raise ValueError("First cell does not contain exactly 3 lines (badges)")
    if lines[0] != _preview_badge_markdown(notebook_filename):
        raise ValueError(
            f"First badge does not match Github preview badge {_preview_badge_markdown(notebook_filename)}, {notebook_filename}"
        )
    if lines[1] != _mybinder_badge_markdown(notebook_filename):
        raise ValueError("Second badge does not match MyBinder badge")
    if lines[2] != _colab_badge_markdown(notebook_filename):
        raise ValueError("Third badge does not match Colab badge")


def test_second_cell_is_a_markdown_cell(notebook_filename):
    """checks if all notebooks have their second cell with some markdown
    (hopefully clarifying what the example is about)"""
    with open(notebook_filename, encoding="utf8") as fp:
        nb = nbformat.read(fp, nbformat.NO_CONVERT)
    if nb.cells[1].cell_type != "markdown":
        raise ValueError("Second cell is not a markdown cell")


def main(argv: Sequence[str] | None = None) -> int:
    """collect failed notebook checks"""
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    args = parser.parse_args(argv)

    failed_files = False
    reformatted_files = []
    unchanged_files = []
    for filename in args.filenames:
        try:
            modified = fix_colab_header(filename)
            if modified:
                reformatted_files.append(str(filename))
            else:
                unchanged_files.append(str(filename))
        except ValueError as exc:
            print(f"[ERROR] {filename}: {exc}")
            failed_files = True
        try:
            test_notebook_has_at_least_three_cells(filename)
            test_first_cell_contains_three_badges(filename)
            test_second_cell_is_a_markdown_cell(filename)

        except ValueError as exc:
            print(f"[ERROR] {filename}: {exc}")
            failed_files = True

    print_hook_summary(reformatted_files, unchanged_files)
    return 1 if (reformatted_files or failed_files) else 0


if __name__ == "__main__":
    raise SystemExit(main())
