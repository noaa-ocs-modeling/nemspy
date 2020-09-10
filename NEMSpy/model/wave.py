from NEMSpy.model import Model, ModelType, ModelVerbosity


class WaveModel(Model):
    """
    abstract implementation of a generic wave modeling system
    """

    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(ModelType.WAVE, processes, verbosity)


class WaveWatch3(WaveModel):
    """
    WaveWatch III modeling system
    https://polar.ncep.noaa.gov/waves/wavewatch/
    """

    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(processes, verbosity)


class WaveWatch3Data(WaveWatch3):
    """
    Dummy IO for simulated WaveWatch III output
    """

    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(processes, verbosity)


class SWAN(WaveModel):
    """
    http://swanmodel.sourceforge.net/
    """

    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(processes, verbosity)
