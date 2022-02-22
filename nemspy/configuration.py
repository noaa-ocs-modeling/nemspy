from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
import os
from os import PathLike
from pathlib import Path
import sys
from textwrap import indent
from typing import Iterator, List, Tuple, Union

if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata

from nemspy.model.base import (
    AttributeEntry,
    ConnectionEntry,
    EntryType,
    FileForcingEntry,
    GridRemapMethod,
    INDENTATION,
    MediationEntry,
    MediatorEntry,
    ModelEntry,
    SequenceEntry,
    VerbosityOption,
)
from nemspy.utilities import create_symlink, LOGGER


class Earth(AttributeEntry):
    """
    multi-model coupling container representing the entire Earth system

    Only one of each model type can be assigned to the Earth system model at a time.
    """

    entry_title = 'EARTH'

    def __init__(self, **models):
        """
        :param atm: atmospheric wind model
        :param wav: oceanic wave model
        :param ocn: oceanic circulation model
        :param hyd: terrestrial water model
        :param med: model mediator
        """

        if 'Verbosity' not in models:
            models['Verbosity'] = VerbosityOption.OFF

        self.__models = {model_type: None for model_type in EntryType}

        attributes = {}
        for key, value in models.items():
            if key.upper() in {entry.name for entry in EntryType}:
                if isinstance(value, ModelEntry):
                    self[EntryType[key.upper()]] = value
            else:
                attributes[key] = value
        self.attributes = attributes

    @property
    def models(self):
        """
        list of models comprising the Earth system
        """

        return self.__models

    def __getitem__(self, model_type: EntryType) -> ModelEntry:
        return self.__models[model_type]

    def __setitem__(self, model_type: EntryType, model: ModelEntry):
        assert model_type == model.entry_type
        if self.__models[model_type] is not None:
            LOGGER.warning(
                f'overwriting existing "{model_type.name}" model: ' f'{repr(self[model_type])}'
            )
        self.__models[model_type] = model

    def __contains__(self, model_type: EntryType):
        return model_type in self.__models

    def __iter__(self) -> Iterator[Tuple[EntryType, ModelEntry]]:
        for model_type, model in self.models.items():
            yield model_type, model

    def __str__(self) -> str:
        attributes = [
            f'{attribute} = {value if not isinstance(value, Enum) else value.value}'
            for attribute, value in self.attributes.items()
        ]

        return '\n'.join(
            [
                f'{self.entry_title}_component_list: '
                f'{" ".join(model_type.value for model_type, model in self.models.items() if model is not None)}',
                f'{self.entry_title}_attributes::',
                indent('\n'.join(attributes), INDENTATION),
                '::',
            ]
        )

    def __repr__(self) -> str:
        models = [
            f'{model_type.name}={repr(model)}' for model_type, model in self.models.items()
        ]
        models += [f'{key}={value}' for key, value in self.attributes.items()]
        return (
            f'{self.__class__.__name__}({self.attributes["Verbosity"]}, {", ".join(models)})'
        )


