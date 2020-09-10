from NEMSpy.model.model import Model, ModelKey, ModelVerbosity


class HydrologicalModel(Model):
    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(ModelKey.HYDROLOGICAL, processes, verbosity)


class NationalWaterModel(HydrologicalModel):
    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(processes, verbosity)
