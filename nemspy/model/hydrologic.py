from . import Model, ModelType
from .. import get_logger

LOGGER = get_logger('model.hydro')


class HydrologicalModel(Model):
    """
    abstract implementation of a generic hydrological model
    """

    def __init__(self, name: str, processes: int, **kwargs):
        super().__init__(name, ModelType.HYDROLOGICAL, processes, **kwargs)


class NationalWaterModel(HydrologicalModel):
    """
    National Water Model
    https://water.noaa.gov/about/nwm
    """

    def __init__(self, processes: int, **kwargs):
        super().__init__('nwm', processes, **kwargs)