class RunSequence(AttributeEntry, SequenceEntry):
    """
    multi-model container for model entries, defining the sequence in which they run within the modeled time loop

    NOTE: Currently, only one loop is supported. Nested loops will be implemented in a future version of NEMSpy.
    """

    entry_title = 'Run Sequence'

    def __init__(self, interval: timedelta, **kwargs):
        """
        :param interval: time interval to repeat the main loop in modeled time
        """

        self.interval = interval

        if 'Verbosity' not in kwargs:
            kwargs['Verbosity'] = VerbosityOption.OFF

        self.__models = {}
        attributes = {}
        for key, value in kwargs.items():
            model_types = [model_type.value for model_type in EntryType]
            if key.upper() in model_types and isinstance(value, ModelEntry):
                self.__models[EntryType(key.upper())] = value
            else:
                attributes[key] = value
        self.attributes = attributes

        self.__sequence = [
            model for model in self.models if model.entry_type != EntryType.MEDIATOR
        ]
        self.__link_models()

    def append(self, entry: SequenceEntry):
        """
        add a sequence entry
        """

        if isinstance(entry, ModelEntry):
            model_type = entry.entry_type
            if model_type in self.__models:
                del self.__models[model_type]
                self[entry.entry_type] = entry
        self.__sequence.append(entry)

    def extend(self, sequence: List[SequenceEntry]):
        """
        add several sequence entries
        """

        for entry in sequence:
            self.append(entry)

    @property
    def sequence(self) -> List[SequenceEntry]:
        """
        list of sequence entries in order, including model entries and connections / mediations
        """

        return self.__sequence

    @sequence.setter
    def sequence(self, sequence: List[SequenceEntry]):
        """
        set the sequence by passing a list of entries in order
        """

        sequence = list(sequence)
        if sequence != self.__sequence:
            mediator = self.mediator
            self.__models = {}
            if mediator is not None:
                self.mediator = mediator
            for entry in sequence:
                if isinstance(entry, ModelEntry):
                    model_type = entry.entry_type
                    if model_type in self.__models:
                        raise TypeError(
                            f'duplicate model type ' f'"{model_type.name}" in given sequence'
                        )
                    self.__models[model_type] = entry
            self.__link_models()
            self.__sequence = sequence

    def connect(
        self, source: EntryType, target: EntryType, method: GridRemapMethod = None, **kwargs,
    ):
        """
        assign a simple connection (not a mediation) between two model entries within the sequence
        """

        if method is None:
            method = GridRemapMethod.REDISTRIBUTE
        if EntryType.MEDIATOR in [source, target] and self.mediator is None:
            self.mediator = MediatorEntry(**kwargs)
        if source not in self.__models:
            raise KeyError(f'no {source.name} model in sequence')
        if target not in self.__models:
            raise KeyError(f'no {target.name} model in sequence')
        self.append(ConnectionEntry(self[source], self[target], method))

    @property
    def connections(self) -> List[Union[ConnectionEntry, MediationEntry]]:
        """
        list of all connections in the sequence
        """

        return [
            entry
            for entry in self.sequence
            if isinstance(entry, ConnectionEntry) or isinstance(entry, MediationEntry)
        ]

    @property
    def mediator(self) -> MediatorEntry:
        """
        shortcut property to the mediator entry
        """

        if EntryType.MEDIATOR in self:
            return self.__models[EntryType.MEDIATOR]
        else:
            return None

    @mediator.setter
    def mediator(self, mediator: MediatorEntry):
        """
        set the mediator entry (does not exist in the sequence by itself)
        """

        self[EntryType.MEDIATOR] = mediator

    def mediate(
        self,
        sources: List[EntryType] = None,
        functions: List[str] = None,
        targets: List[EntryType] = None,
        method: GridRemapMethod = None,
        processors: int = None,
        **attributes,
    ):
        """
        assign a mediation between two entries in the sequence
        """

        if 'name' not in attributes:
            attributes['name'] = 'mediator'
        if self.mediator is None:
            self.mediator = MediatorEntry(processors=processors, **attributes)
        else:
            self.mediator.attributes.update(attributes)
        if processors is not None:
            # increase mediation processor assignment if required
            if self.mediator.processors < processors:
                self.mediator.processors = processors

        if sources is not None:
            sources = [self[source] for source in sources]
        if targets is not None:
            targets = [self[target] for target in targets]

        self.append(MediationEntry(self.mediator, sources, functions, targets, method))

    @property
    def mediations(self) -> List[MediationEntry]:
        """
        list of all mediations in the sequence
        """

        return [entry for entry in self.sequence if isinstance(entry, MediationEntry)]

    @property
    def earth(self) -> Earth:
        """
        Earth system assigned to the sequence
        """

        return Earth(
            **{model.entry_type.name: model for model in self.models}, **self.attributes
        )

    @property
    def processors(self) -> int:
        """
        total number of processors assigned to sequence entries
        """

        return sum(model.processors for model in self.__models.values())

    def __link_models(self):
        """
        link entries and assign processors
        """

        models = self.models
        for model in models:
            if model.previous is not None:
                model.previous.next = None
            if model.next is not None:
                model.next = None
            model.start_processor = 0
        for model_index, model in enumerate(models):
            previous_model_index = model_index - 1
            if previous_model_index >= 0:
                model.previous = models[previous_model_index]

    def __setitem__(self, model_type: EntryType, model: ModelEntry):
        assert model_type == model.entry_type
        if model_type in self.__models:
            existing_model = self.__models[model_type]
            LOGGER.warning(
                f'overwriting {model_type.name} model ' f'"{existing_model}" with "{model}"'
            )
            self.__sequence.remove(self.__sequence.index(existing_model))
        self.__models[model_type] = model
        self.__link_models()

    def __getitem__(self, model_type: EntryType) -> ModelEntry:
        return self.__models[model_type]

    @property
    def models(self) -> List[ModelEntry]:
        """
        list of models in the run sequence
        """

        models = [
            model
            for model_type, model in self.__models.items()
            if model_type in self and model_type is not EntryType.MEDIATOR
        ]
        if self.mediator is not None:
            models.insert(0, self.mediator)
        return models

    def __iter__(self) -> Iterator[ModelEntry]:
        for model in self.models:
            yield model

    def __contains__(self, model_type: EntryType) -> bool:
        return model_type in self.__models

    def __len__(self) -> int:
        return len(self.sequence)

    @property
    def sequence_entry(self) -> str:
        return str(self)

    def __str__(self) -> str:
        block = '\n'.join(
            [
                f'@{self.interval / timedelta(seconds=1):.0f}',
                indent(
                    '\n'.join(entry.sequence_entry for entry in self.__sequence), INDENTATION
                ),
                '@',
            ]
        )
        return '\n'.join([f'runSeq::', indent(block, INDENTATION), '::'])

    def __repr__(self) -> str:
        models = [f'{model.entry_type.name.lower()}={repr(model)}' for model in self.models]
        return f'{self.__class__.__name__}({repr(self.interval)}, {", ".join(models)})'


