#!/usr/bin/env python
from setuptools import config, find_packages, setup

import versioneer

metadata = config.read_configuration('setup.cfg')['metadata']

setup(
    name=metadata['name'],
    version=versioneer.get_version(),
    author=metadata['author'],
    author_email=metadata['author_email'],
    description=metadata['description'],
    long_description=metadata['long_description'],
    long_description_content_type="text/markdown",
    url=metadata['url'],
    packages=find_packages(),
    python_requires='>=3.8',
    cmdclass=versioneer.get_cmdclass(),
    setup_requires=["setuptools>=41.2"],
    test_suite='nose.collector',
    tests_require=['nose']
)
