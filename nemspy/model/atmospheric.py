from nemspy.model import Model, ModelType, ModelVerbosity


class AtmosphericModel(Model):
    """
    abstract implementation of a generic atmospheric model
    """

    def __init__(self, name: str, processes: int, verbosity: ModelVerbosity):
        super().__init__(name, ModelType.ATMOSPHERIC, processes, verbosity)


class ATMesh(AtmosphericModel):
    """
    Atmospheric Mesh (ATMesh) model
    """

    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__('atmesh', processes, verbosity)


class HWRF(AtmosphericModel):
    """
    Hurricane Weather Research and Forecasting (HWRF) model
    https://en.wikipedia.org/wiki/Hurricane_Weather_Research_and_Forecasting_Model
    """

    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__('hwrf', processes, verbosity)
