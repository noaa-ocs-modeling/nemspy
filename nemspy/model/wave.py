from . import Model, ModelType, ModelVerbosity


class WaveModel(Model):
    """
    abstract implementation of a generic wave model
    """

    def __init__(self, name: str, processes: int, verbosity: ModelVerbosity):
        super().__init__(name, ModelType.WAVE, processes, verbosity)


class WaveWatch3(WaveModel):
    """
    WaveWatch III model
    https://polar.ncep.noaa.gov/waves/wavewatch/
    """

    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__('ww3', processes, verbosity)


class WaveWatch3Data(WaveWatch3):
    """
    dummy IO for simulated WaveWatch III output
    """

    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(processes, verbosity)
        self.name = 'ww3data'


class SWAN(WaveModel):
    """
    SWAN wave model
    http://swanmodel.sourceforge.net/
    """

    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__('swan', processes, verbosity)
