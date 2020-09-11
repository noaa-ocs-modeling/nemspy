from datetime import timedelta
from functools import lru_cache
from textwrap import indent

from pandas import DataFrame

from . import get_logger
from .model import ConfigurationEntry, Earth, Model, ModelType

LOGGER = get_logger('configuration')

INDENTATION = '  '


class ModelSequence(ConfigurationEntry):
    header = 'Run Sequence'

    def __init__(self, duration: timedelta, order: [ModelType], **kwargs):
        self.duration = duration
        self.order = order

        self.__models = {}
        for key, value in kwargs.items():
            if key in {entry.name for entry in ModelType} and \
                    isinstance(value, Model):
                self[ModelType[key]] = value
            elif key.upper() == 'EARTH' and isinstance(value, Earth):
                for model_type, model in value:
                    self[model_type] = model

        self.connections = DataFrame(columns=['source', 'destination',
                                              'method'])

    @property
    def models(self) -> {ModelType: Model}:
        return [self[model_type] for model_type in self.order
                if model_type in self]

    def __getitem__(self, model_type: ModelType) -> Model:
        return self.__models[model_type]

    def __setitem__(self, model_type: ModelType, model: Model):
        assert model_type == model.type
        if model_type in self.__models:
            LOGGER.warning(f'overwriting existing "{model_type.name}" model')
        self.__models[model_type] = model

    def __contains__(self, model_type: ModelType):
        return model_type in self.__models

    def __iter__(self) -> Model:
        for model in self.models:
            yield model

    def __str__(self) -> str:
        lines = []
        for model in self.models:
            lines.extend(str(connection) for connection in model.connections)
        lines.extend(model_type.value for model_type in self.order)
        block = '\n'.join(lines)
        block = '\n'.join([
            f'@{self.duration / timedelta(seconds=1):.0f}',
            indent(block, INDENTATION),
            '@'
        ])
        return '\n'.join([f'runSeq::', indent(block, INDENTATION), '::'])

    def __repr__(self) -> str:
        models = [f'{model.type.name}={repr(model)}' for model in self.models]
        return f'{self.__class__.__name__}({repr(self.duration)}, {self.order}, ' \
               f'{", ".join(models)})'


class NEMSConfiguration:
    header = '#############################################\n' \
             '####  NEMS Run-Time Configuration File  #####\n' \
             '#############################################'

    def __init__(self, earth: Earth, model_sequence: ModelSequence):
        self.earth = earth
        self.model_sequence = model_sequence

    def write(self, filename: str):
        with open(filename, 'w') as output_file:
            output_file.write(str(self))

    @property
    @lru_cache(maxsize=1)
    def entries(self) -> [ConfigurationEntry]:
        return [self.earth, *self.earth.models.values(), self.model_sequence]

    def __iter__(self) -> ConfigurationEntry:
        for entry in self.entries:
            yield entry

    def __str__(self) -> str:
        return f'{self.header}\n' + \
               '\n' + \
               '\n'.join(f'# {entry.header} #\n'
                         f'{entry}\n'
                         for entry in self.entries)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.earth)}, {repr(self.model_sequence)})'
