import pathlib
from typing import Union

from .interface import NEMS
from ._version import get_versions

__version__ = get_versions()['version']
del get_versions
