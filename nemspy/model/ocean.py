from . import Model, ModelType, ModelVerbosity


class OceanModel(Model):
    """
    abstract implementation of a generic oceanic model
    """

    def __init__(self, name: str, processes: int, verbosity: ModelVerbosity):
        super().__init__(name, ModelType.OCEAN, processes, verbosity)


class ADCIRC(OceanModel):
    """
    Advanced Circulation (ADCIRC) model
    http://adcirc.org
    """

    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__('adcirc', processes, verbosity)


class SCHISM(OceanModel):
    """
    Semi-implicit Cross-scale Hydroscience Integrated System Model (SCHISM)
    http://ccrm.vims.edu/schismweb/
    """

    def __init__(self, processes: int, verbosity: ModelVerbosity):
        super().__init__('schism', processes, verbosity)
        raise NotImplementedError(
            f'unsupported model "{self.__class__.__name__}"')
