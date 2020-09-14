from enum import Enum


class ModelVerbosity(Enum):
    """
    verbosity attribute within a NEMS / NUOPC configuration file
    """
    MINIMUM = 'min'
    MAXIMUM = 'max'
