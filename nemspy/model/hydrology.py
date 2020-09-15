from .base import Model, ModelType
from ..utilities import get_logger

LOGGER = get_logger('model.hydro')


class HydrologicalModel(Model):
    """
    abstract implementation of a generic hydrological model
    """

    def __init__(self, name: str, processors: int, **kwargs):
        super().__init__(name, ModelType.HYDROLOGICAL, processors, **kwargs)


class NationalWaterModel(HydrologicalModel):
    """
    National Water Model
    https://water.noaa.gov/about/nwm
    """

    def __init__(self, processors: int, **kwargs):
        super().__init__('nwm', processors, **kwargs)
