from .base import Model, ModelType
from ..utilities import get_logger

LOGGER = get_logger('model.ocean')


class OceanModel(Model):
    """
    abstract implementation of a generic oceanic model
    """

    def __init__(self, name: str, processes: int, **kwargs):
        super().__init__(name, ModelType.OCEAN, processes, **kwargs)


class ADCIRC(OceanModel):
    """
    Advanced Circulation (ADCIRC) model
    http://adcirc.org
    """

    def __init__(self, processes: int, **kwargs):
        super().__init__('adcirc', processes, **kwargs)


class SCHISM(OceanModel):
    """
    Semi-implicit Cross-scale Hydroscience Integrated System Model (SCHISM)
    http://ccrm.vims.edu/schismweb/
    """

    def __init__(self, processes: int, **kwargs):
        super().__init__('schism', processes, **kwargs)
        raise NotImplementedError(
            f'unsupported model "{self.__class__.__name__}"')
