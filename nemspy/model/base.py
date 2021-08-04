from abc import ABC, abstractmethod
from enum import Enum
from os import PathLike
from pathlib import PurePosixPath
from textwrap import indent

INDENTATION = '  '


class ModelType(Enum):
    """
    abbreviated model type within a NEMS / NUOPC configuration file
    """

    ATMOSPHERIC = 'ATM'
    WAVE = 'WAV'
    OCEAN = 'OCN'
    HYDROLOGICAL = 'HYD'
    ICE = 'ICE'
    MEDIATOR = 'MED'


class ModelVerbosity(Enum):
    """
    verbosity attribute within a NEMS / NUOPC configuration file
    """

    OFF = 'off'
    LOW = 'low'
    HIGH = 'high'
    MAX = 'max'


class RemapMethod(Enum):
    """
    model remapping methods
    """

    REDISTRIBUTE = 'redist'
    BILINEAR = 'bilinear'
    PATH = 'patch'
    NEAREST_STOD = 'nearest_stod'
    NEAREST_DTOS = 'nearest_dtos'
    CONSERVE = 'conserve'


class ModelMeshEntry(ABC):
    def __init__(self, mesh_type: ModelType, filename: PathLike = None):
        if filename is not None and not isinstance(filename, PurePosixPath):
            filename = PurePosixPath(filename)

        self.mesh_type = mesh_type
        self.filename = filename

    def __str__(self) -> str:
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
    NEMS / NUOPC configuration entry within `nems.configure`
    """

    entry_type: str = NotImplementedError
    __attributes: {str: str} = NotImplementedError

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError

    @property
    def attributes(self) -> {str: str}:
        attributes = {}
        for attribute, value in self.__attributes.items():
            if isinstance(value, Enum):
                value = value.value
            elif isinstance(value, bool):
                value = f'{value}'.lower()
            attributes[attribute] = value
        return attributes

    @attributes.setter
    def attributes(self, attributes: {str: str}):
        self.__attributes = attributes


class SequenceEntry(ABC):
    """
    entry within run sequence
    """

    @property
    @abstractmethod
    def sequence_entry(self) -> str:
        raise NotImplementedError

    def __str__(self) -> str:
        return self.sequence_entry


class ModelEntry(ConfigurationEntry, SequenceEntry):
    """
    abstract implementation of a generic model
    """

    model_type: ModelType
    name: str

    def __init__(self, processors: int, **attributes):
        self.__processors = processors

        self.__start_processor = None

        self.__previous = None
        self.__next = None

        if 'Verbosity' not in attributes:
            attributes['Verbosity'] = ModelVerbosity.OFF

        # http://www.earthsystemmodeling.org/esmf_releases/last_built/NUOPC_refdoc/node3.html#SECTION00033000000000000000
        self.attributes = attributes

    @property
    def entry_type(self) -> str:
        return str(self.model_type.value) if self.model_type is not None else None

    @property
    def processors(self) -> int:
        return self.__processors

    @processors.setter
    def processors(self, processors: int):
        if processors != self.processors:
            self.__processors = processors
            # update following processors
            self.start_processor = self.start_processor

    @property
    def start_processor(self) -> int:
        return self.__start_processor

    @start_processor.setter
    def start_processor(self, index: int):
        self.__start_processor = index
        current_model = self.next
        while current_model is not None:
            if current_model.previous is not None:
                current_model.__start_processor = current_model.previous.end_processor + 1
            current_model = current_model.next

    @property
    def end_processor(self) -> int:
        if self.start_processor is not None:
            return self.start_processor + self.processors - 1
        else:
            return None

    @property
    def previous(self) -> 'ModelEntry':
        return self.__previous

    @previous.setter
    def previous(self, previous: 'ModelEntry'):
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
        return self.__next

    @next.setter
    def next(self, next: 'ModelEntry'):
        if next is None and self.next is not None:
            self.next.__previous = None
        self.__next = next
        if self.next is not None:
            self.next.__previous = self

    @property
    def sequence_entry(self) -> str:
        return str(self.model_type.value)

    def __str__(self) -> str:
        return '\n'.join(
            [
                f'{self.entry_type}_model:                      {self.name}',
                f'{self.entry_type}_petlist_bounds:             {self.start_processor} {self.end_processor}',
                f'{self.entry_type}_attributes::',
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
        return f'{self.__class__.__name__}({repr(self.name)}, {self.model_type}, {self.processors}, {", ".join(kwargs)})'

    @classmethod
    def from_string(cls, string: str, **kwargs) -> 'ModelEntry':
        lines = string.splitlines()

        parsed_model_type, parsed_name = (value.strip() for value in lines[0].split('_model:'))
        parsed_model_type = ModelType(parsed_model_type)

        if hasattr(cls, 'model_type'):
            assert parsed_model_type == cls.model_type
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
            instance.model_type = parsed_model_type
        if not hasattr(cls, 'name'):
            instance.name = parsed_name

        return instance


class ConnectionEntry(SequenceEntry):
    def __init__(self, source: ModelEntry, target: ModelEntry, method: RemapMethod = None):
        self.source = source
        self.target = target
        self.method = method if method is not None else RemapMethod.BILINEAR

    @property
    def models(self) -> [ModelEntry]:
        return [self.source, self.target]

    @property
    def sequence_entry(self) -> str:
        return (
            f'{self.source.entry_type} -> {self.target.entry_type}'.ljust(13)
            + f':remapMethod={self.method.value}'
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.source)}, {repr(self.target)}, {repr(self.method)})'

    @classmethod
    def from_string(cls, string: str) -> 'ConnectionEntry':
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
                method = RemapMethod(parsed_method.split('=')[-1])

        source_model = ModelEntry(None)
        target_model = ModelEntry(None)

        source_model.name = source
        source_model.model_type = ModelType(source)
        target_model.name = target
        target_model.model_type = ModelType(target)

        return cls(source=source_model, target=target_model, method=method)


class MediatorEntry(ModelEntry):
    model_type = ModelType.MEDIATOR
    name = 'implicit'

    def __init__(self, processors: int = None, **attributes):
        if processors is None:
            processors = 1
        super().__init__(processors, **attributes)


class MediationFunctionEntry(SequenceEntry):
    def __init__(self, name: str, mediator: MediatorEntry):
        self.name = name
        self.mediator = mediator

    @property
    def sequence_entry(self) -> str:
        return f'{self.mediator.model_type.value} {self.name}'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.name)}, {repr(self.mediator)})'

    @classmethod
    def from_string(cls, string: str) -> 'MediationFunctionEntry':
        mediator_name, function_name = string.split()
        return cls(name=function_name, mediator=MediatorEntry(mediator_name),)


class MediationEntry(SequenceEntry):
    def __init__(
        self,
        mediator: MediatorEntry,
        sources: [ModelEntry] = None,
        functions: [str] = None,
        targets: [ModelEntry] = None,
        method: RemapMethod = None,
    ):
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
    def source_connections(self) -> [ConnectionEntry]:
        source_connections = []
        if self.sources is not None:
            for index, source in enumerate(self.sources):
                source_connections.append(ConnectionEntry(source, self.mediator, self.method))
        return source_connections

    @property
    def target_connections(self) -> [ConnectionEntry]:
        target_connections = []
        if self.targets is not None:
            for index, target in enumerate(self.targets):
                target_connections.append(ConnectionEntry(self.mediator, target, self.method))
        return target_connections

    @property
    def models(self) -> [ModelEntry]:
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
    def from_string(cls, string: str) -> 'MediationEntry':
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
