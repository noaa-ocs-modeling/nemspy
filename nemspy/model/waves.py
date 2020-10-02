from os import PathLike

from .base import ModelEntry, ModelMeshEntry, ModelType
from ..utilities import get_logger

LOGGER = get_logger('model.wave')


class WaveModelEntry(ModelEntry):
    """
    abstract implementation of a generic wave model
    """

    def __init__(self, name: str, processors: int, **kwargs):
        super().__init__(name, ModelType.WAVE, processors, **kwargs)


class WaveMeshEntry(WaveModelEntry, ModelMeshEntry):
    """
    WaveWatch III mesh reference
    """

    def __init__(self, filename: PathLike, processors: int = None, **kwargs):
        if processors is None:
            processors = 1
        # Uses ww3data as name but the implementation is model agnostic
        WaveModelEntry.__init__(self, 'ww3data', processors, **kwargs)
        ModelMeshEntry.__init__(self, self.model_type, filename)


class WaveWatch3Entry(WaveModelEntry):
    """
    WaveWatch III model
    https://polar.ncep.noaa.gov/waves/wavewatch/
    """

    def __init__(self, processors: int, **kwargs):
        super().__init__('ww3', processors, **kwargs)


class SWANEntry(WaveModelEntry):
    """
    SWAN wave model
    http://swanmodel.sourceforge.net/
    """

    def __init__(self, processors: int, **kwargs):
        super().__init__('swan', processors, **kwargs)
