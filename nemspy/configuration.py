from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from os import PathLike
from pathlib import Path
from textwrap import indent
from typing import Iterator, Tuple

from .model.base import ConfigurationEntry, Connection, INDENTATION, \
    Model, ModelMesh, ModelType, ModelVerbosity, RemapMethod
from .utilities import get_logger

LOGGER = get_logger('configuration')


class EarthEntry(ConfigurationEntry):
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
                if isinstance(value, Model):
                    self[ModelType[key]] = value
            else:
                self.attributes[key] = value

        self.attributes['Verbosity'] = verbosity

    @property
    def models(self):
        return self.__models

    def __getitem__(self, model_type: ModelType) -> Model:
        return self.__models[model_type]

    def __setitem__(self, model_type: ModelType, model: Model):
        assert model_type == model.model_type
        if self.__models[model_type] is not None:
            LOGGER.warning(f'overwriting existing "{model_type.name}" model: '
                           f'{repr(self[model_type])}')
        self.__models[model_type] = model

    def __contains__(self, model_type: ModelType):
        return model_type in self.__models

    def __iter__(self) -> Iterator[Tuple[ModelType, Model]]:
        for model_type, model in self.models.items():
            yield model_type, model

    def __str__(self) -> str:
        attributes = [
            f'{attribute} = {value if not isinstance(value, Enum) else value.value}'
            for attribute, value in self.attributes.items()
        ]

        return '\n'.join([
            f'{self.entry_type}_component_list: {" ".join(model_type.value for model_type, model in self.models.items() if model is not None)}',
            f'{self.entry_type}_attributes::',
            indent('\n'.join(attributes), INDENTATION),
            '::'
        ])

    def __repr__(self) -> str:
        kwargs = [f'{model_type.name}={repr(model)}'
                  for model_type, model in self.models.items()] + \
                 [f'{key}={value}'
                  for key, value in self.attributes.items()]
        return f'{self.__class__.__name__}({self.attributes["Verbosity"]}, {", ".join(kwargs)})'


class ModelSequence(ConfigurationEntry):
    entry_type = 'Run Sequence'

    def __init__(self, interval: timedelta, verbose: bool = False, **kwargs):
        self.interval = interval
        self.verbosity = ModelVerbosity.MAXIMUM if verbose else ModelVerbosity.MINIMUM

        self.__models = {}
        for key, value in kwargs.items():
            key = key.upper()
            if key in {entry.name for entry in ModelType} and \
                    isinstance(value, Model):
                self[ModelType[key]] = value
            elif key == 'EARTH' and isinstance(value, EarthEntry):
                for model_type, model in value:
                    self[model_type] = model

        self.connections = []
        self.__sequence()

    @property
    def entries(self) -> [Model]:
        return [model for model_type, model in self.__models.items()
                if model_type in self]

    @property
    def sequence(self):
        return list(self.__models)

    @sequence.setter
    def sequence(self, sequence: [ModelType]):
        if sequence != list(self.__models):
            if len(sequence) != len(self):
                raise ValueError(f'given length {len(sequence)} differs from '
                                 f'sequence length {len(self)}')
            for model_type in sequence:
                if model_type not in self:
                    raise ValueError(f'{model_type} not in sequence '
                                     f'{self.sequence}')
            models = self.__models
            self.__models = {model_type: models[model_type]
                             for model_type in sequence}
            self.__sequence()

    def connect(self, source: ModelType, destination: ModelType,
                method: RemapMethod = None):
        if method is None:
            method = RemapMethod.REDISTRIBUTE
        if source not in self.__models:
            raise ValueError(f'no {source.name} model in sequence')
        if destination not in self.__models:
            raise ValueError(f'no {destination.name} model in sequence')
        self.connections.append(Connection(source, destination, method))

    @property
    def earth(self) -> EarthEntry:
        return EarthEntry(self.verbosity, **{model.model_type.name: model
                                             for model in self.entries})

    def append(self, model: Model):
        if model is not None:
            if len(self.entries) > 0:
                self.entries[-1].next = model
            self[model.model_type] = model

    @property
    def processors(self) -> int:
        return sum(model.processors for model in self.__models.values())

    def __sequence(self):
        """ link entries and assign processors """
        models = self.entries
        for model_index, model in enumerate(models):
            if model_index == 0 and model.previous is not None:
                model.previous.next = None
                model.previous = None
            if model_index == len(self) and model.next is not None:
                model.next.previous = None
                model.next = None
            next_model_index = model_index + 1
            if next_model_index < len(self):
                model.next = models[next_model_index]

    def __getitem__(self, model_type: ModelType) -> Model:
        return self.__models[model_type]

    def __setitem__(self, model_type: ModelType, model: Model):
        assert model_type == model.model_type
        if model_type in self.__models:
            LOGGER.warning(f'overwriting existing "{model_type.name}" model')
        self.__models[model_type] = model
        self.__sequence()

    def __contains__(self, model_type: ModelType):
        return model_type in self.__models

    def __iter__(self) -> Iterator[Model]:
        for model in self.entries:
            yield model

    def __len__(self) -> int:
        return len(self.entries)

    def __str__(self) -> str:
        block = '\n'.join(
            [str(connection) for connection in self.connections] + \
            [model_type.value for model_type in self.__models])
        block = '\n'.join([
            f'@{self.interval / timedelta(seconds=1):.0f}',
            indent(block, INDENTATION),
            '@'
        ])
        return '\n'.join([
            f'runSeq::',
            indent(block, INDENTATION),
            '::'
        ])

    def __repr__(self) -> str:
        models = [f'{model.model_type.name.lower()}={repr(model)}'
                  for model in self.entries]
        return f'{self.__class__.__name__}({repr(self.interval)}, {", ".join(models)})'


