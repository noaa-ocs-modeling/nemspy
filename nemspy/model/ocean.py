from .base import ModelEntry, ModelType


class OceanModelEntry(ModelEntry):
    """
    abstract implementation of a generic oceanic model
    """

    model_type = ModelType.OCEAN

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)


class ADCIRCEntry(OceanModelEntry):
    """
    Advanced Circulation (ADCIRC) model
    http://adcirc.org
    """

    name = 'adcirc'

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)


class SCHISMEntry(OceanModelEntry):
    """
    Semi-implicit Cross-scale Hydroscience Integrated System Model (SCHISM)
    http://ccrm.vims.edu/schismweb/
    """

    name = 'schism'

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)
