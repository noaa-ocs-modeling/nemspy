from abc import ABC
from enum import Enum
from textwrap import indent


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

    def __init__(self, name: str, model_type: ModelType, processes: int,
                 verbosity: ModelVerbosity, indent_str: str = '  ',
                 previous: 'Model' = None):
        self.name = name
        self.type = model_type

        self.__processes = processes
        self.__start_process = None
        self.__end_process = None

        self.previous = previous
        self.next = None

        self.verbosity = verbosity
        self.indent = indent_str

    @property
    def processes(self):
        return self.__processes

    @processes.setter
    def processes(self, processes: int):
        self.__processes = processes
        self.__end_process = self.__start_process + self.__processes - 1

    @property
    def start_process(self) -> int:
        return self.__start_process

    @property
    def end_process(self) -> int:
        return self.__end_process

    @property
    def previous(self):
        return self.__previous

    @previous.setter
    def previous(self, previous: 'Model'):
        self.__previous = previous
        if self.__previous is not None:
            self.__previous.__next = self
            self.__start_process = self.__previous.end_process + 1
            self.processes = self.__processes
            current = self.next
            while current is not None:
                current.__start_process = current.__previous.end_process + 1
                current = current.next
        else:
            self.__start_process = 0

    @property
    def next(self):
        return self.__previous

    @next.setter
    def next(self, next: 'Model'):
        self.__next = next
        if self.__next is not None:
            self.__next.previous = self

    def __str__(self) -> str:
        return '\n'.join([
            f'{self.type}_model:                      {self.name}'
            f'{self.type}_petlist_bounds:             {self.start_process} {self.end_process}',
            f'{self.type}_attributes::',
            indent(f'Verbosity = {self.verbosity}', self.indent),
            '::'
        ])


class Earth:
    """
    multi-model coupling container
    """

    def __init__(self, verbosity: ModelVerbosity, models: [Model] = None,
                 indent: str = '  '):
        self.verbosity = verbosity

        self.__models = {}
        if models is not None:
            for model in models:
                self.add(model)

        self.indent_str = indent
        self.type = 'EARTH'

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

    def add(self, model: Model):
        self[model.type] = model

    def __str__(self) -> str:
        return '\n'.join([
            f'{self.type}_component_list: {" ".join(self.models)}'
            f'{self.type}_attributes::',
            indent(f'Verbosity = {self.verbosity}', self.indent_str),
            '::'
        ])
