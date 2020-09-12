from datetime import timedelta
from .model import ModelType, Model
from .model.ocean import OceanModel
from .model.atmospheric import AtmosphericModel
from .model.waves import WaveModel
from .model.hydrologic import HydrologicalModel
from .configuration import NEMSConfiguration, ModelSequence


class NEMS:

    def __init__(
            self,
            ocean: OceanModel = None,
            waves: WaveModel = None,
            atmospheric: AtmosphericModel = None,
            hydrologic: HydrologicalModel = None
    ):
        models = {}

        if ocean is not None:
            assert isinstance(ocean, OceanModel)
        models.update({OceanModel: ocean})

        if waves is not None:
            assert isinstance(waves, WaveModel)
        models.update({WaveModel: waves})

        if atmospheric is not None:
            assert isinstance(atmospheric, AtmosphericModel)
        models.update({AtmosphericModel: atmospheric})

        if hydrologic is not None:
            assert isinstance(hydrologic, HydrologicalModel)
        models.update({HydrologicalModel: hydrologic})

        self.models = models
        self.sequences = []

    def add_sequence(self, duration: timedelta) -> ModelSequence:
        self.sequences.append(seq := ModelSequence(duration, **self.models))
        return seq

    def write(self, filename: str):
        self.configuration.write(filename)

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

    @property
    def configuration(self):
        return NEMSConfiguration(self.sequences)
