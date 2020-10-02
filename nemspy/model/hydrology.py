from .base import ModelEntry, ModelType
from ..utilities import get_logger

LOGGER = get_logger('model.hydro')


class HydrologicalModelEntry(ModelEntry):
    """
    abstract implementation of a generic hydrological model
    """

    def __init__(self, name: str, processors: int, **kwargs):
        super().__init__(name, ModelType.HYDROLOGICAL, processors, **kwargs)


class NationalWaterModelEntry(HydrologicalModelEntry):
    """
    National Water Model
    https://water.noaa.gov/about/nwm
    """

    def __init__(self, processors: int, **kwargs):
        super().__init__('nwm', processors, **kwargs)
