from os import PathLike

from .base import Model, ModelMesh, ModelType
from ..utilities import get_logger

LOGGER = get_logger('model.wave')


class WaveModel(Model):
    """
    abstract implementation of a generic wave model
    """

    def __init__(self, name: str, processors: int, **kwargs):
        super().__init__(name, ModelType.WAVE, processors, **kwargs)


class WaveMesh(WaveModel, ModelMesh):
    """
    WaveWatch III mesh reference
    """

    def __init__(self, filename: PathLike, processors: int = None, **kwargs):
        if processors is None:
            processors = 1
        # Uses ww3data as name but the implementation is model agnostic
        WaveModel.__init__(self, 'ww3data', processors, **kwargs)
        ModelMesh.__init__(self, self.model_type, filename)


class WaveWatch3(WaveModel):
    """
    WaveWatch III model
    https://polar.ncep.noaa.gov/waves/wavewatch/
    """

    def __init__(self, processors: int, **kwargs):
        super().__init__('ww3', processors, **kwargs)


class SWAN(WaveModel):
    """
    SWAN wave model
    http://swanmodel.sourceforge.net/
    """

    def __init__(self, processors: int, **kwargs):
        super().__init__('swan', processors, **kwargs)
