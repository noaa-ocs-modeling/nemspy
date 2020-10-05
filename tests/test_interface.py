#!/usr/bin/env python
# flake8: noqa

from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest

from nemspy import ModelingSystem
from nemspy.model.atmosphere import AtmosphericMeshEntry
from nemspy.model.hydrology import NationalWaterModelEntry
from nemspy.model.ice import IceMeshEntry
from nemspy.model.ocean import ADCIRCEntry
from nemspy.model.waves import WaveMeshEntry
from nemspy.utilities import repository_root

REFERENCE_DIRECTORY = repository_root() / 'tests/reference'
ATMOSPHERIC_MESH_FILENAME = '~/wind_atm_fin_ch_time_vec.nc'
ICE_MESH_FILENAME = '~/sea_ice.nc'
WAVE_MESH_FILENAME = '~/ww3.Constant.20151214_sxy_ike_date.nc'


class TestInterface(unittest.TestCase):
    def test_interface(self):
        start_time = datetime(2020, 6, 1)
        duration = timedelta(days=1)
        interval = timedelta(hours=1)
        atmospheric_mesh = AtmosphericMeshEntry(ATMOSPHERIC_MESH_FILENAME)
        wave_mesh = WaveMeshEntry(WAVE_MESH_FILENAME)
        ocean_model = ADCIRCEntry(11)

        nems = ModelingSystem(
            start_time,
            duration,
            interval,
            atm=atmospheric_mesh,
            wav=wave_mesh,
            ocn=ocean_model,
        )

        self.assertIs(nems['ATM'], atmospheric_mesh)
        self.assertIs(nems['WAV'], wave_mesh)
        self.assertIs(nems['OCN'], ocean_model)

        with self.assertRaises(KeyError):
            nems['HYD']
        with self.assertRaises(KeyError):
            nems['nonexistent']

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
        ocean_model = ADCIRCEntry(11)
        wave_mesh = WaveMeshEntry(WAVE_MESH_FILENAME)

        nems = ModelingSystem(start_time, duration, interval, ocn=ocean_model, wav=wave_mesh)
        nems.connect('WAV', 'OCN')

        with self.assertRaises(KeyError):
            nems.connect('ATM', 'OCN')
        with self.assertRaises(KeyError):
            nems.connect('WAV', 'HYD')
        with self.assertRaises(KeyError):
            nems.connect('WAV', 'nonexistent')
        with self.assertRaises(KeyError):
            nems.connect('WAV', 'OCN', 'nonexistent')

        self.assertEqual(nems.connections, ['WAV -> OCN   :remapMethod=redist'])

    def test_mediation(self):
        start_time = datetime(2020, 6, 1)
        duration = timedelta(days=1)
        interval = timedelta(hours=1)
        atmospheric_mesh = AtmosphericMeshEntry(ATMOSPHERIC_MESH_FILENAME)
        ice_mesh = IceMeshEntry(ICE_MESH_FILENAME)
        ocean_model = ADCIRCEntry(11)

        nems = ModelingSystem(
            start_time, duration, interval, ice=ice_mesh, ocn=ocean_model, atm=atmospheric_mesh
        )

        nems.connect('OCN', 'MED')
        nems.mediate('ATM', 'ICE', ['MedPhase_prep_ice'])
        nems.mediate('ICE', None, ['MedPhase_atm_ocn_flux', 'MedPhase_accum_fast'])
        nems.mediate(None, 'OCN', ['MedPhase_prep_ocn'])

        nems.sequence = [
            'ATM',
            'ATM -> MED -> ICE',
            'ICE',
            'ICE -> MED',
            'MED -> OCN',
            'OCN',
            'OCN -> MED',
        ]

        with self.assertRaises(KeyError):
            nems.connect('HYD', 'OCN')
        with self.assertRaises(KeyError):
            nems.connect('WAV', 'nonexistent')
        with self.assertRaises(KeyError):
            nems.connect('WAV', 'OCN', 'nonexistent')

        self.assertEqual(
            nems.connections,
            [
                'ATM -> MED   :remapMethod=redist\n'
                'MED MedPhase_prep_ice\n'
                'MED -> ICE   :remapMethod=redist',
                'ICE -> MED   :remapMethod=redist\n'
                'MED MedPhase_atm_ocn_flux\n'
                'MED MedPhase_accum_fast',
                'MED MedPhase_prep_ocn\n' 'MED -> OCN   :remapMethod=redist',
                'OCN -> MED   :remapMethod=redist',
            ],
        )

    def test_sequence(self):
        start_time = datetime(2020, 6, 1)
        duration = timedelta(days=1)
        interval = timedelta(hours=1)
        atmospheric_mesh = AtmosphericMeshEntry(ATMOSPHERIC_MESH_FILENAME)
        wave_mesh = WaveMeshEntry(WAVE_MESH_FILENAME)
        ocean_model = ADCIRCEntry(11)

        nems = ModelingSystem(
            start_time,
            duration,
            interval,
            atm=atmospheric_mesh,
            wav=wave_mesh,
            ocn=ocean_model,
        )

        models = nems.models

        self.assertEqual(0, models[0].start_processor)
        self.assertEqual(0, models[0].end_processor)
        self.assertEqual(1, models[1].start_processor)
        self.assertEqual(1, models[1].end_processor)
        self.assertEqual(2, models[2].start_processor)
        self.assertEqual(12, models[2].end_processor)

        self.assertEqual(['ATM', 'WAV', 'OCN'], nems.sequence)
        with self.assertRaises(KeyError):
            nems.sequence = ['HYD']
        with self.assertRaises(KeyError):
            nems.sequence = ['nonexistent']
        with self.assertRaises(KeyError):
            nems.sequence = ['OCN', 'ATM', 'WAV', 'WAV -> OCN ']
        self.assertEqual(['ATM', 'WAV', 'OCN'], nems.sequence)

        nems.sequence = ['OCN', 'ATM', 'WAV']

        self.assertEqual(['OCN', 'ATM', 'WAV'], nems.sequence)

        models = nems.models

        self.assertEqual(0, models[0].start_processor)
        self.assertEqual(10, models[0].end_processor)
        self.assertEqual(11, models[1].start_processor)
        self.assertEqual(11, models[1].end_processor)
        self.assertEqual(12, models[2].start_processor)
        self.assertEqual(12, models[2].end_processor)

    def test_configuration_files(self):
        start_time = datetime(2020, 6, 1)
        duration = timedelta(days=1)
        interval = timedelta(hours=1)
        atmospheric_mesh = AtmosphericMeshEntry(ATMOSPHERIC_MESH_FILENAME)
        wave_mesh = WaveMeshEntry(WAVE_MESH_FILENAME)
        ocean_model = ADCIRCEntry(11)
        hydrological_model = NationalWaterModelEntry(769)

        nems = ModelingSystem(
            start_time,
            duration,
            interval,
            atm=atmospheric_mesh,
            wav=wave_mesh,
            ocn=ocean_model,
            hyd=hydrological_model,
        )
        nems.connect('ATM', 'OCN')
        nems.connect('WAV', 'OCN')
        nems.connect('ATM', 'HYD')
        nems.connect('WAV', 'HYD')
        nems.connect('OCN', 'HYD')

        sequence = [
            'ATM -> OCN',
            'WAV -> OCN',
            'ATM -> HYD',
            'WAV -> HYD',
            'OCN -> HYD',
            'ATM',
            'WAV',
            'OCN',
            'HYD',
        ]

        nems.sequence = sequence

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_directory = Path(temporary_directory)
            nems.write(temporary_directory)
            for test_filename in temporary_directory.iterdir():
                reference_filename = REFERENCE_DIRECTORY / test_filename.name
                with open(test_filename) as test_file:
                    with open(reference_filename) as reference_file:
                        self.assertEqual(reference_file.read(), test_file.read())


if __name__ == '__main__':
    unittest.main()
