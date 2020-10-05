from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from os import PathLike, makedirs
from pathlib import Path
import shutil
from textwrap import indent
from typing import Iterator, Tuple

from dunamai import Version

from .model.base import (
    ConfigurationEntry,
    ConnectionEntry,
    INDENTATION,
    MediationEntry,
    MediatorEntry,
    ModelEntry,
    ModelMeshEntry,
    ModelType,
    ModelVerbosity,
    RemapMethod,
    SequenceEntry,
)
from .utilities import get_logger

LOGGER = get_logger('configuration')

__version__ = Version.from_git().serialize(dirty=True)


class Earth(ConfigurationEntry):
    """
    multi-model coupling container
    """

    entry_type = 'EARTH'

    def __init__(self, verbosity: ModelVerbosity = None, **kwargs):
        if verbosity is None:
            verbosity = ModelVerbosity.MINIMUM

        self.__models = {model_type: None for model_type in ModelType}

        self.attributes = {}
        for key, value in kwargs.items():
            key = key.upper()
            if key in {entry.name for entry in ModelType}:
                if isinstance(value, ModelEntry):
                    self[ModelType[key]] = value
            else:
                self.attributes[key] = value

        self.attributes['Verbosity'] = verbosity

    @property
    def models(self):
        return self.__models

    def __getitem__(self, model_type: ModelType) -> ModelEntry:
        return self.__models[model_type]

    def __setitem__(self, model_type: ModelType, model: ModelEntry):
        assert model_type == model.model_type
        if self.__models[model_type] is not None:
            LOGGER.warning(
                f'overwriting existing "{model_type.name}" model: ' f'{repr(self[model_type])}'
            )
        self.__models[model_type] = model

    def __contains__(self, model_type: ModelType):
        return model_type in self.__models

    def __iter__(self) -> Iterator[Tuple[ModelType, ModelEntry]]:
        for model_type, model in self.models.items():
            yield model_type, model

    def __str__(self) -> str:
        attributes = [
            f'{attribute} = {value if not isinstance(value, Enum) else value.value}'
            for attribute, value in self.attributes.items()
        ]

        return '\n'.join(
            [
                f'{self.entry_type}_component_list: '
                f'{" ".join(model_type.value for model_type, model in self.models.items() if model is not None)}',
                f'{self.entry_type}_attributes::',
                indent('\n'.join(attributes), INDENTATION),
                '::',
            ]
        )

    def __repr__(self) -> str:
        kwargs = [
                     f'{model_type.name}={repr(model)}' for model_type, model in self.models.items()
                 ] + [f'{key}={value}' for key, value in self.attributes.items()]
        return (
            f'{self.__class__.__name__}({self.attributes["Verbosity"]}, {", ".join(kwargs)})'
        )


class RunSequence(ConfigurationEntry, SequenceEntry):
    entry_type = 'Run Sequence'

    def __init__(self, interval: timedelta, verbose: bool = False, **kwargs):
        self.interval = interval
        self.verbosity = ModelVerbosity.MAXIMUM if verbose else ModelVerbosity.MINIMUM

        self.__models = {}
        for key, value in kwargs.items():
            key = key.upper()
            model_types = [model_type.value for model_type in ModelType]
            if key in model_types and isinstance(value, ModelEntry):
                self.__models[ModelType(key)] = value
            elif key == 'EARTH' and isinstance(value, Earth):
                for model_type, model in value:
                    self.__models[model_type] = model

        self.__sequence = [
            model for model in self.models if model.model_type != ModelType.MEDIATOR
        ]
        self.__link_models()

    def append(self, entry: SequenceEntry):
        if isinstance(entry, ModelEntry):
            model_type = entry.model_type
            if model_type in self.__models:
                del self.__models[model_type]
                self[entry.model_type] = entry
        self.__sequence.append(entry)

    def extend(self, sequence: [SequenceEntry]):
        for entry in sequence:
            self.append(entry)

    @property
    def sequence(self) -> [SequenceEntry]:
        return self.__sequence

    @sequence.setter
    def sequence(self, sequence: [SequenceEntry]):
        sequence = list(sequence)
        if sequence != self.__sequence:
            mediator = self.mediator
            self.__models = {}
            if mediator is not None:
                self.mediator = mediator
            for entry in sequence:
                if isinstance(entry, ModelEntry):
                    model_type = entry.model_type
                    if model_type in self.__models:
                        raise TypeError(
                            f'duplicate model type ' f'"{model_type.name}" in given sequence'
                        )
                    self.__models[model_type] = entry
            self.__link_models()
            self.__sequence = sequence

    def connect(
        self, source: ModelType, target: ModelType, method: RemapMethod = None, **kwargs
    ):
        if method is None:
            method = RemapMethod.REDISTRIBUTE
        if ModelType.MEDIATOR in [source, target] and self.mediator is None:
            self.mediator = MediatorEntry('implicit', **kwargs)
        if source not in self.__models:
            raise KeyError(f'no {source.name} model in sequence')
        if target not in self.__models:
            raise KeyError(f'no {target.name} model in sequence')
        self.append(ConnectionEntry(self[source], self[target], method))

    @property
    def connections(self) -> [ConnectionEntry]:
        return [entry for entry in self.sequence if isinstance(entry, ConnectionEntry)]

    @property
    def mediator(self) -> MediatorEntry:
        if ModelType.MEDIATOR in self:
            return self.__models[ModelType.MEDIATOR]
        else:
            return None

    @mediator.setter
    def mediator(self, mediator: MediatorEntry):
        self[ModelType.MEDIATOR] = mediator

    def mediate(
        self,
        source: ModelType = None,
        target: ModelType = None,
        functions: [str] = None,
        method: RemapMethod = None,
        processors: int = None,
        **attributes,
    ):
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

        if source is not None:
            source = self[source]
        if target is not None:
            target = self[target]

        self.append(MediationEntry(source, self.mediator, target, functions, method))

    @property
    def mediations(self) -> [MediationEntry]:
        return [entry for entry in self.sequence if isinstance(entry, MediationEntry)]

    @property
    def earth(self) -> Earth:
        return Earth(self.verbosity, **{model.model_type.name: model for model in self.models})

    @property
    def processors(self) -> int:
        return sum(model.processors for model in self.__models.values())

    def __link_models(self):
        """ link entries and assign processors """
        models = self.models
        for model in models:
            if model.previous is not None:
                model.previous.next = None
            if model.next is not None:
                model.next = None
        for model_index, model in enumerate(models):
            next_model_index = model_index + 1
            if next_model_index < len(models):
                model.next = models[next_model_index]
        models[0].start_processor = 0

    def __setitem__(self, model_type: ModelType, model: ModelEntry):
        assert model_type == model.model_type
        if model_type in self.__models:
            existing_model = self.__models[model_type]
            LOGGER.warning(
                f'overwriting {model_type.name} model ' f'"{existing_model}" with "{model}"'
            )
            self.__sequence.remove(self.__sequence.index(existing_model))
        self.__models[model_type] = model
        self.__link_models()

    def __getitem__(self, model_type: ModelType) -> ModelEntry:
        return self.__models[model_type]

    @property
    def models(self) -> [ModelEntry]:
        models = [
            model
            for model_type, model in self.__models.items()
            if model_type in self and model_type is not ModelType.MEDIATOR
        ]
        if self.mediator is not None:
            models.insert(0, self.mediator)
        return models

    def __iter__(self) -> Iterator[ModelEntry]:
        for model in self.models:
            yield model

    def __contains__(self, model_type: ModelType) -> bool:
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
        models = [f'{model.model_type.name.lower()}={repr(model)}' for model in self.models]
        return f'{self.__class__.__name__}({repr(self.interval)}, {", ".join(models)})'


