from abc import ABC, abstractmethod
from enum import Enum
from textwrap import indent

from .. import get_logger

LOGGER = get_logger('model')

INDENTATION = '  '


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


class ModelMediation(Enum):
    REDISTRIBUTE = 'redist'


class ModelMediator:
    def __init__(self, source: 'Model', destination: 'Model',
                 method: ModelMediation):
        self.source = source
        self.destination = destination
        self.method = method if method is not None else ModelMediation.REDISTRIBUTE

    def __str__(self) -> str:
        return f'{self.source.type.value} -> ' \
               f'{self.destination.type.value}'.ljust(13) + \
               f':remapMethod={self.method.value}'


class ConfigurationEntry(ABC):
    """
    NEMS / NUOPC configuration entry within `*.configure` file
    """

    header: str = NotImplementedError

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError


class Model(ConfigurationEntry):
    """
    abstract implementation of a generic model
    """

    def __init__(self, name: str, model_type: ModelType, processors: int,
                 verbosity: ModelVerbosity = None):
        self.name = name
        self.type = model_type
        self.processors = processors
        self.verbosity = verbosity if verbosity is not None else ModelVerbosity.MINIMUM

        self.__start_processor = None

        self.previous = None
        self.next = None

        self.connections = []

        self.header = str(self.type.value)

    def connect(self, other: 'Model', method: ModelMediation = None):
        self.connections.append(ModelMediator(self, other, method))

    @property
    def processors(self):
        return self.__processors

    @processors.setter
    def processors(self, processes: int):
        self.__processors = processes

    @property
    def start_processor(self) -> int:
        return self.__start_processor

    @property
    def end_processor(self) -> int:
        return self.start_processor + self.processors - 1

    @property
    def previous(self):
        return self.__previous

    @previous.setter
    def previous(self, previous: 'Model'):
        self.__previous = previous
        if self.previous is not None:
            self.previous.__next = self
            self.__start_processor = self.previous.end_processor + 1
            current_model = self.next
            while current_model is not None:
                current_model.__start_processor = current_model.previous.end_processor + 1
                current_model = current_model.next
        else:
            self.__start_processor = 0

    @property
    def next(self):
        return self.__next

    @next.setter
    def next(self, next: 'Model'):
        self.__next = next
        if self.next is not None:
            self.next.previous = self

    def __str__(self) -> str:
        return '\n'.join([
            f'{self.header}_model:                      {self.name}',
            f'{self.header}_petlist_bounds:             {self.start_processor} {self.end_processor}',
            f'{self.header}_attributes::',
            indent(f'Verbosity = {self.verbosity.value}', INDENTATION),
            '::'
        ])

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.name}", {self.type}, {self.processors}, {self.verbosity})'