class ConfigurationFile(ABC):
    """
    abstraction of a configuration file
    """

    name: str = NotImplementedError

    def __init__(self, sequence: RunSequence):
        """
        :param sequence: run sequence object containing models and order
        """

        self.sequence = sequence

    def __getitem__(self, entry_type: type) -> List[AttributeEntry]:
        return [entry for entry in self if isinstance(entry, entry_type)]

    @property
    def version_header(self) -> str:
        """
        comment header indicating filename and NEMSpy version
        """

        installed_distributions = importlib_metadata.distributions()
        for distribution in installed_distributions:
            if (
                distribution.metadata['Name'] is not None
                and distribution.metadata['Name'].lower() == 'nemspy'
            ):
                version = distribution.version
                break
        else:
            version = 'unknown'
        return f'# `{self.name}` generated with NEMSpy {version}'

    def write(
        self, filename: PathLike, overwrite: bool = False, include_version: bool = False
    ) -> Path:
        """
        write this configuration to file

        :param filename: path to file
        :param overwrite: overwrite an existing file
        :param include_version: include NEMSpy version information
        :returns: path to written file
        """

        if not isinstance(filename, Path):
            filename = Path(filename)
        ensure_directory(filename.parent)

        output = f'{self}\n'
        if include_version:
            output = f'{self.version_header}\n' f'{output}'

        if filename.is_dir():
            filename = filename / self.name
            LOGGER.warning(
                f'creating new file "{os.path.relpath(filename.resolve(), Path.cwd())}"'
            )

        if filename.exists():
            LOGGER.warning(
                f'{"overwriting" if overwrite else "skipping"} existing file "{os.path.relpath(filename.resolve(), Path.cwd())}"'
            )
        if not filename.exists() or overwrite:
            with open(filename, 'w', newline='\n') as output_file:
                output_file.write(output)

        return filename

    @abstractmethod
    def __str__(self) -> str:
        """
        :returns: string representation of configuration file
        """

        raise NotImplementedError

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.sequence)})'


