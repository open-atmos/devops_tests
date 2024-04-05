""" executes all Jupyter notebooks tracked by git """

# pylint: disable=wrong-import-position
# https://bugs.python.org/issue37373
import sys

if sys.platform == "win32" and sys.version_info[:2] >= (3, 7):
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import gc
import os
import warnings

import nbformat
import pint
import pytest

from .utils import find_files

with warnings.catch_warnings():
    warnings.filterwarnings("ignore")
    from nbconvert.preprocessors import ExecutePreprocessor

SI = pint.UnitRegistry()


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
    (i.e., no errors or warnings) visible"""
    with open(notebook_filename, encoding="utf8") as notebook_file:
        notebook = nbformat.read(notebook_file, nbformat.NO_CONVERT)
        for cell in notebook.cells:
            if cell.cell_type == "code":
                for output in cell.outputs:
                    if "name" in output and output["name"] == "stderr":
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
