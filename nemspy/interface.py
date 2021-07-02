from datetime import datetime, timedelta
from os import PathLike
from pathlib import Path

from .configuration import (
    ConfigurationFile,
    ensure_directory,
    MeshFile,
    ModelConfigurationFile,
    NEMSConfigurationFile,
    RunSequence,
)
from .model.base import ConnectionEntry, MediationEntry, ModelEntry, ModelType, RemapMethod
from .utilities import parse_datetime


class ModelingSystem:
    """
    NEMS interface with configuration file output
    """

    def __init__(
        self, start_time: datetime, end_time: datetime, interval: timedelta, **models,
    ):
        """
        create a NEMS interface from the given interval and models

        :param start_time: start time within the modeled system
        :param end_time: end time within the modeled system
        :param interval: time interval of top-level run sequence
        :param verbose: verbosity in NEMS configuration
        :param atm: atmospheric wind model
        :param wav: oceanic wave model
        :param ocn: oceanic circulation model
        :param hyd: terrestrial water model
        :param med: model mediator
        """

        self.__start_time = start_time
        self.end_time = end_time

        model_types = [model_type.value.lower() for model_type in ModelType]

        parsed_models = {}
        attributes = {}
        for key, value in models.items():
            if key.lower() in model_types:
                key = key.lower()
                if isinstance(value, ModelEntry):
                    if value.model_type.value.lower() == key:
                        parsed_models[key.upper()] = value
                    else:
                        raise TypeError(f'"{value.name}" is not {key}')
                else:
                    raise TypeError(f'unsupported type {value.__class__}"')
            else:
                attributes[key] = value

        models = parsed_models
        self.__sequence = RunSequence(interval, **models, **attributes)

    @property
    def start_time(self) -> datetime:
        """ end time within modeled system """
        return self.__start_time

    @start_time.setter
    def start_time(self, start_time: datetime):
        start_time = parse_datetime(start_time)
        self.__start_time = start_time
        if self.start_time > self.end_time:
            self.start_time = self.end_time
            self.end_time = start_time

    @property
    def end_time(self) -> datetime:
        """ end time within modeled system """
        return self.__end_time

    @end_time.setter
    def end_time(self, end_time: datetime):
        end_time = parse_datetime(end_time)
        self.__end_time = end_time
        if self.end_time < self.start_time:
            self.end_time = self.start_time
            self.start_time = end_time

    @property
    def duration(self) -> timedelta:
        """ duration of run within modeled system """
        return self.end_time - self.start_time

    @property
    def interval(self) -> timedelta:
        """ run sequence interval within the modeled system """
        return self.__sequence.interval

    @interval.setter
    def interval(self, interval: timedelta):
        self.__sequence.interval = interval

    @property
    def attributes(self):
        return self.__sequence.attributes

    @attributes.setter
    def attributes(self, attributes: {str: str}):
        self.__sequence.attributes = attributes

    @property
    def models(self) -> [ModelEntry]:
        """ models in execution order """
        return self.__sequence.models

    @property
    def processors(self) -> int:
        """ number of PETs / processors / tasks """
        return self.__sequence.processors

    @property
    def sequence(self) -> [str]:
        """ model execution order """
        return [entry.sequence_entry for entry in self.__sequence.sequence]

    @sequence.setter
    def sequence(self, sequence: [str]):
        sequence_entries = []
        entries = {entry.sequence_entry: entry for entry in self.__sequence.sequence}
        for entry in sequence:
            if entry.upper() in entries:
                sequence_entries.append(entries[entry.upper()])
            elif '->' in entry:
                models = [model.strip() for model in entry.split('->')]
                if len(models) == 2:
                    connection = ConnectionEntry.from_string(entry)
                    source = connection.source.model_type.value
                    destination = connection.target.model_type.value
                    del connection

                    for connection in self.__sequence.connections:
                        if isinstance(connection, ConnectionEntry):
                            if (
                                connection.source.model_type.value == source
                                and connection.target.model_type.value == destination
                            ):
                                sequence_entries.append(connection)
                                break
                        elif isinstance(connection, MediationEntry):
                            if (connection.sources is None and source is None) or (
                                connection.sources is not None
                                and source
                                in [source.model_type.value for source in connection.sources]
                            ):
                                if (connection.targets is None and destination is None) or (
                                    connection.targets is not None
                                    and destination
                                    in [
                                        target.model_type.value
                                        for target in connection.targets
                                    ]
                                ):
                                    sequence_entries.append(connection)
                                    break
                    else:
                        raise KeyError(f'"{entry}" not in {self.connections}')
                elif len(models) == 3:
                    for mediation in self.__sequence.mediations:
                        if models == [
                            model.model_type.value
                            for model in mediation.models
                            if model is not None
                        ]:
                            sequence_entries.append(mediation)
                            break
                    else:
                        raise KeyError(f'"{entry}" not in {self.connections}')
            else:
                raise KeyError(f'"{entry}" not in {self.sequence}')
        self.__sequence.sequence = sequence_entries

    def connect(self, source: str, target: str = None, method: str = None):
        """
        couple two models with an information exchange pathway

        :param source: model providing information
        :param target: model receiving information
        :param method: remapping method
        """

        if target is None:
            try:
                connection = ConnectionEntry.from_string(source)
                source = connection.source.name
                target = connection.target.name
                del connection
            except:
                pass

        model_types = [model_type.value.upper() for model_type in ModelType]
        remap_methods = [remap.value.lower() for remap in RemapMethod]

        if source.upper() not in model_types:
            raise KeyError(f'"{source}" not in {model_types}')
        if target is not None:
            if target.upper() not in model_types:
                raise KeyError(f'"{target}" not in {model_types}')
            target = ModelType(target.upper())
        if method is not None:
            if method.lower() not in remap_methods:
                raise KeyError(f'"{method}" not in {remap_methods}')
            method = RemapMethod(method.lower())

        self.__sequence.connect(ModelType(source.upper()), target, method)

    @property
    def connections(self) -> [str]:
        """
        string representations of coupling connections in format `'WAV -> HYD'`
        """

        return [str(connection) for connection in self.__sequence.connections]

    def mediate(
        self,
        sources: [str] = None,
        functions: [str] = None,
        targets: [str] = None,
        method: RemapMethod = None,
        processors: int = None,
        **attributes,
    ):
        """
        create a mediation between one or two models and a mediator,
        with an arbitrary number of mediation functions

        :param sources: model providing information
        :param functions: mediator functions
        :param targets: model receiving information
        :param method: remapping method
        :param processors: number of processors to assign to mediation
        """

        if targets is None:
            try:
                targets = MediationEntry.from_string(sources).targets
            except:
                pass

        model_types = [model_type.value.upper() for model_type in ModelType]
        remap_methods = [remap.value.lower() for remap in RemapMethod]

        if sources is not None:
            if isinstance(sources, str):
                sources = [sources]
            for index, source in enumerate(sources):
                if isinstance(source, str):
                    if source.upper() not in model_types:
                        raise KeyError(f'"{source}" not in {model_types}')
                    sources[index] = ModelType(source.upper())
        if targets is not None:
            if isinstance(targets, str):
                targets = [targets]
            for index, target in enumerate(targets):
                if isinstance(target, str):
                    if target.upper() not in model_types:
                        raise KeyError(f'"{target}" not in {model_types}')
                    targets[index] = ModelType(target.upper())
        if method is not None and isinstance(method, str):
            if method.lower() not in remap_methods:
                raise KeyError(f'"{method}" not in {remap_methods}')
            method = RemapMethod(method.lower())

        self.__sequence.mediate(sources, functions, targets, method, processors, **attributes)

    @property
    def __configuration_files(self) -> [ConfigurationFile]:
        return [
            NEMSConfigurationFile(self.__sequence),
            MeshFile(self.__sequence),
            ModelConfigurationFile(self.start_time, self.duration, self.__sequence),
        ]

    @property
    def configuration(self) -> {str: str}:
        return {
            configuration_file.name: str(configuration_file)
            for configuration_file in self.__configuration_files
        }

    def write(
        self, directory: PathLike, overwrite: bool = False, include_version: bool = False,
    ) -> [Path]:
        """
        write NEMS / NUOPC configuration to the given directory

        :param directory: path to output directory
        :param overwrite: overwrite existing files
        :param include_version: include the NEMSpy version in a comment
        """

        directory = ensure_directory(directory)
        filenames = []
        for configuration_file in self.__configuration_files:
            filename = configuration_file.write(
                directory / configuration_file.name, overwrite, include_version
            )
            filenames.append(filename)
            if isinstance(configuration_file, ModelConfigurationFile):
                filenames.append(directory / 'atm_namelist.rc')
        return filenames

    def __getitem__(self, model_type: str) -> ModelEntry:
        if not isinstance(model_type, str) and not isinstance(model_type, ModelType):
            raise ValueError(
                f'model type must be {str} or {ModelType}, not {type(model_type)}'
            )
        model_types = [model_type.value.upper() for model_type in ModelType]
        if model_type.upper() not in model_types:
            raise KeyError(f'"{model_type}" not in {model_types}')
        return self.__sequence[ModelType(model_type.upper())]

    def __setitem__(self, model_type: str, model: ModelEntry):
        if not isinstance(model_type, str) and not isinstance(model_type, ModelType):
            raise ValueError(
                f'model type must be {str} or {ModelType}, not {type(model_type)}'
            )
        model_types = [model_type.value.upper() for model_type in ModelType]
        if model_type.upper() not in model_types:
            raise KeyError(f'"{model_type}" not in {model_types}')
        self.__sequence[ModelType(model_type.upper())] = model

    def __contains__(self, model_type: str) -> bool:
        if not isinstance(model_type, str) and not isinstance(model_type, ModelType):
            raise ValueError(
                f'model type must be {str} or {ModelType}, not {type(model_type)}'
            )
        return ModelType(model_type.upper()) in self.__sequence

    def __repr__(self) -> str:
        models = [f'{model.model_type}={repr(model)}' for model in self.__sequence.models]
        return f'{self.__class__.__name__}({repr(self.interval)}, {", ".join(models)})'
