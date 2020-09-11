from datetime import timedelta
from enum import Enum
from textwrap import indent

from pandas import DataFrame

from . import get_logger
from .model import Earth, Model, ModelType

LOGGER = get_logger('configuration')

INDENTATION = '  '


class ModelMediation(Enum):
    REDISTRIBUTE = 'redist'


class ModelSequence:
    def __init__(self, duration: timedelta, **kwargs):
        self.duration = duration

        self.__models = {model_type: None for model_type in ModelType}
        for key, value in kwargs.items():
            if key in ModelType and isinstance(value, Model):
                self[key] = value
            elif key.upper() == 'EARTH' and isinstance(value, Earth):
                for model_type, model in value:
                    self[model_type] = model

        self.connections = DataFrame(columns=['source', 'destination',
                                              'method'])

    @property
    def models(self) -> {ModelType: Model}:
        return {model_type: model
                for model_type, model in self.__models.items()
                if model is not None}

    def __getitem__(self, model_type: ModelType) -> Model:
        return self.__models[model_type]

    def __setitem__(self, model_type: ModelType, model: Model):
        assert model_type == model.type
        if self[model_type] is not None:
            LOGGER
        self.__models[model_type] = model

    def __iter__(self) -> (ModelType, Model):
        for model_type, model in self.__models.items():
            yield model_type, model

    def add_earth(self, earth: Earth):
        for model in earth:
            self[model.type] = model

    def add_connection(self, source: ModelType, destination: ModelType,
                       method: ModelMediation = None):
        if method is None:
            method = ModelMediation.REDISTRIBUTE
        self.connections.loc[len(self.connections)] = [source, destination,
                                                       method]
        self.connections.sort_values('destination', inplace=True)

    def __str__(self) -> str:
        lines = []
        for relation_index, relation in self.connections.iterrows():
            lines += f'{relation["source"]} -> {relation["destination"]}'.ljust(
                13) + f':remapMethod={relation["method"]}'
        # TODO: Order of execution is not well-defined on the current API
        for model_type in self.models:
            lines += f'{model_type}'
        block = '\n'.join(lines)
        block = [f'@{self.duration / timedelta(seconds=1)}',
                 indent(block, INDENTATION), '@']
        block = '\n'.join(block)
        block = [f'runSeq::', indent(block, INDENTATION), '::']
        return '\n'.join(block)
