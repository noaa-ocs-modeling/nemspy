from abc import ABC, abstractmethod
from enum import Enum
from os import PathLike
from pathlib import PurePosixPath
from textwrap import indent
from typing import Dict, List

INDENTATION = '  '


class EntryType(Enum):
    """
    possible types of a configuration entry
    """

    ATMOSPHERIC = 'ATM'
    WAVE = 'WAV'
    OCEAN = 'OCN'
    HYDROLOGICAL = 'HYD'
    ICE = 'ICE'
    MEDIATOR = 'MED'


class VerbosityOption(Enum):
    """
    possible verbosity options for model entries
    """

    OFF = 'off'
    LOW = 'low'
    HIGH = 'high'
    MAX = 'max'


class GridRemapMethod(Enum):
    """
    possible remapping methods (interpolation / redistribution) for translating coupled data from one grid to another
    """

    REDISTRIBUTE = 'redist'
    BILINEAR = 'bilinear'
    PATH = 'patch'
    NEAREST_STOD = 'nearest_stod'
    NEAREST_DTOS = 'nearest_dtos'
    CONSERVE = 'conserve'


class FileForcingEntry(ABC):
    """
    abstraction of a forcing entry in ``config.rc``, defining the file path to a forcing file
    """

    def __init__(self, entry_type: EntryType, filename: PathLike = None):
        """
        :param entry_type: type of file forcing (i.e. ``ATM``, ``ICE``, etc.)
        :param filename: path to file
        """

        if filename is not None and not isinstance(filename, PurePosixPath):
            filename = PurePosixPath(filename)

        self.mesh_type = entry_type
        self.filename = filename

    def __str__(self) -> str:
        """
        string representation of the forcing entry in ``config.rc``
        """

        if self.filename is not None:
            directory = self.filename.parent.as_posix()
            name = self.filename.name
        else:
            directory = ''
            name = ''

        return (
            f' {self.mesh_type.value.lower()}_dir: {directory}\n'
            f' {self.mesh_type.value.lower()}_nam: {name}'
        )


class ConfigurationEntry(ABC):
    """
    abstraction of an entry in a configuration file
    """

    @classmethod
    @abstractmethod
    def from_string(cls, string: str, **kwargs) -> 'ConfigurationEntry':
        """
        parse entry information from a configuration entry string
        """

        raise NotImplementedError


class AttributeEntry(ABC):
    """
    abstraction of a configuration entry in ``nems.configure``
    """

    entry_title: str = NotImplementedError
    __attributes: Dict[str, str] = NotImplementedError

    @abstractmethod
    def __str__(self) -> str:
        """
        string representation of the configuration entry in ``nems.configure``
        """

        raise NotImplementedError

    @property
    def attributes(self) -> Dict[str, str]:
        """
        attributes defining options for the configuration entry, such as verbosity
        """

        attributes = {}
        for attribute, value in self.__attributes.items():
            if isinstance(value, Enum):
                value = value.value
            elif isinstance(value, bool):
                value = f'{value}'.lower()
            attributes[attribute] = value
        return attributes

    @attributes.setter
    def attributes(self, attributes: Dict[str, str]):
        self.__attributes = attributes


class SequenceEntry(ABC):
    """
    abstraction of an entry within the run sequence in ``nems.configure``
    """

    @property
    @abstractmethod
    def sequence_entry(self) -> str:
        """
        string representation of the sequence entry in ``nems.configure``
        """

        raise NotImplementedError

    def __str__(self) -> str:
        return self.sequence_entry


