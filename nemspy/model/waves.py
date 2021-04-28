from os import PathLike

from .base import ModelEntry, ModelMeshEntry, ModelType


class WaveModelEntry(ModelEntry):
    """
    abstract implementation of a generic wave model
    """

    model_type = ModelType.WAVE

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)


class WaveWatch3MeshEntry(WaveModelEntry, ModelMeshEntry):
    """
    WaveWatch III mesh reference
    """

    name = 'ww3data'

    def __init__(self, filename: PathLike = None, processors: int = None, **kwargs):
        if processors is None:
            processors = 1
        # Uses ww3data as name but the implementation is model agnostic
        WaveModelEntry.__init__(self, processors, **kwargs)
        ModelMeshEntry.__init__(self, self.model_type, filename)


class WaveWatch3Entry(WaveModelEntry):
    """
    WaveWatch III model
    https://polar.ncep.noaa.gov/waves/wavewatch/
    """

    name = 'ww3'

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)


class SWANEntry(WaveModelEntry):
    """
    SWAN wave model
    http://swanmodel.sourceforge.net/
    """

    name = 'swan'

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)
