from datetime import timedelta
from functools import lru_cache
from textwrap import indent

# from pandas import DataFrame

from . import get_logger
from .model import ConfigurationEntry, Earth, Model, ModelType, \
    ModelVerbosity, ModelMediation, ModelMediator

LOGGER = get_logger('configuration')

INDENTATION = '  '


class ModelSequence(ConfigurationEntry):
    header = 'Run Sequence'

    def __init__(self, duration: timedelta, **kwargs):
        self.duration = duration

        self.__models = {}
        for key, value in kwargs.items():
            if key in {entry.name for entry in ModelType} and \
                    isinstance(value, Model):
                self[ModelType[key]] = value
            elif key.upper() == 'EARTH' and isinstance(value, Earth):
                for model_type, model in value:
                    self[model_type] = model

        # set start and end processors
        models = list(self.__models.values())
        for model_index, model in enumerate(models):
            next_model_index = model_index + 1
            if next_model_index < len(models):
                model.next = models[next_model_index]

        self.connections = []

    def connect(self, source: Model, destination: Model,
                method: ModelMediation = None):
        self.connections.append(ModelMediator(source, destination, method))

    @property
    @lru_cache(maxsize=1)
    def models(self) -> {ModelType: Model}:
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

    def __iter__(self) -> Model:
        for model in self.models:
            yield model

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
        return '\n'.join(['runSeq::', indent(block, INDENTATION), '::'])

    def __repr__(self) -> str:
        models = [f'{model.type.name}={repr(model)}' for model in self.models]
        return f'{self.__class__.__name__}({repr(self.duration)}, {", ".join(models)})'


class NEMSConfiguration:
    header = '#############################################\n' \
             '####  NEMS Run-Time Configuration File  #####\n' \
             '#############################################'

    def __init__(self, model_sequences: [ModelSequence]):
        self.model_sequences = model_sequences

    # @property
    # def models(self):
    #     return self.model_sequence.models

    def write(self, filename: str):
        with open(filename, 'w') as output_file:
            output_file.write(str(self))

    @property
    @lru_cache(maxsize=1)
    def entries(self) -> [ConfigurationEntry]:
        # TODO: EARTH is not a member of a sequence.
        return [self.model_sequence.earth, *self.models, *self.model_sequences]

    def __iter__(self) -> ConfigurationEntry:
        for entry in self.entries:
            yield entry

    def __str__(self) -> str:
        return f'{self.header}\n' + \
               '\n' + \
               '\n'.join(f'# {entry.header} #\n'
                         f'{entry}\n'
                         for entry in self.entries)

    # def __repr__(self) -> str:
    #     return f'{self.__class__.__name__}({repr(self.model_sequence)})'
