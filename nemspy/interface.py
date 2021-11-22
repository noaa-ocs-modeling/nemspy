from datetime import datetime, timedelta
from os import PathLike
from pathlib import Path
from typing import Dict, List

from nemspy.configuration import (
    ConfigurationFile,
    ensure_directory,
    FileForcingsFile,
    ModelConfigurationFile,
    NEMSConfigurationFile,
    RunSequence,
)
from nemspy.model.base import (
    ConnectionEntry,
    EntryType,
    GridRemapMethod,
    MediationEntry,
    ModelEntry,
)
from nemspy.utilities import parse_datetime


class ModelingSystem:
    """
    main user interface class of NEMSpy, providing configuration and output to files

    .. code-block:: python

        from datetime import datetime, timedelta
        from nemspy import ModelingSystem
        from nemspy.model import ADCIRCEntry, AtmosphericForcingEntry, WaveWatch3ForcingEntry

        # instantiate model system with model entries
        nems = ModelingSystem(
         start_time=datetime(2020, 6, 1),
         end_time=start_time + timedelta(days=1),
         interval=timedelta(hours=1),
         ocn=ADCIRCEntry(processors=11),
         atm=AtmosphericForcingEntry(filename='wind_atm_fin_ch_time_vec.nc'),
         wav=WaveWatch3ForcingEntry(filename='ww3.Constant.20151214_sxy_ike_date.nc'),
        )

        # form connections between models
        nems.connect('ATM', 'OCN')
        nems.connect('WAV', 'OCN')

        # define execution order
        nems.sequence = [
         'ATM -> OCN',
         'WAV -> OCN',
         'ATM',
         'WAV',
         'OCN',
        ]

        # write configuration files to the given directory
        nems.write('nems_configuration')
    """

    def __init__(
        self, start_time: datetime, end_time: datetime, interval: timedelta, **models,
    ):
        """
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

        model_types = [model_type.value.lower() for model_type in EntryType]

        parsed_models = {}
        attributes = {}
        for key, value in models.items():
            if key.lower() in model_types:
                key = key.lower()
                if isinstance(value, ModelEntry):
                    if value.entry_type.value.lower() == key:
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
        """
        end time within modeled system
        """

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
        """
        end time within modeled system
        """

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
        """
        duration of run within modeled system
        """

        return self.end_time - self.start_time

    @property
    def interval(self) -> timedelta:
        """
        run sequence interval within the modeled system
        """

        return self.__sequence.interval

    @interval.setter
    def interval(self, interval: timedelta):
        self.__sequence.interval = interval

    @property
    def attributes(self):
        return self.__sequence.attributes

    @attributes.setter
    def attributes(self, attributes: Dict[str, str]):
        self.__sequence.attributes = attributes

    @property
    def models(self) -> List[ModelEntry]:
        """
        models in execution order
        """

        return self.__sequence.models

    @property
    def processors(self) -> int:
        """
        number of PETs / processors / tasks
        """

        return self.__sequence.processors

    @property
    def sequence(self) -> List[str]:
        """
        model execution order
        """

        return [entry.sequence_entry for entry in self.__sequence.sequence]

    @sequence.setter
    def sequence(self, sequence: List[str]):
        sequence_entries = []
        entries = {entry.sequence_entry: entry for entry in self.__sequence.sequence}
        for entry in sequence:
            if entry.upper() in entries:
                sequence_entries.append(entries[entry.upper()])
            elif '->' in entry:
                models = [model.strip() for model in entry.split('->')]
                if len(models) == 2:
                    connection = ConnectionEntry.from_string(entry)
                    source = connection.source.entry_type.value
                    destination = connection.target.entry_type.value
                    del connection

                    for connection in self.__sequence.connections:
                        if isinstance(connection, ConnectionEntry):
                            if (
                                connection.source.entry_type.value == source
                                and connection.target.entry_type.value == destination
                            ):
                                sequence_entries.append(connection)
                                break
                        elif isinstance(connection, MediationEntry):
                            if (connection.sources is None and source is None) or (
                                connection.sources is not None
                                and source
                                in [source.entry_type.value for source in connection.sources]
                            ):
                                if (connection.targets is None and destination is None) or (
                                    connection.targets is not None
                                    and destination
                                    in [
                                        target.entry_type.value
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
                            model.entry_type.value
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

        model_types = [model_type.value.upper() for model_type in EntryType]
        remap_methods = [remap.value.lower() for remap in GridRemapMethod]

        if source.upper() not in model_types:
            raise KeyError(f'"{source}" not in {model_types}')
        if target is not None:
            if target.upper() not in model_types:
                raise KeyError(f'"{target}" not in {model_types}')
            target = EntryType(target.upper())
        if method is not None:
            if method.lower() not in remap_methods:
                raise KeyError(f'"{method}" not in {remap_methods}')
            method = GridRemapMethod(method.lower())

        self.__sequence.connect(EntryType(source.upper()), target, method)

    @property
    def connections(self) -> List[str]:
        """
        string representations of coupling connections in format ``'WAV -> HYD'``
        """

        return [str(connection) for connection in self.__sequence.connections]

    def mediate(
        self,
        sources: List[str] = None,
        functions: List[str] = None,
        targets: List[str] = None,
        method: GridRemapMethod = None,
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

        model_types = [model_type.value.upper() for model_type in EntryType]
        remap_methods = [remap.value.lower() for remap in GridRemapMethod]

        if sources is not None:
            if isinstance(sources, str):
                sources = [sources]
            for index, source in enumerate(sources):
                if isinstance(source, str):
                    if source.upper() not in model_types:
                        raise KeyError(f'"{source}" not in {model_types}')
                    sources[index] = EntryType(source.upper())
        if targets is not None:
            if isinstance(targets, str):
                targets = [targets]
            for index, target in enumerate(targets):
                if isinstance(target, str):
                    if target.upper() not in model_types:
                        raise KeyError(f'"{target}" not in {model_types}')
                    targets[index] = EntryType(target.upper())
        if method is not None and isinstance(method, str):
            if method.lower() not in remap_methods:
                raise KeyError(f'"{method}" not in {remap_methods}')
            method = GridRemapMethod(method.lower())

        self.__sequence.mediate(sources, functions, targets, method, processors, **attributes)

    @property
    def __configuration_files(self) -> List[ConfigurationFile]:
        return [
            NEMSConfigurationFile(self.__sequence),
            FileForcingsFile(self.__sequence),
            ModelConfigurationFile(self.start_time, self.duration, self.__sequence),
        ]

    @property
    def configuration(self) -> Dict[str, str]:
        return {
            configuration_file.name: str(configuration_file)
            for configuration_file in self.__configuration_files
        }

    def write(
        self, directory: PathLike, overwrite: bool = False, include_version: bool = False,
    ) -> List[Path]:
        """
        write NEMS / NUOPC configuration to the given directory

        :param directory: path to output directory
        :param overwrite: overwrite existing files
        :param include_version: include the NEMSpy version in a comment
        :returns: list of written file paths
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
        if not isinstance(model_type, str) and not isinstance(model_type, EntryType):
            raise ValueError(
                f'model type must be {str} or {EntryType}, not {type(model_type)}'
            )
        model_types = [model_type.value.upper() for model_type in EntryType]
        if model_type.upper() not in model_types:
            raise KeyError(f'"{model_type}" not in {model_types}')
        return self.__sequence[EntryType(model_type.upper())]

    def __setitem__(self, model_type: str, model: ModelEntry):
        if not isinstance(model_type, str) and not isinstance(model_type, EntryType):
            raise ValueError(
                f'model type must be {str} or {EntryType}, not {type(model_type)}'
            )
        model_types = [model_type.value.upper() for model_type in EntryType]
        if model_type.upper() not in model_types:
            raise KeyError(f'"{model_type}" not in {model_types}')
        self.__sequence[EntryType(model_type.upper())] = model

    def __contains__(self, model_type: str) -> bool:
        if not isinstance(model_type, str) and not isinstance(model_type, EntryType):
            raise ValueError(
                f'model type must be {str} or {EntryType}, not {type(model_type)}'
            )
        return EntryType(model_type.upper()) in self.__sequence

    def __repr__(self) -> str:
        models = [f'{model.entry_type}={repr(model)}' for model in self.__sequence.models]
        return f'{self.__class__.__name__}({repr(self.interval)}, {", ".join(models)})'
