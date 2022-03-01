#!/usr/bin/env python

import logging

from setuptools import config, find_packages, setup

try:
    try:
        from dunamai import Version
    except ImportError:
        import subprocess
        import sys

        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'dunamai'])
        from dunamai import Version

    __version__ = Version.from_any_vcs().serialize()
except RuntimeError as error:
    logging.exception(error)
    __version__ = '0.0.0'

logging.info(f'using version {__version__}')

metadata = config.read_configuration('setup.cfg')['metadata']

setup(
    **metadata['name'],
    version=__version__,
    packages=find_packages(),
    python_requires='>=3.6',
    setup_requires=['dunamai', 'setuptools>=41.2'],
    install_requires=None,
    extras_require={
        'testing': ['pytest', 'pytest-cov', 'pytest-xdist'],
        'development': ['flake8', 'isort', 'oitnb'],
        'documentation': ['dunamai', 'm2r2', 'sphinx', 'sphinx-rtd-theme'],
    },
)
