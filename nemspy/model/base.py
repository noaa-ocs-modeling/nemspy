from abc import ABC, abstractmethod
from enum import Enum
from os import PathLike
from pathlib import Path
from textwrap import indent

from nemspy.utilities import get_logger

LOGGER = get_logger('model')
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


class ModelMeshEntry(ABC):
    def __init__(self, mesh_type: ModelType, filename: PathLike):
        if not isinstance(filename, Path):
            filename = Path(filename)

        self.mesh_type = mesh_type
        self.filename = filename

    def __str__(self) -> str:
        return (
            f' {self.mesh_type.value.lower()}_dir: {self.filename.parent}\n'
            f' {self.mesh_type.value.lower()}_nam: {self.filename.name}'
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

    def __init__(
        self, name: str, model_type: ModelType, processors: int, **attributes,
    ):
        self.name = name
        self.model_type = model_type
        self.__processors = processors

        self.__start_processor = None

        self.__previous = None
        self.__next = None

        self.entry_type = str(self.model_type.value)

        if 'Verbosity' not in attributes:
            attributes['Verbosity'] = ModelVerbosity.OFF

        # http://www.earthsystemmodeling.org/esmf_releases/last_built/NUOPC_refdoc/node3.html#SECTION00033000000000000000
        self.attributes = attributes

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


class ConnectionEntry(SequenceEntry):
    def __init__(self, source: ModelEntry, target: ModelEntry, method: RemapMethod = None):
        self.source = source
        self.target = target
        self.method = method if method is not None else RemapMethod.REDISTRIBUTE

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


class MediatorEntry(ModelEntry):
    def __init__(self, name: str, processors: int = None, **attributes):
        if processors is None:
            processors = 1
        super().__init__(name, ModelType.MEDIATOR, processors, **attributes)


class MediationFunctionEntry(SequenceEntry):
    def __init__(self, name: str, mediator: MediatorEntry):
        self.name = name
        self.mediator = mediator

    @property
    def sequence_entry(self) -> str:
        return f'{self.mediator.model_type.value} {self.name}'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.name)}, {repr(self.mediator)})'


class MediationEntry(ConnectionEntry):
    def __init__(
        self,
        source: ModelEntry,
        mediator: MediatorEntry,
        target: ModelEntry = None,
        functions: [str] = None,
        method: RemapMethod = None,
    ):
        if functions is None:
            functions = []
        self.mediator = mediator
        self.functions = [
            MediationFunctionEntry(mediation_function, self.mediator)
            for mediation_function in functions
        ]
        super().__init__(source, target, method)

    @property
    def models(self) -> [ModelEntry]:
        return [self.source, self.mediator, self.target]

    @property
    def sequence_entry(self) -> str:
        output = ''
        if self.source is not None:
            output += (
                f'{self.source.entry_type} -> {self.mediator.entry_type}'.ljust(13)
                + f':remapMethod={self.method.value}'
            )
            if len(self.functions) > 0:
                output += '\n'
        output += '\n'.join(
            mediation_function.sequence_entry for mediation_function in self.functions
        )
        if self.target is not None:
            output += (
                '\n'
                + f'{self.mediator.entry_type} -> {self.target.entry_type}'.ljust(13)
                + f':remapMethod={self.method.value}'
            )
        return output

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.source)}, {repr(self.target)}, {repr(self.mediator)}, {self.method.name})'
