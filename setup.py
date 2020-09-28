#!/usr/bin/env python
from dunamai import Version
from setuptools import config, find_packages, setup

metadata = config.read_configuration('setup.cfg')['metadata']

setup(
    name=metadata['name'],
    version=Version.from_any_vcs().serialize(),
    author=metadata['author'],
    author_email=metadata['author_email'],
    description=metadata['description'],
    long_description=metadata['long_description'],
    long_description_content_type='text/markdown',
    url=metadata['url'],
    packages=find_packages(),
    python_requires='>=3.6',
    setup_requires=['dunamai', 'setuptools>=41.2'],
    install_requires=['dunamai'],
    extras_require={'dev': ['coverage', 'dunamai', 'flake8', 'nose']},
    test_suite='nose.collector',
)
