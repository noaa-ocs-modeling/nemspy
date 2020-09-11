from . import Model, ModelType, ModelVerbosity


class AtmosphericModel(Model):
    """
    abstract implementation of a generic atmospheric modeling system
    """

    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(ModelType.ATMOSPHERIC, processes, verbosity)


class ATMesh(AtmosphericModel):
    """
    Atmospheric Mesh (ATMesh) modeling system
    """

    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(processes, verbosity)


class HWRF(AtmosphericModel):
    """
    Hurricane Weather Research and Forecasting (HWRF) modeling system
    https://en.wikipedia.org/wiki/Hurricane_Weather_Research_and_Forecasting_Model
    """

    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(processes, verbosity)
