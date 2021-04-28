from .base import ModelEntry, ModelType


class HydrologicalModelEntry(ModelEntry):
    """
    abstract implementation of a generic hydrological model
    """

    model_type = ModelType.HYDROLOGICAL

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)


class NationalWaterModelEntry(HydrologicalModelEntry):
    """
    National Water Model
    https://water.noaa.gov/about/nwm
    """

    name = 'nwm'

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)
