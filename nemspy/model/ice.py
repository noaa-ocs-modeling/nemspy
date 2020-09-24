from os import PathLike

from .base import Model, ModelMesh, ModelType
from ..utilities import get_logger

LOGGER = get_logger('model.wave')


class IceModel(Model):
    """
    abstract implementation of a generic ice model
    """

    def __init__(self, name: str, processors: int, **kwargs):
        super().__init__(name, ModelType.ICE, processors, **kwargs)


class IceMesh(IceModel, ModelMesh):
    """
    Ice model mesh reference
    """

    def __init__(self, filename: PathLike, processors: int = None, **kwargs):
        if processors is None:
            processors = 1
        # Uses ww3data as name but the implementation is model agnostic
        IceModel.__init__(self, 'icemesh', processors, **kwargs)
        ModelMesh.__init__(self, self.model_type, filename)
