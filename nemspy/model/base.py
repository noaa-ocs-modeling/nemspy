from abc import ABC, abstractmethod
from enum import Enum
from textwrap import indent

from nemspy.utilities import get_logger

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


class RemapMethod(Enum):
    """
    model remapping methods
    """

    REDISTRIBUTE = 'redist'


class Connection:
    def __init__(self, source: ModelType, destination: ModelType,
                 method: RemapMethod):
        self.source = source
        self.destination = destination
        self.method = method if method is not None else RemapMethod.REDISTRIBUTE

    def __str__(self) -> str:
        return f'{self.source.value} -> ' \
               f'{self.destination.value}'.ljust(13) + \
               f':remapMethod={self.method.value}'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.source.name}, {self.destination.name}, {self.method.name})'


class ConfigurationEntry(ABC):
    """
    NEMS / NUOPC configuration entry within `*.configure` file
    """

    entry_type: str = NotImplementedError

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError


class Model(ConfigurationEntry):
    """
    abstract implementation of a generic model
    """

    def __init__(self, name: str, model_type: ModelType, processors: int,
                 verbose: bool = False, **attributes):
        self.name = name
        self.type = model_type
        self.__processors = processors

        self.__start_processor = None

        self.previous = None
        self.next = None

        self.connections = []

        self.entry_type = str(self.type.value)

        self.attributes = {
            'Verbosity': ModelVerbosity.MAXIMUM if verbose else ModelVerbosity.MINIMUM,
            **attributes
        }

    def connect(self, other: 'Model', method: RemapMethod = None):
        self.connections.append(Connection(self, other, method))

    @property
    def processors(self) -> int:
        return self.__processors

    @processors.setter
    def processors(self, processors: int):
        if processors != self.processors:
            self.__processors = processors
            # update following processors
            self.next.previous = self

    @property
    def start_processor(self) -> int:
        return self.__start_processor

    @property
    def end_processor(self) -> int:
        return self.start_processor + self.processors - 1

    @property
    def previous(self) -> 'Model':
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
    def next(self) -> 'Model':
        return self.__next

    @next.setter
    def next(self, next: 'Model'):
        self.__next = next
        if self.next is not None:
            self.next.previous = self

    def __str__(self) -> str:
        return '\n'.join([
            f'{self.entry_type}_model:                      {self.name}',
            f'{self.entry_type}_petlist_bounds:             {self.start_processor} {self.end_processor}',
            f'{self.entry_type}_attributes::',
            indent('\n'.join([
                f'{attribute} = {value if not isinstance(value, Enum) else value.value}'
                for attribute, value in self.attributes.items()
            ]), INDENTATION),
            '::'
        ])

    def __repr__(self) -> str:
        kwargs = [f'{key}={value}'
                  for key, value in self.attributes.items()]
        return f'{self.__class__.__name__}("{self.name}", {self.type}, {self.processors}, {", ".join(kwargs)})'
