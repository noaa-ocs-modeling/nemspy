from NEMSpy.model.model import Model, ModelKey, ModelVerbosity


class WaveModel(Model):
    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(ModelKey.WAVE, processes, verbosity)


class WaveWatch3(WaveModel):
    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(processes, verbosity)


class WaveWatch3Data(WaveWatch3):
    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(processes, verbosity)


class SWAN(WaveModel):
    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(processes, verbosity)
