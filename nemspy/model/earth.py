from typing import Dict, Generator

from .base import ModelEntry, ModelType
from ..verbosity import ModelVerbosity


class EarthModel:
    """
    multi-model coupling container
    """

    header = 'EARTH'

    def __init__(self, verbosity: ModelVerbosity = ModelVerbosity.MINIMUM,
                 **kwargs):
        self.verbosity = ModelVerbosity.MINIMUM if verbosity is None \
                         else verbosity
        self.__models: Dict[ModelType, ModelEntry] = {}
        for key, value in kwargs.items():
            if key.upper() in {entry.name for entry in ModelType} and \
                    isinstance(value, ModelEntry):
                self[ModelType[key.upper()]] = value

    def __getitem__(self, model_type: ModelType) -> ModelEntry:
        return self.__models[model_type]

    def __setitem__(self, model_type: ModelType, model: ModelEntry):
        self.__models[model_type] = model

    def __contains__(self, model_type: ModelType):
        return model_type in self.__models

    def __iter__(self) -> Generator:
        for model_type, model in self.__models.items():
            yield model_type, model

    def __str__(self) -> str:
        return '\n' \
            f'# {self.header} #\n' \
            f'{self.header}_component_list: ' \
            f'{" ".join(model_type.value for model_type in self.__models)}\n' \
            f'{self.header}_attributes::\n' \
            f'  Verbosity = {self.verbosity.value}\n::' + \
            '\n'.join([str(entry) for entry in self.__models.items()])
