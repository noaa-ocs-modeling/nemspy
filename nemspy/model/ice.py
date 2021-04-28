from os import PathLike

from .base import ModelEntry, ModelMeshEntry, ModelType


class IceModelEntry(ModelEntry):
    """
    abstract implementation of a generic ice model
    """

    model_type = ModelType.ICE

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)


class IceMeshEntry(IceModelEntry, ModelMeshEntry):
    """
    Ice model mesh reference
    """

    name = 'icemesh'

    def __init__(self, filename: PathLike = None, processors: int = None, **kwargs):
        if processors is None:
            processors = 1
        # Uses ww3data as name but the implementation is model agnostic
        IceModelEntry.__init__(self, processors, **kwargs)
        ModelMeshEntry.__init__(self, self.model_type, filename)
