from abc import ABC
from enum import Enum
from textwrap import indent

from ..verbosity import ModelVerbosity


class ModelType(Enum):
    """
    abbreviated model type within a NEMS / NUOPC configuration file
    """

    ATMOSPHERIC = 'ATM'
    WAVES = 'WAV'
    OCEAN = 'OCN'
    HYDROLOGICAL = 'HYD'


class ModelEntry(ABC):
    """
    abstract implementation of a generic model
    """

    def __init__(self, name: str, model_type: ModelType, processors: int,
                 verbosity: ModelVerbosity = None):
        self.name = name
        self.type = model_type
        self.processors = processors
        self.verbosity = (verbosity if verbosity is not None
                          else ModelVerbosity.MINIMUM)

        self.__start_processor = 0

        self.previous = None
        self.next = None

        self.header = str(self.type.value)

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
    def previous(self, previous: 'ModelEntry'):
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
    def next(self, next: 'ModelEntry'):
        self.__next = next
        if self.next is not None:
            self.next.previous = self

    def __str__(self) -> str:
        return '\n'.join([
            f'{self.header}_model:                      {self.name}',
            f'{self.header}_petlist_bounds:             {self.start_processor} {self.end_processor}',
            f'{self.header}_attributes::',
            indent(f'Verbosity = {self.verbosity.value}', '  '),
            '::'
        ])