class ConfigurationFile(ABC):
    name: str = NotImplementedError

    def __init__(self, sequence: RunSequence):
        self.sequence = sequence

    def __getitem__(self, entry_type: type) -> [ConfigurationEntry]:
        return [entry for entry in self if isinstance(entry, entry_type)]

    @property
    def version_header(self) -> str:
        return f'# `{self.name}` generated with NEMSpy {__version__}'

    def write(
        self, directory: PathLike, overwrite: bool = False, include_version: bool = True
    ) -> Path:
        output = f'{self}\n'
        if include_version:
            output = f'{self.version_header}\n{output}'

        directory = ensure_directory(directory)
        filename = directory / self.name

        if filename.exists():
            LOGGER.warning(
                f'{"overwriting" if overwrite else "skipping"} existing file "{filename}"'
            )
        if not filename.exists() or overwrite:
            with open(filename, 'w') as output_file:
                output_file.write(output)

        return filename

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.sequence)})'


class NEMSConfigurationFile(ConfigurationFile):
    name = 'nems.configure'

    @property
    def entries(self) -> [ConfigurationEntry]:
        return [self.sequence.earth, *self.sequence.models, self.sequence]

    def __iter__(self) -> Iterator[ConfigurationEntry]:
        for entry in self.entries:
            yield entry

    def __str__(self) -> str:
        return '\n'.join(f'# {entry.entry_type} #\n' f'{entry}\n' for entry in self).strip()


class MeshFile(ConfigurationFile):
    name = 'config.rc'

    @property
    def entries(self) -> [ModelMeshEntry]:
        return [entry for entry in self.sequence if isinstance(entry, ModelMeshEntry)]

    def __iter__(self) -> Iterator[ConfigurationEntry]:
        for entry in self.entries:
            yield entry

    def __str__(self) -> str:
        return '\n'.join([ModelMeshEntry.__str__(model_mesh) for model_mesh in self])


class ModelConfigurationFile(ConfigurationFile):
    name = 'model_configure'

    def __init__(self, start_time: datetime, duration: timedelta, sequence: RunSequence):
        self.start_time = start_time
        self.duration = duration
        super().__init__(sequence)

    def write(
        self, directory: PathLike, overwrite: bool = False, include_version: bool = True
    ):
        filename = super().write(directory, overwrite, include_version)
        symbolic_link_filename = filename.parent / 'atm_namelist.rc'

        try:
            symbolic_link_filename.symlink_to(filename)
        except Exception as error:
            LOGGER.warning(f'could not create symbolic link: {error}')
            shutil.copyfile(filename, symbolic_link_filename)

    def __str__(self) -> str:
        duration_hours = round(self.duration / timedelta(hours=1))
        return '\n'.join(
            [
                'total_member:            1',
                'print_esmf:              .true.',
                'namelist:                atm_namelist',
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
    if not isinstance(directory, Path):
        directory = Path(directory)
    directory = directory.expanduser()
    if directory.is_file():
        directory = directory.parent
    if not directory.exists():
        makedirs(directory, exist_ok=True)
    return directory
