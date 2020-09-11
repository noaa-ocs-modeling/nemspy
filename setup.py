#!/usr/bin/env python
import pathlib

import setuptools

import versioneer

PARENT = pathlib.Path(__file__).parent.absolute()
conf = setuptools.config.read_configuration(PARENT / 'setup.cfg')
meta = conf['metadata']

setuptools.setup(
    name=meta['name'],
    version=versioneer.get_version(),
    author=meta['author'],
    author_email=meta['author_email'],
    description=meta['description'],
    long_description=meta['long_description'],
    long_description_content_type="text/markdown",
    url=meta['url'],
    packages=setuptools.find_packages(),
    python_requires='>=3.8',
    cmdclass=versioneer.get_cmdclass(),
    # setup_requires=["setuptools>=41.2"],
    # install_requires=[],
    # entry_points={
    #     'console_scripts': []
    # },
    test_suite='nose.collector',
    tests_require=['nose']
    )