class ModelEntry(AttributeEntry, SequenceEntry, ConfigurationEntry):
    """
    abstraction of a generic model implementing NEMS / NUOPC coupling
    """

    entry_type: EntryType
    name: str

    def __init__(self, processors: int, **attributes):
        """
        The model entry is represented in two places in ``nems.configure``: once as a configuration entry with attributes, and once in the run sequence.
        The specific processors assigned to the model are defined by start and stop indices, which are determined on configuration write from the stop index of the previous entry in the run sequence.

        :param processors: number of processors to assign to this model
        """

        self.__processors = processors

        self.__start_processor = None

        self.__previous = None
        self.__next = None

        if 'Verbosity' not in attributes:
            attributes['Verbosity'] = VerbosityOption.OFF

        # http://www.earthsystemmodeling.org/esmf_releases/last_built/NUOPC_refdoc/node3.html#SECTION00033000000000000000
        self.attributes = attributes

    @property
    def entry_title(self) -> str:
        return str(self.entry_type.value) if self.entry_type is not None else None

    @property
    def processors(self) -> int:
        """
        the number of processors assigned to this model
        """

        return self.__processors

    @processors.setter
    def processors(self, processors: int):
        """
        set the number of processors (this also updates all subsequent entries in the run sequence)
        """

        if processors != self.processors:
            self.__processors = processors
            # update following processors
            self.start_processor = self.start_processor

    @property
    def start_processor(self) -> int:
        """
        the first index in the processor series assigned to this model
        """

        return self.__start_processor

    @start_processor.setter
    def start_processor(self, index: int):
        """
        set the first index in the processor series (this also updates all subsequent entries in the run sequence)
        """

        self.__start_processor = index
        current_model = self.next
        while current_model is not None:
            if current_model.previous is not None:
                current_model.__start_processor = current_model.previous.end_processor + 1
            current_model = current_model.next

    @property
    def end_processor(self) -> int:
        """
        the last index in the processor series assigned to this model
        """

        if self.start_processor is not None:
            return self.start_processor + self.processors - 1
        else:
            return None

    @property
    def previous(self) -> 'ModelEntry':
        """
        the previous entry in the run sequence
        """

        return self.__previous

    @previous.setter
    def previous(self, previous: 'ModelEntry'):
        """
        assign the previous entry in the run sequence (this also updates the processor series for this and all subsequent entries in the run sequence)
        """

        if previous is None and self.previous is not None:
            self.previous.__next = None
        self.__previous = previous
        if self.previous is not None:
            self.previous.__next = self
            if self.previous.end_processor is not None:
                self.start_processor = self.previous.end_processor + 1
        else:
            self.start_processor = 0

    @property
    def next(self) -> 'ModelEntry':
        """
        the next entry in the run sequence
        """

        return self.__next

    @next.setter
    def next(self, next: 'ModelEntry'):
        """
        assign the next entry in the run sequence (this updates all subsequent entries in the run sequence)
        """

        if next is None and self.next is not None:
            self.next.__previous = None
        self.__next = next
        if self.next is not None:
            self.next.__previous = self

    @property
    def sequence_entry(self) -> str:
        return str(self.entry_type.value)

    def __str__(self) -> str:
        return '\n'.join(
            [
                f'{self.entry_type.value}_model:                      {self.name}',
                f'{self.entry_type.value}_petlist_bounds:             {self.start_processor} {self.end_processor}',
                f'{self.entry_type.value}_attributes::',
                indent(
                    '\n'.join(
                        [
                            f'{attribute} = {value}'
                            for attribute, value in self.attributes.items()
                        ]
                    ),
                    INDENTATION,
                ),
                '::',
            ]
        )

    def __repr__(self) -> str:
        kwargs = [f'{key}={value}' for key, value in self.attributes.items()]
        return f'{self.__class__.__name__}({repr(self.name)}, {self.entry_type}, {self.processors}, {", ".join(kwargs)})'

    @classmethod
    def from_string(cls, string: str, **kwargs) -> 'ModelEntry':
        lines = string.splitlines()

        parsed_model_type, parsed_name = (value.strip() for value in lines[0].split('_model:'))
        parsed_model_type = EntryType(parsed_model_type)

        if hasattr(cls, 'model_type'):
            assert parsed_model_type == cls.entry_type
        if hasattr(cls, 'name'):
            assert parsed_name == cls.name

        start_processor, end_processor = [
            int(entry) for entry in lines[1].split('_petlist_bounds:')[-1].strip().split()
        ]

        attributes = {}
        for attribute_line in lines[3:-1]:
            key, value = (value.strip() for value in attribute_line.split('='))
            attributes[key] = value

        instance = cls(processors=end_processor + 1 - start_processor, **attributes, **kwargs,)

        if not hasattr(cls, 'model_type'):
            instance.entry_type = parsed_model_type
        if not hasattr(cls, 'name'):
            instance.name = parsed_name

        return instance


class ConnectionEntry(SequenceEntry, ConfigurationEntry):
    """
    a connection entry in ``nems.configure`` representing a simple coupling between two model entries
    """

    def __init__(self, source: ModelEntry, target: ModelEntry, method: GridRemapMethod = None):
        """
        :param source: source model entry
        :param target: target model entry
        :param method: remapping method with which to translate between differing grids (use ``redist`` for the same grid)
        """

        self.source = source
        self.target = target
        self.method = method if method is not None else GridRemapMethod.BILINEAR

    @property
    def models(self) -> List[ModelEntry]:
        """
        the source and target models in the coupling
        """

        return [self.source, self.target]

    @property
    def sequence_entry(self) -> str:
        return (
            f'{self.source.entry_type.value} -> {self.target.entry_type.value}'.ljust(13)
            + f':remapMethod={self.method.value}'
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.source)}, {repr(self.target)}, {repr(self.method)})'

    @classmethod
    def from_string(cls, string: str, **kwargs) -> 'ConnectionEntry':
        method = None
        try:
            source, target = (entry.strip() for entry in string.split('->', 1))
        except ValueError:
            raise ValueError(
                'connection entry should be formatted as `SRC -> DST   :remapMethod=METHOD`'
            )

        if ':' in target:
            target, parsed_method = (entry.strip() for entry in target.split(':', 1))
            if method is None and len(parsed_method) > 0:
                method = GridRemapMethod(parsed_method.split('=')[-1])

        source_model = ModelEntry(None)
        target_model = ModelEntry(None)

        source_model.name = source
        source_model.entry_type = EntryType(source)
        target_model.name = target
        target_model.entry_type = EntryType(target)

        return cls(source=source_model, target=target_model, method=method)


