#!/usr/bin/env python
# flake8: noqa

from datetime import timedelta
from pathlib import Path
import tempfile
import unittest

from nemspy import ModelingSystem
from nemspy.model.atmosphere import AtmosphericMesh
from nemspy.model.hydrology import NationalWaterModel
from nemspy.model.ocean import ADCIRC
from nemspy.model.waves import WaveMesh
from nemspy.utilities import repository_root


class TestConfiguration(unittest.TestCase):
    def test_connection(self):
        nems = ModelingSystem(timedelta(hours=1), ocean=ADCIRC(11),
                              wave=WaveMesh(1))
        nems.connect('wave', 'ocean')

        with self.assertRaises(ValueError):
            nems.connect('atmospheric', 'ocean')
        with self.assertRaises(ValueError):
            nems.connect('wave', 'hydrological')
        self.assertEqual(nems.connections,
                         ['WAV -> OCN   :remapMethod=redist'])

    def test_configuration(self):
        nems = ModelingSystem(timedelta(hours=1),
                              atmospheric=AtmosphericMesh(),
                              wave=WaveMesh(), ocean=ADCIRC(11),
                              hydrological=NationalWaterModel(769))
        nems.connect('atmospheric', 'ocean')
        nems.connect('wave', 'ocean')
        nems.connect('atmospheric', 'hydrological')
        nems.connect('wave', 'hydrological')
        nems.connect('ocean', 'hydrological')

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_filename = Path(temporary_directory) / 'test.configure'
            nems.write(temporary_filename)
            with open(temporary_filename) as temporary_file:
                with open(repository_root() /
                          'tests/reference/nems.configure') as reference_file:
                    self.assertEqual(temporary_file.read(),
                                     reference_file.read())


if __name__ == '__main__':
    unittest.main()
