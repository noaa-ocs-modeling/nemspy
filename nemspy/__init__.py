from dunamai import Version, get_version

from .interface import ModelingSystem

__version__ = get_version('nemspy', third_choice=Version.from_git).serialize()
