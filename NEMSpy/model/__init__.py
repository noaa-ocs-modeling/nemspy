from abc import ABC
from enum import Enum


class ModelType(Enum):
    """
    abbreviated model type within a NEMS / NUOPC configuration file
    """
    ATMOSPHERIC = 'ATM'
    WAVE = 'WAV'
    OCEAN = 'OCN'
    HYDROLOGICAL = 'HYD'


class ModelVerbosity(Enum):
    """
    verbosity attribute within a NEMS / NUOPC configuration file
    """

    MINIMUM = 'min'
    MAXIMUM = 'max'


class Model(ABC):
    """
    abstract implementation of a generic model
    """

    def __init__(self, model_type: ModelType, processes: int,
                 verbosity: ModelVerbosity):
        self.model_type = model_type
        self.processes = processes
        self.verbosity = verbosity


class Earth:
    """
    multi-model coupling container
    """

    def __init__(self, verbosity: ModelVerbosity, models: [ModelType]):
        self.verbosity = verbosity
        self.models = models
