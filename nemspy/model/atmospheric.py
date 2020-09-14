from .base import ModelEntry, ModelType
from ..logger import get_logger

LOGGER = get_logger('model.atmos')


class AtmosphericModel(ModelEntry):
    """
    abstract implementation of a generic atmospheric model
    """

    def __init__(self, name: str, processes: int, **kwargs):
        super().__init__(name, ModelType.ATMOSPHERIC, processes, **kwargs)


class AtmosphericMeshData(AtmosphericModel):
    """
    Atmospheric Mesh (ATMesh) reference
    """

    def __init__(self, **kwargs):
        super().__init__('atmesh', 1, **kwargs)


class HWRF(AtmosphericModel):
    """
    Hurricane Weather Research and Forecasting (HWRF) model
    https://en.wikipedia.org/wiki/Hurricane_Weather_Research_and_Forecasting_Model
    """

    def __init__(self, processes: int, **kwargs):
        super().__init__('hwrf', processes, **kwargs)
