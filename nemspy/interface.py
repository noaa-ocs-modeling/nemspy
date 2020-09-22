from datetime import datetime, timedelta
from os import PathLike

from .configuration import MeshFile, ModelConfigurationFile, ModelSequence, \
    NEMSConfigurationFile
from .model.base import Model, ModelType, ModelVerbosity, RemapMethod


class ModelingSystem:
    """
    NEMS interface with configuration file output
    """

    def __init__(self, start_time: datetime, duration: timedelta,
                 interval: timedelta, verbose: bool = False, **models):
        """
        create a NEMS interface from the given interval and models

        :param start_time: time at which to start
        :param duration: total time to run models
        :param interval: time interval of top-level run sequence
        :param verbose: verbosity in NEMS configuration
        :param atmospheric: atmospheric wind model
        :param wave: oceanic wave model
        :param ocean: oceanic circulation model
        :param hydrological: terrestrial water model
        """

        self.__models = {}
        for model_type, model in models.items():
            model_types = {entry.name.lower() for entry in ModelType}
            if model_type in model_types:
                if isinstance(model, Model):
                    if model.model_type.name.lower() == model_type:
                        self.__models[model_type] = model
                    else:
                        raise ValueError(f'"{model.name}" model is not '
                                         f'type "{model_type}"')
                else:
                    raise ValueError(f'value must be of type {Model}')
            else:
                raise ValueError(f'unexpected model type "{model_type}"; '
                                 f'must be one of {model_types}')

        self.__sequence = ModelSequence(interval, verbose, **self.__models)
        self.__configuration_files = [
            NEMSConfigurationFile(self.__sequence),
            MeshFile(self.__sequence),
            ModelConfigurationFile(start_time, duration, self.__sequence)
        ]

    @property
    def interval(self) -> timedelta:
        """
        run sequence interval
        """

        return self.__sequence.interval

    @interval.setter
    def interval(self, interval: timedelta):
        self.__sequence.interval = interval

    @property
    def models(self) -> [Model]:
        """
        models in execution order
        """

        return self.__sequence.entries

    @property
    def sequence(self) -> [str]:
        """
        model execution order
        """

        return [model_type.name.lower()
                for model_type in self.__sequence.sequence]

    @sequence.setter
    def sequence(self, sequence: [str]):
        model_types = [model_type.name.lower() for model_type in ModelType]
        for model_type in sequence:
            if model_type.lower() not in model_types:
                raise ValueError(f'"{model_type}" not in {model_types}')
        self.__sequence.sequence = [ModelType[model_type.upper()]
                                    for model_type in sequence]

    def connect(self, source: str, destination: str, method: str = None):
        """
        couple two models with an information exchange pathway

        :param source: model providing information (from `models.ModelType`)
        :param destination: model receiving information (from `models.ModelType`)
        :param method: remapping method (from `models.RemapMethod`)
        """

        model_types = [model_type.name.lower() for model_type in ModelType]
        remap_methods = [remap.name.lower() for remap in RemapMethod]

        if source.lower() not in model_types:
            raise ValueError(f'"{source}" not in {model_types}')
        if destination.lower() not in model_types:
            raise ValueError(f'"{destination}" not in {model_types}')
        if method is not None:
            if method.lower() not in remap_methods:
                raise ValueError(f'"{method}" not in {remap_methods}')
            method = RemapMethod[method.upper()]

        self.__sequence.connect(ModelType[source.upper()],
                                ModelType[destination.upper()],
                                method)

    @property
    def connections(self) -> [str]:
        """
        string representations of coupling connections in format `'WAV -> HYD   :remapMethod=redist'`
        """

        return [str(connection)
                for connection in self.__sequence.connections]

    @property
    def configuration(self) -> {str: str}:
        return {configuration_file.name: str(configuration_file)
                for configuration_file in self.__configuration_files}

    def write(self, directory: PathLike, overwrite: bool = False):
        """
        write NEMS / NUOPC configuration to the given directory

        :param directory: path to output directory
        :param overwrite: whether to overwrite existing files
        """

        for configuration_file in self.__configuration_files:
            configuration_file.write(directory, overwrite)

    @property
    def verbose(self) -> bool:
        return self.__sequence.verbosity is ModelVerbosity.MAXIMUM

    @verbose.setter
    def verbose(self, verbose: bool):
        self.__sequence.verbosity = ModelVerbosity.MAXIMUM if verbose else ModelVerbosity.MINIMUM

    def __getitem__(self, model_type: str) -> Model:
        return self.__models[model_type]

    def __repr__(self) -> str:
        models = [f'{model_type}={repr(model)}'
                  for model_type, model in self.__models.items()]
        return f'{self.__class__.__name__}({repr(self.interval)}, {", ".join(models)})'
