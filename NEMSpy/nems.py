from datetime import timedelta
from enum import Enum
from textwrap import indent

from NEMSpy.model import Model, ModelType


class ModelRelationMethod(Enum):
    REDISTRIBUTE = 'redist'


class ModelSequence:
    def __init__(self, duration: timedelta = None, indent: str = '  '):
        self.duration = duration if duration is not None else \
            timedelta(hours=1)
        self.indent = indent
        self.relations = {model_type: {} for model_type in ModelType}

    def __getitem__(self, model_type: ModelType) -> Model:
        return self.__models[model_type]

    def __setitem__(self, model_type: ModelType, model: Model):
        assert model_type == model.model_type
        self.__models[model_type] = model

    def __str__(self) -> str:
        lines = []
        for source, source_relations in self.relations.items():
            for destination, method in source_relations.items():
                lines += f'{source} -> {destination}   :remapMethod={method}'
        for model_type in self.models:
            lines += f'{model_type}'
        block = '\n'.join(lines)
        block = [f'@{self.duration / timedelta(seconds=1)}',
                 indent(block, self.indent), '@']
        block = '\n'.join(block)
        block = [f'runSeq::', indent(block, self.indent), '::']
        return '\n'.join(block)


class NEMS:

    def __init__(self, models: [ModelType]):
        self.models = models

    @property
    def models(self) -> {ModelType: Model}:
        return {model_type: model
                for model_type, model in self.__models.items()
                if model is not None}

    @models.setter
    def models(self, models):
        self.__models = {model_type: None for model_type in ModelType}
