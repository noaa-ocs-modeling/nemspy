from abc import ABC
from enum import Enum


class ModelKey(Enum):
    ATMOSPHERIC = 'ATM'
    OCEAN = 'OCN'
    WAVE = 'WAV'
    HYDROLOGICAL = 'HYD'


class ModelVerbosity(Enum):
    MINIMUM = 'min'
    MAXIMUM = 'max'


class Model(ABC):
    def __init__(self, key: ModelKey, processes: int,
                 verbosity: ModelVerbosity):
        self.key = key
        self.processes = processes
        self.verbosity = verbosity
