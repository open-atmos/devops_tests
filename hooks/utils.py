"""
Utils functions to reuse in different parts of the codebase
"""

import os
import pathlib

from git import Git


def find_files(path_to_folder_from_project_root=".", file_extension=None):
    """
    Returns all files in a current git repo.
    The list of returned files may be filtered with `file_extension` param.
    """
    all_files = [
        path
        for path in Git(
            Git(path_to_folder_from_project_root).rev_parse("--show-toplevel")
        )
        .ls_files()
        .split("\n")
        if os.path.isfile(path)
    ]
    if file_extension is not None:
        return list(filter(lambda path: path.endswith(file_extension), all_files))

    return all_files


def relative_path(absolute_path):
    """returns a path relative to the repo base (converting backslashes to slashes on Windows)"""
    relpath = os.path.relpath(absolute_path, original_repo_path().absolute())
    posixpath_to_make_it_usable_in_urls_even_on_windows = pathlib.Path(
        relpath
    ).as_posix()
    return posixpath_to_make_it_usable_in_urls_even_on_windows


def original_repo_path() -> pathlib.Path:
    """Path to the original (non-temp) repository root during pre-commit."""
    root = os.environ.get("PRE_COMMIT_REPOROOT")
    print(root)
    if root:
        return pathlib.Path(root).resolve()

    # Fallback for normal execution (not in pre-commit)
    from git import Repo

    repo = Repo(__file__, search_parent_directories=True)
    return pathlib.Path(repo.git.rev_parse("--show-toplevel"))


def original_repo_name() -> str:
    return original_repo_path().name
