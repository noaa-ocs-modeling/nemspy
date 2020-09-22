#!/usr/bin/env python
# flake8: noqa

from datetime import datetime, timedelta
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
ATMOSPHERIC_MESH_FILENAME = '~/wind_atm_fin_ch_time_vec.nc'
WAVE_MESH_FILENAME = '~/ww3.Constant.20151214_sxy_ike_date.nc'


class TestInterface(unittest.TestCase):
    def test_interface(self):
        start_time = datetime(2020, 6, 1)
        duration = timedelta(days=1)
        interval = timedelta(hours=1)
        atmospheric_mesh = AtmosphericMesh(ATMOSPHERIC_MESH_FILENAME)
        wave_mesh = WaveMesh(WAVE_MESH_FILENAME)
        ocean_model = ADCIRC(11)
        hydrological_model = NationalWaterModel(769)

        nems = ModelingSystem(start_time, duration, interval,
                              atmospheric=atmospheric_mesh,
                              wave=wave_mesh, ocean=ocean_model,
                              hydrological=hydrological_model)

        self.assertIs(nems['atmospheric'], atmospheric_mesh)
        self.assertIs(nems['wave'], wave_mesh)
        self.assertIs(nems['ocean'], ocean_model)
        self.assertIs(nems['hydrological'], hydrological_model)

        self.assertEqual(nems.interval, interval)
        self.assertEqual(nems.verbose, False)

        new_interval = timedelta(minutes=30)
        nems.interval = new_interval
        nems.verbose = True

        self.assertEqual(nems.interval, new_interval)
        self.assertEqual(nems.verbose, True)

    def test_connection(self):
        start_time = datetime(2020, 6, 1)
        duration = timedelta(days=1)
        interval = timedelta(hours=1)
        ocean_model = ADCIRC(11)
        wave_mesh = WaveMesh(WAVE_MESH_FILENAME)

        nems = ModelingSystem(start_time, duration, interval,
                              ocean=ocean_model, wave=wave_mesh)
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

    def test_sequence(self):
        start_time = datetime(2020, 6, 1)
        duration = timedelta(days=1)
        interval = timedelta(hours=1)
        atmospheric_mesh = AtmosphericMesh(ATMOSPHERIC_MESH_FILENAME)
        wave_mesh = WaveMesh(WAVE_MESH_FILENAME)
        ocean_model = ADCIRC(11)

        nems = ModelingSystem(start_time, duration, interval,
                              atmospheric=atmospheric_mesh,
                              wave=wave_mesh, ocean=ocean_model)

        self.assertEqual(nems.sequence, ['atmospheric', 'wave', 'ocean'])

        models = nems.models

        self.assertEqual(models[0].start_processor, 0)
        self.assertEqual(models[0].end_processor, 0)
        self.assertEqual(models[1].start_processor, 1)
        self.assertEqual(models[1].end_processor, 1)
        self.assertEqual(models[2].start_processor, 2)
        self.assertEqual(models[2].end_processor, 12)

        with self.assertRaises(ValueError):
            nems.sequence = []
        with self.assertRaises(ValueError):
            nems.sequence = ['atmospheric']
        with self.assertRaises(ValueError):
            nems.sequence = ['hydrological']
        with self.assertRaises(ValueError):
            nems.sequence = ['nonexistent']

        self.assertEqual(nems.sequence, ['atmospheric', 'wave', 'ocean'])

        nems.sequence = ['ocean', 'atmospheric', 'wave']

        self.assertEqual(nems.sequence, ['ocean', 'atmospheric', 'wave'])

        models = nems.models

        self.assertEqual(models[0].start_processor, 0)
        self.assertEqual(models[0].end_processor, 10)
        self.assertEqual(models[1].start_processor, 11)
        self.assertEqual(models[1].end_processor, 11)
        self.assertEqual(models[2].start_processor, 12)
        self.assertEqual(models[2].end_processor, 12)

    def test_configuration_files(self):
        start_time = datetime(2020, 6, 1)
        duration = timedelta(days=1)
        interval = timedelta(hours=1)
        atmospheric_mesh = AtmosphericMesh(ATMOSPHERIC_MESH_FILENAME)
        wave_mesh = WaveMesh(WAVE_MESH_FILENAME)
        ocean_model = ADCIRC(11)
        hydrological_model = NationalWaterModel(769)

        nems = ModelingSystem(start_time, duration, interval,
                              atmospheric=atmospheric_mesh,
                              wave=wave_mesh, ocean=ocean_model,
                              hydrological=hydrological_model)
        nems.connect('atmospheric', 'ocean')
        nems.connect('wave', 'ocean')
        nems.connect('atmospheric', 'hydrological')
        nems.connect('wave', 'hydrological')
        nems.connect('ocean', 'hydrological')

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_directory = Path(temporary_directory)
            nems.write(temporary_directory)
            for test_filename in temporary_directory.iterdir():
                reference_filename = REFERENCE_DIRECTORY / test_filename.name
                with open(test_filename) as test_file:
                    with open(reference_filename) as reference_file:
                        self.assertEqual(test_file.read(),
                                         reference_file.read())


if __name__ == '__main__':
    unittest.main()
