from .base import ModelEntry, ModelType
from ..utilities import get_logger

LOGGER = get_logger('model.ocean')


class OceanModelEntry(ModelEntry):
    """
    abstract implementation of a generic oceanic model
    """

    def __init__(self, name: str, processors: int, **kwargs):
        super().__init__(name, ModelType.OCEAN, processors, **kwargs)


class ADCIRCEntry(OceanModelEntry):
    """
    Advanced Circulation (ADCIRC) model
    http://adcirc.org
    """

    def __init__(self, processors: int, **kwargs):
        super().__init__('adcirc', processors, **kwargs)


class SCHISMEntry(OceanModelEntry):
    """
    Semi-implicit Cross-scale Hydroscience Integrated System Model (SCHISM)
    http://ccrm.vims.edu/schismweb/
    """

    def __init__(self, processors: int, **kwargs):
        super().__init__('schism', processors, **kwargs)
        raise NotImplementedError(f'unsupported model "{self.__class__.__name__}"')
