from datetime import datetime
import logging
import os
from os import PathLike
from pathlib import Path
import shutil
import sys
from typing import Union


def repository_root(path: PathLike = None) -> Path:
    """
    find enclosing Git repository

    :param path: path to start at
    :return: path to root of Git repository
    """

    if path is None:
        path = __file__
    if not isinstance(path, Path):
        path = Path(path)
    if path.is_file():
        path = path.parent
    if '.git' in (child.name for child in path.iterdir()) or path == path.parent:
        return path
    else:
        return repository_root(path.parent)


def get_logger(
    name: str,
    log_filename: PathLike = None,
    file_level: int = None,
    console_level: int = None,
    log_format: str = None,
) -> logging.Logger:
    """
    instantiate logger instance

    :param name: name of logger
    :param log_filename: path to log file
    :param file_level: minimum log level to write to log file
    :param console_level: minimum log level to print to console
    :param log_format: logger message format
    :return: instance of a Logger object
    """

    if file_level is None:
        file_level = logging.DEBUG
    if console_level is None:
        console_level = logging.INFO
    logger = logging.getLogger(name)

    # check if logger is already configured
    if logger.level == logging.NOTSET and len(logger.handlers) == 0:
        # check if logger has a parent
        if '.' in name:
            if isinstance(logger.parent, logging.RootLogger):
                for existing_console_handler in [
                    handler
                    for handler in logger.parent.handlers
                    if not isinstance(handler, logging.FileHandler)
                ]:
                    logger.parent.removeHandler(existing_console_handler)
            logger.parent = get_logger(name.rsplit('.', 1)[0])
        else:
            # otherwise create a new split-console logger
            if console_level != logging.NOTSET:
                for existing_console_handler in [
                    handler
                    for handler in logger.handlers
                    if not isinstance(handler, logging.FileHandler)
                ]:
                    logger.removeHandler(existing_console_handler)

                console_output = logging.StreamHandler(sys.stdout)
                console_output.setLevel(console_level)
                logger.addHandler(console_output)

    if log_filename is not None:
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(file_level)
        for existing_file_handler in [
            handler for handler in logger.handlers if isinstance(handler, logging.FileHandler)
        ]:
            logger.removeHandler(existing_file_handler)
        logger.addHandler(file_handler)

    if log_format is None:
        log_format = '[%(asctime)s] %(name)-15s %(levelname)-8s: %(message)s'
    log_formatter = logging.Formatter(log_format)
    for handler in logger.handlers:
        handler.setFormatter(log_formatter)

    return logger


LOGGER = get_logger('nemspy')


def create_symlink(
    source_filename: PathLike, symlink_filename: PathLike, relative: bool = False
):
    """
    :param source_filename: path to point to
    :param symlink_filename: path at which to create symlink
    :param relative: make symlink relative to source location
    """

    if not isinstance(source_filename, Path):
        source_filename = Path(source_filename)
    if not isinstance(symlink_filename, Path):
        symlink_filename = Path(symlink_filename)

    if symlink_filename.is_symlink():
        LOGGER.debug(f'removing symlink "{symlink_filename}"')
        os.remove(symlink_filename)
    symlink_filename = symlink_filename.parent.absolute().resolve() / symlink_filename.name

    starting_directory = None
    if relative:
        starting_directory = Path().cwd().resolve()
        os.chdir(symlink_filename.parent)
        if source_filename.is_absolute():
            try:
                source_filename = source_filename.relative_to(symlink_filename.parent)
            except ValueError as error:
                LOGGER.warning(error)
                os.chdir(starting_directory)
    else:
        source_filename = source_filename.absolute()

    try:
        symlink_filename.symlink_to(source_filename)
    except Exception as error:
        LOGGER.warning(f'could not create symbolic link: {error}')
        shutil.copyfile(source_filename, symlink_filename)

    if starting_directory is not None:
        os.chdir(starting_directory)


def parse_datetime(value: Union[int, float, str, datetime]) -> datetime:
    """
    attempt to parse a datetime from the given value

    :param value: value to parse
    :return: parsed datetime
    """

    if not isinstance(value, datetime):
        if isinstance(value, int) or isinstance(value, float):
            value = datetime.fromtimestamp(value)
        elif isinstance(value, str):
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        else:
            raise TypeError(
                f'unable to convert value of type "{type(value)}" to datetime: {value}'
            )
    return value
