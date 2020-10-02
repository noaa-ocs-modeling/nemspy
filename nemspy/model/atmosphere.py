from os import PathLike

from .base import ModelEntry, ModelMeshEntry, ModelType
from ..utilities import get_logger

LOGGER = get_logger('model.atmos')


class AtmosphericModelEntry(ModelEntry):
    """
    abstract implementation of a generic atmospheric model
    """

    def __init__(self, name: str, processors: int, **kwargs):
        super().__init__(name, ModelType.ATMOSPHERIC, processors, **kwargs)


class AtmosphericMeshEntry(AtmosphericModelEntry, ModelMeshEntry):
    """
    Atmospheric Mesh (ATMesh) reference
    """

    def __init__(self, filename: PathLike, processors: int = None, **kwargs):
        if processors is None:
            processors = 1
        AtmosphericModelEntry.__init__(self, 'atmesh', processors, **kwargs)
        ModelMeshEntry.__init__(self, self.model_type, filename)


class HWRFEntry(AtmosphericModelEntry):
    """
    Hurricane Weather Research and Forecasting (HWRF) model
    https://en.wikipedia.org/wiki/Hurricane_Weather_Research_and_Forecasting_Model
    """

    def __init__(self, processors: int, **kwargs):
        super().__init__('hwrf', processors, **kwargs)