class NEMSConfigurationFile(ConfigurationFile):
    """
    ``nems.configure`` file, containing NEMS members, coupling connections, and run sequence information
    """

    name = 'nems.configure'

    @property
    def entries(self) -> List[AttributeEntry]:
        """
        list of attributed configuration entries, including the Earth system, models, and run sequence
        """

        return [self.sequence.earth, *self.sequence.models, self.sequence]

    def __iter__(self) -> Iterator[AttributeEntry]:
        for entry in self.entries:
            yield entry

    def __str__(self) -> str:
        return '\n'.join(f'# {entry.entry_title} #\n' f'{entry}\n' for entry in self).strip()


class FileForcingsFile(ConfigurationFile):
    """
    ``config.rc`` file, containing paths to forcing files
    """

    name = 'config.rc'

    @property
    def entries(self) -> List[FileForcingEntry]:
        """
        list of file forcing entries
        """

        return [entry for entry in self.sequence if isinstance(entry, FileForcingEntry)]

    def __iter__(self) -> Iterator[AttributeEntry]:
        for entry in self.entries:
            yield entry

    def __str__(self) -> str:
        return '\n'.join([FileForcingEntry.__str__(model_mesh) for model_mesh in self])


class ModelConfigurationFile(ConfigurationFile):
    """
    ``model_configure`` file, containing information on modeled start and end times, as well as ensemble information also aliased to ``atm_namelist.rc``
    """

    name = 'model_configure'

    def __init__(
        self,
        start_time: datetime,
        duration: timedelta,
        sequence: RunSequence,
        create_atm_namelist_rc: bool = True,
    ):
        """
        :param start_time: start time in model time
        :param duration: duration in model time
        :param sequence: run sequence containing models, connections, and order
        :param create_atm_namelist_rc: whether to create a symlink to ``atm_namelist.rc``
        """

        self.start_time = start_time
        self.duration = duration
        self.create_atm_namelist_rc = create_atm_namelist_rc
        super().__init__(sequence)

    def write(
        self, filename: PathLike, overwrite: bool = False, include_version: bool = False,
    ) -> Path:
        filename = super().write(filename, overwrite, include_version)
        if self.create_atm_namelist_rc:
            create_symlink(filename, filename.parent / 'atm_namelist.rc', relative=True)
        return filename

    def __str__(self) -> str:
        duration_hours = round(self.duration / timedelta(hours=1))
        return '\n'.join(
            [
                'total_member:            1',
                'print_esmf:              .true.',
                f'namelist:                {"atm_namelist.rc" if self.create_atm_namelist_rc else "model_configure"}',
                f'PE_MEMBER01:             {self.sequence.processors}',
                f'start_year:              {self.start_time.year}',
                f'start_month:             {self.start_time.month}',
                f'start_day:               {self.start_time.day}',
                f'start_hour:              {self.start_time.hour}',
                f'start_minute:            {self.start_time.minute}',
                f'start_second:            {self.start_time.second}',
                f'nhours_fcst:             {duration_hours:.0f}',
                'RUN_CONTINUE:            .false.',
                'ENS_SPS:                 .false.',
                # 'dt_atmos:                   @[DT_ATMOS]'
                # 'atm_coupling_interval_sec:  @[coupling_interval_fast_sec]'
                #
                # 'iatm: @[IATM]'
                # 'jatm: @[JATM]'
                #
                # 'cdate0: @[CDATE]'
                # 'nfhout: @[NFHOUT]'
                # 'filename_base: @[FILENAME_BASE]'
            ]
        )


def ensure_directory(directory: PathLike) -> Path:
    """
    ensure that a directory exists

    :param directory: directory path to ensure
    :returns: path to ensured directory
    """

    if not isinstance(directory, Path):
        directory = Path(directory)
    directory = directory.expanduser()
    if directory.is_file():
        directory = directory.parent
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
    return directory
