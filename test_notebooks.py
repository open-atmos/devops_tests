"""executes all Jupyter notebooks tracked by git"""

# pylint: disable=wrong-import-position
# https://bugs.python.org/issue37373
import sys

if sys.platform == "win32" and sys.version_info[:2] >= (3, 7):
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import gc
import os
import pathlib
import warnings

import nbformat
import pint
import pytest
from git.cmd import Git

from .utils import find_files

with warnings.catch_warnings():
    warnings.filterwarnings("ignore")
    from nbconvert.preprocessors import ExecutePreprocessor

SI = pint.UnitRegistry()


def _relative_path(absolute_path):
    """returns a path relative to the repo base (converting backslashes to slashes on Windows)"""
    relpath = os.path.relpath(absolute_path, _repo_path().absolute())
    posixpath_to_make_it_usable_in_urls_even_on_windows = pathlib.Path(
        relpath
    ).as_posix()
    return posixpath_to_make_it_usable_in_urls_even_on_windows


def _repo_path():
    """returns absolute path to the repo base (ignoring .git location if in a submodule)"""
    path = pathlib.Path(__file__)
    while not (path.is_dir() and Git(path).rev_parse("--git-dir") == ".git"):
        path = path.parent
    return path


COLAB_HEADER = f"""import sys
if 'google.colab' in sys.modules:
    !pip --quiet install open-atmos-jupyter-utils
    from open_atmos_jupyter_utils import pip_install_on_colab
    pip_install_on_colab('{_repo_path().name}-examples')"""


@pytest.fixture(
    params=find_files(file_extension=".ipynb"),
    name="notebook_filename",
)
def _notebook_filename(request):
    return request.param


def test_run_notebooks(notebook_filename, tmp_path):
    """executes a given notebook"""
    os.environ["JUPYTER_PLATFORM_DIRS"] = "1"

    executor = ExecutePreprocessor(timeout=15 * 60, kernel_name="python3")

    with open(notebook_filename, encoding="utf8") as notebook_file:
        # https://github.com/pytest-dev/pytest-asyncio/issues/212
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="There is no current event loop")
            executor.preprocess(
                nbformat.read(notebook_file, as_version=4),
                {"metadata": {"path": tmp_path}},
            )

    # so that nbconvert perplexities are reported here, and not at some dtor test later on
    gc.collect()


def test_file_size(notebook_filename):
    """checks if all example Jupyter notebooks have file size less than an arbitrary limit"""
    assert os.stat(notebook_filename).st_size * SI.byte < 2 * SI.megabyte


def test_no_errors_or_warnings_in_output(notebook_filename):
    """checks if all example Jupyter notebooks have clear std-err output
    (i.e., no errors or warnings) visible; with exception of acceptable
    diagnostics from the joblib package"""
    with open(notebook_filename, encoding="utf8") as notebook_file:
        notebook = nbformat.read(notebook_file, nbformat.NO_CONVERT)
        for cell in notebook.cells:
            if cell.cell_type == "code":
                for output in cell.outputs:
                    if "name" in output and output["name"] == "stderr":
                        if not output["text"].startswith("[Parallel(n_jobs="):
                            raise AssertionError(output["text"])


def test_jetbrains_bug_py_66491(notebook_filename):
    """checks if all notebooks have the execution_count key for each cell in JSON what is
    required by GitHub renderer and what happens not to be the case if generating the notebook
    using buggy versions of PyCharm: https://youtrack.jetbrains.com/issue/PY-66491"""
    with open(notebook_filename, encoding="utf8") as notebook_file:
        notebook = nbformat.read(notebook_file, nbformat.NO_CONVERT)
        for cell in notebook.cells:
            if cell.cell_type == "code" and not hasattr(cell, "execution_count"):
                raise AssertionError(
                    "notebook cell is missing the execution_count attribute"
                    + " (could be due to a bug in PyCharm,"
                    + " see https://youtrack.jetbrains.com/issue/PY-66491 )"
                )


def _preview_badge_markdown(absolute_path):
    svg_badge_url = (
        "https://img.shields.io/static/v1?"
        + "label=render%20on&logo=github&color=87ce3e&message=GitHub"
    )
    link = (
        f"https://github.com/open-atmos/{_repo_path().name}/blob/main/"
        + f"{_relative_path(absolute_path)}"
    )
    return f"[![preview notebook]({svg_badge_url})]({link})"