class ConfigurationFile(ABC):
    name: str = NotImplementedError

    def __init__(self, sequence: ModelSequence):
        self.sequence = sequence

    def __getitem__(self, entry_type: type) -> [ConfigurationEntry]:
        return [entry for entry in self if isinstance(entry, entry_type)]

    @abstractmethod
    def write(self, directory: PathLike, overwrite: bool = False):
        raise NotImplementedError

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.sequence)})'


class NEMSConfigurationFile(ConfigurationFile):
    name = 'nems.configure'

    def write(self, directory: PathLike, overwrite: bool = False):
        if not isinstance(directory, Path):
            directory = Path(directory)

        directory = directory.expanduser()

        filename = directory / self.name

        if filename.exists():
            LOGGER.warning(f'{"overwriting" if overwrite else "skipping"} '
                           f'existing file "{filename}"')
        if not filename.exists() or overwrite:
            LOGGER.debug(f'writing NEMS configuration to "{filename}"')
            with open(filename, 'w') as output_file:
                output_file.write(str(self))

    def __iter__(self) -> Iterator[ConfigurationEntry]:
        for entry in [self.sequence.earth, *self.sequence.entries,
                      self.sequence]:
            yield entry

    def __str__(self) -> str:
        return '#############################################\n' \
               '####  NEMS Run-Time Configuration File  #####\n' \
               '#############################################\n' \
               '\n' + \
               '\n'.join(f'# {entry.entry_type} #\n'
                         f'{entry}\n'
                         for entry in self)


class MeshFile(ConfigurationFile):
    name = 'config.rc'

    def write(self, directory: PathLike, overwrite: bool = False):
        if not isinstance(directory, Path):
            directory = Path(directory)

        directory = directory.expanduser()

        filename = directory / self.name

        if filename.exists():
            LOGGER.warning(f'{"overwriting" if overwrite else "skipping"} '
                           f'existing file "{filename}"')
        if not filename.exists() or overwrite:
            LOGGER.debug(f'writing mesh filenames to "{filename}"')
            with open(filename, 'w') as output_file:
                output_file.write(str(self))

    def __iter__(self) -> Iterator[ModelMesh]:
        for entry in [entry for entry in self.sequence
                      if isinstance(entry, ModelMesh)]:
            yield entry

    def __str__(self) -> str:
        return '\n'.join([ModelMesh.__str__(model_mesh)
                          for model_mesh in self]) + '\n'


