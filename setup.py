#!/usr/bin/env python
from setuptools import config, find_packages, setup

metadata = config.read_configuration('setup.cfg')['metadata']

setup(
    name=metadata['name'],
    author=metadata['author'],
    author_email=metadata['author_email'],
    description=metadata['description'],
    long_description=metadata['long_description'],
    long_description_content_type="text/markdown",
    url=metadata['url'],
    packages=find_packages(),
    python_requires='>=3.8',
    setup_requires=['dunamai', 'setuptools>=41.2'],
    extras_require={'dev': ['coverage', 'nose']},
    test_suite='nose.collector'
)
