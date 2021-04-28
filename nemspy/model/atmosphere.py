from os import PathLike

from .base import ModelEntry, ModelMeshEntry, ModelType


class AtmosphericModelEntry(ModelEntry):
    """
    abstract implementation of a generic atmospheric model
    """

    model_type = ModelType.ATMOSPHERIC

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)


class AtmosphericMeshEntry(AtmosphericModelEntry, ModelMeshEntry):
    """
    Atmospheric Mesh (ATMesh) reference
    """

    name = 'atmesh'

    def __init__(self, filename: PathLike = None, processors: int = None, **kwargs):
        if processors is None:
            processors = 1
        AtmosphericModelEntry.__init__(self, processors, **kwargs)
        ModelMeshEntry.__init__(self, self.model_type, filename)


class HWRFEntry(AtmosphericModelEntry):
    """
    Hurricane Weather Research and Forecasting (HWRF) model
    https://en.wikipedia.org/wiki/Hurricane_Weather_Research_and_Forecasting_Model
    """

    name = 'hwrf'

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)
