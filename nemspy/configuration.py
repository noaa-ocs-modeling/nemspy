from datetime import timedelta
from functools import lru_cache
from os import PathLike
from textwrap import indent
from typing import Iterator, Tuple

from . import get_logger
from .model import ConfigurationEntry, INDENTATION, Model, ModelType, \
    ModelVerbosity

LOGGER = get_logger('configuration')


class Earth(ConfigurationEntry):
    """
    multi-model coupling container
    """

    entry_type = 'EARTH'

    def __init__(self, verbosity: ModelVerbosity = None, **kwargs):
        self.verbosity = verbosity if verbosity is None else ModelVerbosity.MINIMUM
        self.__models = {model_type: None for model_type in ModelType}
        for key, value in kwargs.items():
            key = key.upper()
            if key in {entry.name for entry in ModelType}:
                if isinstance(value, Model):
                    self[ModelType[key]] = value

    @property
    def models(self):
        return self.__models

    def __getitem__(self, model_type: ModelType) -> Model:
        return self.__models[model_type]

    def __setitem__(self, model_type: ModelType, model: Model):
        assert model_type == model.type
        if self.__models[model_type] is not None:
            LOGGER.warning(f'overwriting existing "{model_type.name}" model: '
                           f'{repr(self[model_type])}')
        self.__models[model_type] = model

    def __contains__(self, model_type: ModelType):
        return model_type in self.__models

    def __iter__(self) -> Iterator[Tuple[ModelType, Model]]:
        for model_type, model in self.models.items():
            yield model_type, model

    def __str__(self) -> str:
        return '\n'.join([
            f'{self.entry_type}_component_list: {" ".join(model_type.value for model_type in self.models)}',
            f'{self.entry_type}_attributes::',
            indent(f'Verbosity = {self.verbosity.value}', INDENTATION),
            '::'
        ])

    def __repr__(self) -> str:
        models = [f'{model_type.name}={repr(model)}'
                  for model_type, model in self.models.items()]
        return f'{self.__class__.__name__}({self.verbosity}, {", ".join(models)})'


class ModelSequence(ConfigurationEntry):
    entry_type = 'Run Sequence'

    def __init__(self, duration: timedelta, **kwargs):
        self.duration = duration

        self.__models: {ModelType: Model} = {}
        for key, value in kwargs.items():
            key = key.upper()
            if key in {entry.name for entry in ModelType} and \
                    isinstance(value, Model):
                self[ModelType[key]] = value
            elif key == 'EARTH' and isinstance(value, Earth):
                for model_type, model in value:
                    self[model_type] = model

        # set start and end processors
        for model_index, model in enumerate(self):
            next_model_index = model_index + 1
            if next_model_index < len(self):
                model.next = self.models[next_model_index]

    @property
    @lru_cache(maxsize=1)
    def models(self) -> [Model]:
        return [self[model_type] for model_type in self.__models
                if model_type in self]

    @property
    def earth(self) -> Earth:
        return Earth(ModelVerbosity.MAXIMUM, **{model.type.name: model
                                                for model in self.models})

    def __getitem__(self, model_type: ModelType) -> Model:
        return self.__models[model_type]

    def __setitem__(self, model_type: ModelType, model: Model):
        assert model_type == model.type
        if model_type in self.__models:
            LOGGER.warning(f'overwriting existing "{model_type.name}" model')
        self.__models[model_type] = model

    def __contains__(self, model_type: ModelType):
        return model_type in self.__models

    def __iter__(self) -> Iterator[Model]:
        for model in self.models:
            yield model

    def __len__(self) -> int:
        return len(self.models)

    def __str__(self) -> str:
        lines = []
        for model in self.models:
            lines.extend(str(connection) for connection in model.connections)
        lines.extend(model_type.value for model_type in self.__models)
        block = '\n'.join(lines)
        block = '\n'.join([
            f'@{self.duration / timedelta(seconds=1):.0f}',
            indent(block, INDENTATION),
            '@'
        ])
        return '\n'.join([
            f'runSeq::',
            indent(block, INDENTATION),
            '::'
        ])

    def __repr__(self) -> str:
        models = [f'{model.type.name}={repr(model)}' for model in self.models]
        return f'{self.__class__.__name__}({repr(self.duration)}, {", ".join(models)})'


class NEMSConfiguration:
    def __init__(self, model_sequence: ModelSequence):
        self.model_sequence = model_sequence

    def write(self, filename: PathLike):
        with open(filename, 'w') as output_file:
            output_file.write(str(self))

    @property
    @lru_cache(maxsize=1)
    def entries(self) -> [ConfigurationEntry]:
        return [self.model_sequence.earth, *self.model_sequence.models,
                self.model_sequence]

    def __iter__(self) -> Iterator[ConfigurationEntry]:
        for entry in self.entries:
            yield entry

    def __getitem__(self, entry_type: type) -> [ConfigurationEntry]:
        return [entry for entry in self.entries
                if isinstance(entry, entry_type)]

    def __str__(self) -> str:
        return '#############################################\n' \
               '####  NEMS Run-Time Configuration File  #####\n' \
               '#############################################\n' \
               '\n' + \
               '\n'.join(f'# {entry.entry_type} #\n'
                         f'{entry}\n'
                         for entry in self.entries)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.model_sequence)})'
