from datetime import timedelta
import pathlib
from typing import Union, List, Dict

from .model.base import ModelEntry, ModelType
from .model.earth import EarthModel
from .model.ocean import OceanModel
from .model.atmospheric import AtmosphericModel
from .model.waves import WaveModel
from .model.hydrological import HydrologicalModel
from .configuration import ModelSequence
from .verbosity import ModelVerbosity


class NEMS:

    header = '#############################################\n' \
             '####  NEMS Run-Time Configuration File  #####\n' \
             '#############################################'

    def __init__(
            self,
            ocean: OceanModel = None,
            waves: WaveModel = None,
            atmospheric: AtmosphericModel = None,
            hydrological: HydrologicalModel = None,
            verbosity: ModelVerbosity = ModelVerbosity.MAXIMUM
    ):
        self.ocean = ocean
        self.waves = waves
        self.atmospheric = atmospheric
        self.hydrological = hydrological
        self.verbosity = verbosity
        self.sequences: List[ModelSequence] = []

    def __str__(self):
        return f'{self.header}\n' \
               f'{str(self.earth)}\n' + \
               "\n".join([str(seq) for seq in self.sequences])

    def add_sequence(self, duration: timedelta) -> ModelSequence:
        seq = ModelSequence(
            duration,
            **self.models
            )
        self.sequences.append(seq)
        return seq

    def write(self, filename: Union[str, pathlib.Path],
              overwrite: bool = False):
        raise NotImplementedError

    @property
    def earth(self):
        return EarthModel(self.verbosity, **self.models)

    @property
    def ocean(self):
        return self.__ocean

    @ocean.setter
    def ocean(self, ocean: Union[None, OceanModel]):
        if ocean is not None:
            assert isinstance(ocean, OceanModel)
        self.__ocean = ocean

    @property
    def waves(self):
        return self.__waves

    @waves.setter
    def waves(self, waves: Union[None, WaveModel]):
        if waves is not None:
            assert isinstance(waves, WaveModel)
        self.__waves = waves

    @property
    def atmospheric(self):
        return self.__atmospheric

    @atmospheric.setter
    def atmospheric(self, atmospheric: Union[None, AtmosphericModel]):
        if atmospheric is not None:
            assert isinstance(atmospheric, AtmosphericModel)
        self.__atmospheric = atmospheric

    @property
    def hydrological(self):
        return self.__hydrological

    @hydrological.setter
    def hydrological(self, hydrological: Union[None, HydrologicalModel]):
        if hydrological is not None:
            assert isinstance(hydrological, HydrologicalModel)
        self.__hydrological = hydrological

    @property
    def verbosity(self):
        return self.__verbosity

    @verbosity.setter
    def verbosity(self, verbosity: ModelVerbosity):
        if verbosity is None:
            verbosity = ModelVerbosity.MAXIMUM
        self.__verbosity = verbosity

    @property
    def models(self) -> Dict[str, ModelEntry]:
        models: Dict[ModelType, ModelEntry] = {}
        models[ModelType.OCEAN] = self.ocean
        models[ModelType.WAVES] = self.waves
        models[ModelType.ATMOSPHERIC] = self.atmospheric
        models[ModelType.HYDROLOGICAL] = self.hydrological
        return {model_type.name.lower(): model
                for model_type, model in models.items()}

    # @models.setter
    # def models(self, models):
    #     if len(models) == 0:
    #         raise TypeError('Must specify at least one model.')
    #     self.__models = models

    # @property
    # def configuration(self):
    #     return NEMSConfiguration(self.sequences)
