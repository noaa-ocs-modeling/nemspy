from datetime import timedelta
from enum import Enum
from textwrap import indent

from .model import Model, ModelType
from .model.ocean import OceanModel
from .model.atmospheric import AtmosphericModel
from .model.wave import WaveModel
from .model.hydrological import HydrologicalModel


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
    def __init__(self, duration: timedelta):
        self.duration = duration
        self.connectors = []

    def __str__(self) -> str:
        lines = []
        for conn in self.connectors:
            lines += f'{conn.source} -> {conn.destination}    :remapMethod={conn.method}'
        # TODO: Order of execution is not well-defined on the current API
        for model_type in self.models:
            lines += f'{model_type}'
        block = '\n'.join(lines)
        block = [f'@{self.duration.total_seconds()}',
                 indent(block, '  '), '@']
        block = '\n'.join(block)
        block = ['runSeq::', indent(block, '  '), '::']
        return '\n'.join(block)

    def define_connector(
            self, source: ModelType, destination: ModelType,
            method: ModelRelationMethod = ModelRelationMethod.REDISTRIBUTE
            ):
        self.connectors.append(ModelConnector(source, destination, method))


class NEMS:

    def __init__(
            self,
            ocean: OceanModel = None,
            wave: WaveModel = None,
            atmospheric: AtmosphericModel = None,
            hydrological: HydrologicalModel = None
    ):
        models = {}

        if ocean is not None:
            assert isinstance(ocean, OceanModel)
            models.update({OceanModel: ocean})

        if wave is not None:
            assert isinstance(wave, WaveModel)
            models.update({WaveModel: wave})

        if atmospheric is not None:
            assert isinstance(atmospheric, AtmosphericModel)
            models.update({AtmosphericModel: atmospheric})

        if hydrological is not None:
            assert isinstance(hydrological, HydrologicalModel)
            models.update({HydrologicalModel: hydrological})

        self.models = models
        self.sequences = []

    def __getitem__(self, model_type: ModelType) -> Model:
        return self.__models[model_type]

    def __setitem__(self, model_type: ModelType, model: Model):
        assert model_type == model.model_type
        self.__models[model_type] = model

    def define_sequence(self, duration: timedelta) -> ModelSequence:
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
        if len(models) == 0:
            raise TypeError('Must specify at least one model.')
        self.__models = models
