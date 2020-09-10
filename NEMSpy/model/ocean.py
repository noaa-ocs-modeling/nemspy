from NEMSpy.model.model import Model, ModelKey, ModelVerbosity


class OceanModel(Model):
    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(ModelKey.OCEAN, processes, verbosity)


class ADCIRC(OceanModel):
    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(processes, verbosity)


class SCHISM(OceanModel):
    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(processes, verbosity)
