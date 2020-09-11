from . import Model, ModelType, ModelVerbosity


class OceanModel(Model):
    """
    abstract implementation of a generic oceanic modeling system
    """

    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(ModelType.OCEAN, processes, verbosity)


class ADCIRC(OceanModel):
    """
    Advanced Circulation (ADCIRC) modeling system
    http://adcirc.org
    """

    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(processes, verbosity)


class SCHISM(OceanModel):
    """
    Semi-implicit Cross-scale Hydroscience Integrated System Model (SCHISM)
    http://ccrm.vims.edu/schismweb/
    """

    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__(processes, verbosity)
