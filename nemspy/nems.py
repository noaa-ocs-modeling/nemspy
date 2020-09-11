from datetime import timedelta
from enum import Enum
from textwrap import indent

from pandas import DataFrame

from nemspy.model import Earth, Model, ModelType


class ModelRelationMethod(Enum):
    REDISTRIBUTE = 'redist'


class ModelSequence:
    def __init__(self, duration: timedelta = None, indent_str: str = '  '):
        self.duration = duration if duration is not None else \
            timedelta(hours=1)
        self.indent = indent_str
        self.__models = {model_type: None for model_type in ModelType}
        self.relations = DataFrame(columns=['source', 'destination', 'method'])

    @property
    def models(self) -> {ModelType: Model}:
        return {model_type: model
                for model_type, model in self.__models.items()
                if model is not None}

    def __getitem__(self, model_type: ModelType) -> Model:
        return self.__models[model_type]

    def __setitem__(self, model_type: ModelType, model: Model):
        assert model_type == model.type
        self.__models[model_type] = model

    def add_earth(self, earth: Earth):
        for model in earth:
            self[model.type] = model

    def add_relation(self, source: ModelType, destination: ModelType,
                     method: ModelRelationMethod = ModelRelationMethod.REDISTRIBUTE):
        self.relations.loc[len(self.relations)] = [source, destination, method]
        self.relations.sort_values('destination')

    def __str__(self) -> str:
        lines = []
        for relation_index, relation in self.relations.iterrows():
            lines += f'{relation["source"]} -> {relation["destination"]}'.ljust(
                13) + f':remapMethod={relation["method"]}'
        for model_type in self.models:
            lines += f'{model_type}'
        block = '\n'.join(lines)
        block = [f'@{self.duration / timedelta(seconds=1)}',
                 indent(block, self.indent), '@']
        block = '\n'.join(block)
        block = [f'runSeq::', indent(block, self.indent), '::']
        return '\n'.join(block)
