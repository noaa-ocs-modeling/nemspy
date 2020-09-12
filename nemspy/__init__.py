import logging
from pathlib import Path
from datetime import timedelta
import sys

from .model import ModelType, Model
from .model.ocean import OceanModel
from .model.atmospheric import AtmosphericModel
from .model.waves import WaveModel
from .model.hydrologic import HydrologicalModel
from .configuration import NEMSConfiguration, ModelSequence


def repository_root(path: str = None) -> str:
    if path is None:
        path = __file__
    if not isinstance(path, Path):
        path = Path(path)
    if path.is_file():
        path = path.parent
    if '.git' in (child.name for child in
                  path.iterdir()) or path == path.parent:
        return path
    else:
        return repository_root(path.parent)


def get_logger(name: str, log_filename: str = None, file_level: int = None,
               console_level: int = None,
               log_format: str = None) -> logging.Logger:
    if file_level is None:
        file_level = logging.DEBUG
    if console_level is None:
        console_level = logging.INFO
    logger = logging.getLogger(name)

    # check if logger is already configured
    if logger.level == logging.NOTSET and len(logger.handlers) == 0:
        # check if logger has a parent
        if '.' in name:
            logger.parent = get_logger(name.rsplit('.', 1)[0])
        else:
            # otherwise create a new split-console logger
            logger.setLevel(logging.DEBUG)
            if console_level != logging.NOTSET:
                if console_level <= logging.INFO:
                    class LoggingOutputFilter(logging.Filter):
                        def filter(self, rec):
                            return rec.levelno in (logging.DEBUG, logging.INFO)

                    console_output = logging.StreamHandler(sys.stdout)
                    console_output.setLevel(console_level)
                    console_output.addFilter(LoggingOutputFilter())
                    logger.addHandler(console_output)

                console_errors = logging.StreamHandler(sys.stderr)
                console_errors.setLevel(max((console_level, logging.WARNING)))
                logger.addHandler(console_errors)

    if log_filename is not None:
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(file_level)
        for existing_file_handler in [handler for handler in logger.handlers if
                                      type(handler) is logging.FileHandler]:
            logger.removeHandler(existing_file_handler)
        logger.addHandler(file_handler)

    if log_format is None:
        log_format = '[%(asctime)s] %(name)-13s %(levelname)-8s: %(message)s'
    log_formatter = logging.Formatter(log_format)
    for handler in logger.handlers:
        handler.setFormatter(log_formatter)

    return logger


class NEMS:

    def __init__(
            self,
            ocean: OceanModel = None,
            waves: WaveModel = None,
            atmospheric: AtmosphericModel = None,
            hydrological: HydrologicalModel = None
    ):
        models = {}

        if ocean is not None:
            assert isinstance(ocean, OceanModel)
        models.update({OceanModel: ocean})

        if waves is not None:
            assert isinstance(waves, WaveModel)
        models.update({WaveModel: waves})

        if atmospheric is not None:
            assert isinstance(atmospheric, AtmosphericModel)
        models.update({AtmosphericModel: atmospheric})

        if hydrological is not None:
            assert isinstance(hydrological, HydrologicalModel)
        models.update({HydrologicalModel: hydrological})

        self.models = models
        self.sequences = []

    def add_sequence(self, duration: timedelta) -> ModelSequence:
        self.sequences.append(seq := ModelSequence(duration, **self.models))
        return seq

    def write(self, filename: str):
        self.configuration.write(filename)

    @property
    def models(self) -> {ModelType: Model}:
        return {model_type: model
                for model_type, model in self.__models.items()
                if model is not None}

    @models.setter
    def models(self, models):
        if len(models) == 0:
            raise TypeError('Must specify at least one model.')
        self.__models = models

    @property
    def configuration(self):
        return NEMSConfiguration(self.sequences)

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
