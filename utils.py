"""
Utils functions to reuse in different parts of the codebase
"""

import os

from git.cmd import Git


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
