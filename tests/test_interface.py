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

REFERENCE_DIRECTORY = repository_root() / 'tests/reference'
ATMOSPHERIC_MESH_FILENAME = REFERENCE_DIRECTORY / 'wind_atm_fin_ch_time_vec.nc'
WAVE_MESH_FILENAME = REFERENCE_DIRECTORY / 'ww3.Constant.20151214_sxy_ike_date.nc'


class TestConfiguration(unittest.TestCase):
    def test_connection(self):
        nems = ModelingSystem(timedelta(hours=1), ocean=ADCIRC(11),
                              wave=WaveMesh(WAVE_MESH_FILENAME))
        nems.connect('wave', 'ocean')

        with self.assertRaises(ValueError):
            nems.connect('atmospheric', 'ocean')
        with self.assertRaises(ValueError):
            nems.connect('wave', 'hydrological')
        with self.assertRaises(ValueError):
            nems.connect('wave', 'nonexistent')
        with self.assertRaises(ValueError):
            nems.connect('wave', 'ocean', 'nonexistent')

        self.assertEqual(nems.connections,
                         ['WAV -> OCN   :remapMethod=redist'])

    def test_configuration(self):
        nems = ModelingSystem(timedelta(hours=1),
                              atmospheric=AtmosphericMesh(
                                  ATMOSPHERIC_MESH_FILENAME),
                              wave=WaveMesh(WAVE_MESH_FILENAME),
                              ocean=ADCIRC(11),
                              hydrological=NationalWaterModel(769))
        nems.connect('atmospheric', 'ocean')
        nems.connect('wave', 'ocean')
        nems.connect('atmospheric', 'hydrological')
        nems.connect('wave', 'hydrological')
        nems.connect('ocean', 'hydrological')

        reference_filename = REFERENCE_DIRECTORY / 'nems.configure'
        with tempfile.TemporaryDirectory() as temporary_directory:
            nems.write(temporary_directory)
            test_filename = Path(temporary_directory) / 'nems.configure'
            with open(test_filename) as temporary_file:
                with open(reference_filename) as reference_file:
                    self.assertEqual(temporary_file.read(),
                                     reference_file.read())


if __name__ == '__main__':
    unittest.main()
