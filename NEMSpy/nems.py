from datetime import timedelta
from enum import Enum
from textwrap import indent

from NEMSpy.model import Model, ModelType


class ModelRelationMethod(Enum):
    REDISTRIBUTE = 'redist'


class ModelConnector:
    def __init__(
            self, source: ModelType, destination: ModelType,
            method: ModelRelationMethod = ModelRelationMethod.REDISTRIBUTE):
        self.source = source
        self.destination = destination
        self.method = method


class ModelSequence:
    def __init__(self, duration: timedelta, indent: str = '  '):
        self.duration = duration
        self.indent = indent
        self.connectors = []

    def __str__(self) -> str:
        lines = []
        for conn in self.connectors:
            lines += f'{conn.source} -> {conn.destination}    :remapMethod={conn.method}'
        for model_type in self.models:
            lines += f'{model_type}'
        block = '\n'.join(lines)
        block = [f'@{self.duration / timedelta(seconds=1)}',
                 indent(block, self.indent), '@']
        block = '\n'.join(block)
        block = [f'runSeq::', indent(block, self.indent), '::']
        return '\n'.join(block)

    def add_model_connector(
            self, source: ModelType, destination: ModelType,
            method: ModelRelationMethod = ModelRelationMethod.REDISTRIBUTE
            ):
        self.connectors.append(ModelConnector(source, destination, method))


class NEMS:

    def __init__(self, models: [ModelType]):
        self.models = models
        self.sequences = []

    def __getitem__(self, model_type: ModelType) -> Model:
        return self.__models[model_type]

    def __setitem__(self, model_type: ModelType, model: Model):
        assert model_type == model.model_type
        self.__models[model_type] = model

    def add_model_sequence(self, duration: timedelta) -> ModelSequence:
        self.sequences.append(seq := ModelSequence(duration))
        return seq

    def write(self):
        raise NotImplementedError

    @property
    def models(self) -> {ModelType: Model}:
        return {model_type: model
                for model_type, model in self.__models.items()
                if model is not None}

    @models.setter
    def models(self, models):
        self.__models = {model_type: None for model_type in ModelType}
