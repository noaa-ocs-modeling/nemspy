# from abc import ABC, abstractmethod
from datetime import timedelta
from enum import Enum
from functools import lru_cache
from textwrap import indent
from typing import List, Dict, Generator

from .model.base import ModelEntry, ModelType

INDENTATION = '  '


class ModelMediation(Enum):
    REDISTRIBUTE = 'redist'


class ModelMediator:
    def __init__(self, source: ModelEntry, destination: ModelEntry,
                 method: ModelMediation):
        self.source = source
        self.destination = destination
        self.method = method if method is not None else ModelMediation.REDISTRIBUTE

    def __str__(self) -> str:
        return f'{self.source.type.value} -> ' \
               f'{self.destination.type.value}'.ljust(13) + \
               f':remapMethod={self.method.value}'


class ModelSequence:
    header = 'Run Sequence'

    def __init__(self, duration: timedelta, **kwargs):
        self.duration = duration

        self.__models: Dict[ModelType, ModelEntry] = {}
        for key, value in kwargs.items():
            if key.upper() in {entry.name for entry in ModelType} and \
                    isinstance(value, ModelEntry):
                self[ModelType[key.upper()]] = value

        # set start and end processors
        models = list(self.models.values())
        for model_index, model in enumerate(models):
            next_model_index = model_index + 1
            if next_model_index < len(models):
                model.next = models[next_model_index]

        self.connections: List[ModelMediator] = []

    def __getitem__(self, model_type: ModelType) -> ModelEntry:
        return self.__models[model_type]

    def __setitem__(self, model_type: ModelType, model: ModelEntry):
        assert model_type == model.type
        # if model_type in self.__models:
        #     LOGGER.warning(f'overwriting existing "{model_type.name}" model')
        self.__models[model_type] = model

    def __contains__(self, model_type: ModelType):
        return model_type in self.__models

    def __iter__(self) -> Generator:
        for model in self.models:
            yield model

    def __str__(self) -> str:
        if len(self.models) == 0:
            return ''
        lines: List[str] = []
        if len(self.models) > 1:
            for model in self.models:
                lines.extend(str(connection)
                             for connection in model.connections)
            lines.extend(model_type.value for model_type in self.models)
            block = '\n'.join(lines)
        else:
            lines.append(self.models[0].value)
        block = '\n'.join([
            f'@{self.duration.total_seconds():.0f}',
            indent(block, INDENTATION),
            '@'
        ])
        return '\n'.join([
            f"\n# {self.header} #",
            'runSeq::',
            indent(block, INDENTATION), '::']
            )

    def __repr__(self) -> str:
        models = [f'{model.type.name}={repr(model)}' for model in self.models]
        return f'{self.__class__.__name__}({repr(self.duration)}, {", ".join(models)})'

    def connect(self, source: ModelEntry, destination: ModelEntry,
                method: ModelMediation = ModelMediation.REDISTRIBUTE):
        method = ModelMediation.REDISTRIBUTE if method is None else method
        self.connections.append(ModelMediator(source, destination, method))

    @property
    def models(self) -> List[ModelEntry]:
        return [self[model_type] for model_type in self.__models]


# class NEMSConfiguration:
#     header = '#############################################\n' \
#              '####  NEMS Run-Time Configuration File  #####\n' \
#              '#############################################'

#     def __init__(self, earth: Earth, verbosity: ModelVerbosity = None):
#         self.verbosity = verbosity if verbosity is not None \
#                          else ModelVerbosity.MAXIMUM


#     def __str__(self) -> str:
#         return f'{self.header}\n' + \
#                '\n' + \
#                f'{str(self.earth)}' + \
#                ''
#                # '\n'.join(f'# {entry.header} #\n' 
#                #           f'{entry}\n'
#                #           for entry in self.entries)

#     def write(self, filename: str):
#         with open(filename, 'w') as output_file:
#             output_file.write(str(self))

#     @property
#     def earth(self) -> Earth:
#         return Earth(self.verbosity,
#                      **{model.type.name: model for model in self.models})

#     @property
#     def models(self):
#         models = {}
#         for sequence in self.model_sequences:
#             print(sequence)
#             exit()
#             # models.update({})
#         exit()

#     @property
#     def verbosity(self):
#         return self.__verbosity

#     @verbosity.setter
#     def verbosity(self, verbosity: ModelVerbosity):
#         self.__verbosity = verbosity


    