class ModelConfigurationFile(ConfigurationFile):
    name = 'model_configure'

    def __init__(self, start_time: datetime, duration: timedelta,
                 sequence: ModelSequence):
        self.start_time = start_time
        self.duration = duration
        super().__init__(sequence)

    def write(self, directory: PathLike, overwrite: bool = False):
        if not isinstance(directory, Path):
            directory = Path(directory)

        directory = directory.expanduser()

        filename = directory / self.name

        if filename.exists():
            LOGGER.warning(f'{"overwriting" if overwrite else "skipping"} '
                           f'existing file "{filename}"')
        if not filename.exists() or overwrite:
            LOGGER.debug(f'writing model configuration to "{filename}"')
            with open(filename, 'w') as output_file:
                output_file.write(str(self))

        symbolic_link_filename = directory / 'atm_namelist.rc'
        try:
            symbolic_link_filename.symlink_to(filename)
        except Exception as error:
            LOGGER.warning(f'could not create symbolic link: {error}')
            with open(symbolic_link_filename, 'w') as output_file:
                output_file.write(str(self))

    def __str__(self) -> str:
        duration_hours = round(self.duration / timedelta(hours=1))
        return '\n'.join([
            'core: gfs',
            'print_esmf:     .true.',
            '',
            'nhours_dfini=0',
            '',
            '#nam_atm +++++++++++++++++++++++++++',
            'nlunit:                  35',
            'deltim:                  900.0',
            'fhrot:                   0',
            'namelist:                atm_namelist',
            'total_member:            1',
            'grib_input:              0',
            f'PE_MEMBER01:             {self.sequence.processors}',
            'PE_MEMBER02',
            'PE_MEMBER03',
            'PE_MEMBER04',
            'PE_MEMBER05',
            'PE_MEMBER06',
            'PE_MEMBER07',
            'PE_MEMBER08',
            'PE_MEMBER09',
            'PE_MEMBER10',
            'PE_MEMBER11',
            'PE_MEMBER12',
            'PE_MEMBER13',
            'PE_MEMBER14',
            'PE_MEMBER15',
            'PE_MEMBER16',
            'PE_MEMBER17',
            'PE_MEMBER18',
            'PE_MEMBER19:',
            'PE_MEMBER20:',
            'PE_MEMBER21:',
            '',
            '# For stochastic perturbed runs -  added by Dhou and Wyang',
            '--------------------------------------------------------',
            '#  ENS_SPS, logical control for application of stochastic perturbation scheme',
            '#  HH_START, start hour of forecast, and modified ADVANCECOUNT_SETUP',
            '#  HH_INCREASE and HH_FINAL are fcst hour increment and end hour of forecast',
            '#  ADVANCECOUNT_SETUP is an integer indicating the number of time steps between integration_start and the time when model state is saved for the _ini of the GEFS_Coupling, currently is 0h.',
            '',
            'HH_INCREASE:             600',
            'HH_FINAL:                600',
            'HH_START:                0',
            'ADVANCECOUNT_SETUP:      0',
            '',
            'ENS_SPS:                 .false.',
            'HOUTASPS:                10000',
            '',
            '#ESMF_State_Namelist +++++++++++++++',
            '',
            'RUN_CONTINUE:            .false.',
            '',
            '#',
            'dt_int:                  900',
            'dt_num:                  0',
            'dt_den:                  1',
            f'start_year:              {self.start_time.year}',
            f'start_month:             {self.start_time.month}',
            f'start_day:               {self.start_time.day}',
            f'start_hour:              {self.start_time.hour}',
            f'start_minute:            {self.start_time.minute}',
            f'start_second:            {self.start_time.second}',
            f'nhours_fcst:             {duration_hours:.0f}',
            'restart:                 .false.',
            f'nhours_fcst1:            {duration_hours:.0f}',
            'im:                      192',
            'jm:                      94',
            'global:                  .true.',
            'nhours_dfini:            0',
            'adiabatic:               .false.',
            'lsoil:                   4',
            'passive_tracer:          .true.',
            'dfilevs:                 64',
            'ldfiflto:                .true.',
            'num_tracers:             3',
            'ldfi_grd:                .false.',
            'lwrtgrdcmp:              .false.',
            'nemsio_in:               .false.',
            '',
            '',
            '#jwstart added quilt',
            '###############################',
            '#### Specify the I/O tasks ####',
            '###############################',
            '',
            '',
            'quilting:                .false.   #For asynchronous quilting/history writes',
            'read_groups:             0',
            'read_tasks_per_group:    0',
            'write_groups:            1',
            'write_tasks_per_group:   3',
            '',
            'num_file:                3                   #',
            'filename_base:           \'SIG.F\' \'SFC.F\' \'FLX.F\'',
            'file_io_form:            \'bin4\' \'bin4\' \'bin4\'',
            'file_io:                 \'DEFERRED\' \'DEFERRED\' \'DEFERRED\' \'DEFERRED\'  #',
            'write_dopost:            .false.          # True--> run do on quilt',
            'post_gribversion:        grib1      # True--> grib version for post output files',
            'gocart_aer2post:         .false.',
            'write_nemsioflag:        .TRUE.       # True--> Write nemsio run history files',
            'nfhout:                  3',
            'nfhout_hf:               1',
            'nfhmax_hf:               0',
            'nsout:                   0',
            '',
            'io_recl:                 100',
            'io_position:             \' \'',
            'io_action:               \'WRITE\'',
            'io_delim:                \' \'',
            'io_pad:                  \' \'',
            '',
            '#jwend'
        ])
