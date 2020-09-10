from NEMSpy.model.model import Model, ModelKey, ModelVerbosity


class AtmosphericModel(Model):
    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(ModelKey.ATMOSPHERIC, processes, verbosity)


class ATMESH(AtmosphericModel):
    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(processes, verbosity)


class HWRF(AtmosphericModel):
    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(processes, verbosity)
