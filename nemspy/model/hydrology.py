from nemspy.model.base import EntryType, ModelEntry


class HydrologicalModelEntry(ModelEntry):
    """
    abstraction of a generic hydrological model
    """

    entry_type = EntryType.HYDROLOGICAL

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