def _mybinder_badge_markdown(abslute_path):
    svg_badge_url = "https://mybinder.org/badge_logo.svg"
    link = (
        f"https://mybinder.org/v2/gh/open-atmos/{_repo_path().name}.git/main?urlpath=lab/tree/"
        + f"{_relative_path(abslute_path)}"
    )
    return f"[![launch on mybinder.org]({svg_badge_url})]({link})"


def _colab_badge_markdown(absolute_path):
    svg_badge_url = "https://colab.research.google.com/assets/colab-badge.svg"
    link = (
        f"https://colab.research.google.com/github/open-atmos/{_repo_path().name}/blob/main/"
        + f"{_relative_path(absolute_path)}"
    )
    return f"[![launch on Colab]({svg_badge_url})]({link})"


def test_first_cell_contains_three_badges(notebook_filename):
    """checks if all notebooks feature Github preview, mybinder and Colab badges
    (in the first cell)"""
    with open(notebook_filename, encoding="utf8") as fp:
        nb = nbformat.read(fp, nbformat.NO_CONVERT)
        assert len(nb.cells) > 0
        assert nb.cells[0].cell_type == "markdown"
        lines = nb.cells[0].source.split("\n")
        assert len(lines) == 3
        assert lines[0] == _preview_badge_markdown(notebook_filename)
        assert lines[1] == _mybinder_badge_markdown(notebook_filename)
        assert lines[2] == _colab_badge_markdown(notebook_filename)


def test_second_cell_is_a_markdown_cell(notebook_filename):
    """checks if all notebooks have their second cell with some markdown
    (hopefully clarifying what the example is about)"""
    with open(notebook_filename, encoding="utf8") as fp:
        nb = nbformat.read(fp, nbformat.NO_CONVERT)
        assert len(nb.cells) > 1
        assert nb.cells[1].cell_type == "markdown"


def test_third_cell_contains_colab_header(notebook_filename):
    """checks if all notebooks feature a Colab-magic cell"""
    with open(notebook_filename, encoding="utf8") as fp:
        nb = nbformat.read(fp, nbformat.NO_CONVERT)
        assert len(nb.cells) > 2
        assert nb.cells[2].cell_type == "code"
        assert nb.cells[2].source == COLAB_HEADER


def test_cell_contains_output(notebook_filename):
    """checks if all notebook cells have an output present"""
    with open(notebook_filename, encoding="utf8") as fp:
        nb = nbformat.read(fp, nbformat.NO_CONVERT)
        for cell in nb.cells:
            if cell.cell_type == "code" and cell.source != "":
                assert cell.execution_count is not None


def test_show_plot_used_instead_of_matplotlib(notebook_filename):
    """checks if plotting is done with open_atmos_jupyter_utils show_plot()"""
    with open(notebook_filename, encoding="utf8") as fp:
        nb = nbformat.read(fp, nbformat.NO_CONVERT)
        for cell in nb.cells:
            if cell.cell_type != "code":
                continue
            if cell.outputs[0].data.starts_with("image/"):
                assert (
                    cell.source[-1].starts_with("show_plot"),
                    "if using matplotlib, please use open_atmos_jupyter_utils.show_plot()",
                )


def test_show_anim_used_instead_of_matplotlib(notebook_filename):
    """checks if animation generation is done with open_atmos_jupyter_utils show_anim()"""
    with open(notebook_filename, encoding="utf8") as fp:
        nb = nbformat.read(fp, nbformat.NO_CONVERT)
        matplot_used = False
        show_anim_used = False
        for cell in nb.cells:
            if cell.cell_type == "code":
                if (
                    "funcAnimation" in cell.source
                    or "matplotlib.animation" in cell.source
                    or "from matplotlib import animation" in cell.source
                ):
                    matplot_used = True
                if "show_anim(" in cell.source:
                    show_anim_used = True
        if matplot_used and not show_anim_used:
            raise AssertionError(
                """if using matplotlib for animations,
                please use open_atmos_jupyter_utils.show_anim()"""
            )
