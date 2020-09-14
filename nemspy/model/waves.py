from .base import Model, ModelType
from ..utilities import get_logger

LOGGER = get_logger('model.wave')


class WaveModel(Model):
    """
    abstract implementation of a generic wave model
    """

    def __init__(self, name: str, processes: int, **kwargs):
        super().__init__(name, ModelType.WAVE, processes, **kwargs)


class WaveMeshData(WaveModel):
    """
    WaveWatch III mesh reference
    """

    def __init__(self, **kwargs):
        # Uses ww3data as name but the implementation is model agnostic
        super().__init__('ww3data', 1, **kwargs)


class WaveWatch3(WaveModel):
    """
    WaveWatch III model
    https://polar.ncep.noaa.gov/waves/wavewatch/
    """

    def __init__(self, processes: int, **kwargs):
        super().__init__('ww3', processes, **kwargs)


class SWAN(WaveModel):
    """
    SWAN wave model
    http://swanmodel.sourceforge.net/
    """

    def __init__(self, processes: int, **kwargs):
        super().__init__('swan', processes, **kwargs)
