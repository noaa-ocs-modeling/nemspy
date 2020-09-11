from abc import ABC
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


class Model(ABC):
    """
    abstract implementation of a generic model
    """

    def __init__(self, name: str, model_type: ModelType, processors: int,
                 verbosity: ModelVerbosity = None, previous: 'Model' = None):
        self.name = name
        self.type = model_type

        self.__start_processor = None
        self.__end_processor = None
        self.__processors = processors

        self.next = None
        self.previous = previous

        self.verbosity = verbosity if verbosity is not None else ModelVerbosity.MINIMUM

    @property
    def processors(self):
        return self.__processors

    @processors.setter
    def processors(self, processes: int):
        self.__processors = processes
        self.__end_processor = self.__start_processor + self.__processors - 1

    @property
    def start_processor(self) -> int:
        return self.__start_processor

    @property
    def end_processor(self) -> int:
        return self.__end_processor

    @property
    def previous(self):
        return self.__previous

    @previous.setter
    def previous(self, previous: 'Model'):
        self.__previous = previous
        if self.__previous is not None:
            self.__previous.__next = self
            self.__start_processor = self.__previous.end_processor + 1
            self.processors = self.__processors
            current_model = self.next
            while current_model is not None:
                current_model.__start_processor = current_model.__previous.end_processor + 1
                current_model = current_model.next
        else:
            self.__start_processor = 0
            self.__end_processor = self.__start_processor + self.processors - 1

    @property
    def next(self):
        return self.__next

    @next.setter
    def next(self, next: 'Model'):
        self.__next = next
        if self.__next is not None:
            self.__next.previous = self

    def __str__(self) -> str:
        return '\n'.join([
            f'{self.type}_model:                      {self.name}'
            f'{self.type}_petlist_bounds:             {self.start_processor} {self.end_processor}',
            f'{self.type}_attributes::',
            indent(f'Verbosity = {self.verbosity}', INDENTATION),
            '::'
        ])


class Earth:
    """
    multi-model coupling container
    """

    def __init__(self, verbosity: ModelVerbosity = None, **kwargs):
        self.type = 'EARTH'
        self.verbosity = verbosity if verbosity is None else ModelVerbosity.MINIMUM

        self.__models = {}
        for key, value in kwargs.items():
            if key in {entry.name for entry in ModelType}:
                self[key] = value

    @property
    def models(self):
        return {model_type: model
                for model_type, model in self.__models.items()
                if model is not None}

    def __getitem__(self, model_type: ModelType) -> Model:
        return self.__models[model_type]

    def __setitem__(self, model_type: ModelType, model: Model):
        assert model_type == model.type
        self.__models[model_type] = model

    def __str__(self) -> str:
        return '\n'.join([
            f'{self.type}_component_list: {" ".join(self.models)}'
            f'{self.type}_attributes::',
            indent(f'Verbosity = {self.verbosity}', INDENTATION),
            '::'
        ])
