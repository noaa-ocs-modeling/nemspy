
import pathlib
from typing import Union

from .interface import NEMS
from ._version import get_versions


def repository_root(path: Union[pathlib.Path, str] = __file__) -> pathlib.Path:
    if path is None:
        path = __file__
    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)
    if path.is_file():
        path = path.parent
    if '.git' in (child.name for child in
                  path.iterdir()) or path == path.parent:
        return path
    else:
        return repository_root(path.parent)


__all__ = ["NEMS"]
__version__ = get_versions()['version']
del get_versions
