import dunamai

from .interface import ModelingSystem
from .model import Model

__version__ = dunamai.get_version('nemspy',
                                  third_choice=dunamai.Version.from_any_vcs).serialize()