class MediatorEntry(ModelEntry):
    """
    a special entry in ``nems.configure`` representing a coupler between two model entries with a dedicated coupling function
    """

    entry_type = EntryType.MEDIATOR
    name = 'implicit'

    def __init__(self, processors: int = None, **attributes):
        """
        :param processors: number of processors to assign to this mediator
        """

        if processors is None:
            processors = 1
        super().__init__(processors, **attributes)


class MediationFunctionEntry(SequenceEntry, ConfigurationEntry):
    """
    the dedicated function of a mediation entry, applied to the coupling between two model entries in ``nems.configure``
    """

    def __init__(self, name: str, mediator: MediatorEntry):
        """
        :param name: name of function
        :param mediator: mediator entry to host this function
        """

        self.name = name
        self.mediator = mediator

    @property
    def sequence_entry(self) -> str:
        return f'{self.mediator.entry_type.value} {self.name}'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.name)}, {repr(self.mediator)})'

    @classmethod
    def from_string(cls, string: str, **kwargs) -> 'MediationFunctionEntry':
        """
        parse entry information from a configuration entry string
        """

        mediator_name, function_name = string.split()
        return cls(name=function_name, mediator=MediatorEntry(mediator_name))


class MediationEntry(SequenceEntry, ConfigurationEntry):
    """
    an application of a mediator between model entries, with a dedicated coupling function
    """

    def __init__(
        self,
        mediator: MediatorEntry,
        sources: List[ModelEntry] = None,
        functions: List[str] = None,
        targets: List[ModelEntry] = None,
        method: GridRemapMethod = None,
    ):
        """
        A Mediation can include multiple connections; for instance, an ICE model might connect to the mediation function, then the mediation function connects to the OCN model.

        :param mediator: mediator entry to host this mediation
        :param sources: source models
        :param functions: mediation functions to use
        :param targets: target models
        :param method: remapping method with which to translate between differing grids (use ``redist`` for the same grid)
        """

        if functions is None:
            functions = []

        self.mediator = mediator
        self.functions = [
            MediationFunctionEntry(mediation_function, self.mediator)
            for mediation_function in functions
        ]

        self.sources = sources
        self.targets = targets
        self.method = method

    @property
    def source_connections(self) -> List[ConnectionEntry]:
        """
        list of connections between the source(s) and the mediator
        """

        source_connections = []
        if self.sources is not None:
            for index, source in enumerate(self.sources):
                source_connections.append(ConnectionEntry(source, self.mediator, self.method))
        return source_connections

    @property
    def target_connections(self) -> List[ConnectionEntry]:
        """
        list of connections between the mediator and the target(s)
        """

        target_connections = []
        if self.targets is not None:
            for index, target in enumerate(self.targets):
                target_connections.append(ConnectionEntry(self.mediator, target, self.method))
        return target_connections

    @property
    def models(self) -> List[ModelEntry]:
        """
        list of model entries involved in the mediation
        """

        return [
            *(connection.source for connection in self.source_connections),
            self.mediator,
            *(connection.target for connection in self.target_connections),
        ]

    @property
    def sequence_entry(self) -> str:
        return '\n'.join(
            (
                *(
                    source_connection.sequence_entry
                    for source_connection in self.source_connections
                ),
                *(mediation_function.sequence_entry for mediation_function in self.functions),
                *(
                    target_connection.sequence_entry
                    for target_connection in self.target_connections
                ),
            )
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.mediator)}, {repr(self.sources)}, {repr(self.functions)}, {repr(self.targets)}, {repr(self.method)})'

    @classmethod
    def from_string(cls, string: str, **kwargs) -> 'MediationEntry':
        lines = string.strip().splitlines()

        connections = []
        functions = []
        for line in lines:
            if len(line) > 0:
                if '->' in line:
                    parts = [entry.strip() for entry in line.split('->')]
                    method = None
                    if ':' in parts[-1]:
                        parts[-1], method = [
                            entry.strip() for entry in parts[-1].split(':remapMethod=')
                        ]
                    if len(parts) == 2:
                        connection = ConnectionEntry.from_string(line)
                    else:
                        connection = ConnectionEntry(
                            source=parts[0], target=parts[-1], method=method
                        )
                    connections.append(connection)
                else:
                    functions.append(MediationFunctionEntry.from_string(line))

        mediator = None
        function_names = []
        for function in functions:
            if mediator is None:
                mediator = function.mediator
            function_names.append(function.name)

        method = None
        sources = []
        targets = []
        for connection in connections:
            if method is None:
                method = connection.method
            if connection.source.name != mediator.name:
                sources.append(connection.source)
            if connection.target.name != mediator.name:
                targets.append(connection.target)

        return cls(
            mediator=mediator,
            sources=sources,
            functions=function_names,
            targets=targets,
            method=method,
        )
