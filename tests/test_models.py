import unittest

from nemspy.model.atmosphere import AtmosphericMeshEntry
from nemspy.model.ocean import ADCIRCEntry
from nemspy.model.waves import WaveMeshEntry
from nemspy.utilities import repository_root

REFERENCE_DIRECTORY = repository_root() / 'tests/reference'
ATMOSPHERIC_MESH_FILENAME = REFERENCE_DIRECTORY / 'wind_atm_fin_ch_time_vec.nc'
WAVE_MESH_FILENAME = REFERENCE_DIRECTORY / 'ww3.Constant.20151214_sxy_ike_date.nc'


class TestModels(unittest.TestCase):
    def test_model(self):
        model = AtmosphericMeshEntry(
            ATMOSPHERIC_MESH_FILENAME, verbose=False, test='value', test2=5
        )
        model.start_processor = 0

        self.assertEqual(
            'ATM_model:                      atmesh\n'
            'ATM_petlist_bounds:             0 0\n'
            'ATM_attributes::\n'
            '  Verbosity = min\n'
            '  test = value\n'
            '  test2 = 5\n'
            '::',
            str(model),
        )

    def test_processors(self):
        model_1 = AtmosphericMeshEntry(ATMOSPHERIC_MESH_FILENAME)
        model_2 = WaveMeshEntry(WAVE_MESH_FILENAME)
        model_3 = ADCIRCEntry(11)

        model_1.next = model_2
        model_2.next = model_3

        self.assertIs(model_1.start_processor, None)
        self.assertIs(model_1.end_processor, None)
        self.assertIs(model_2.start_processor, None)
        self.assertIs(model_2.end_processor, None)
        self.assertIs(model_3.start_processor, None)
        self.assertIs(model_3.end_processor, None)

        model_1.start_processor = 0

        self.assertEqual(0, model_1.start_processor)
        self.assertEqual(0, model_1.end_processor)
        self.assertEqual(1, model_2.start_processor)
        self.assertEqual(1, model_2.end_processor)
        self.assertEqual(2, model_3.start_processor)
        self.assertEqual(12, model_3.end_processor)

        model_2.processors = 3
        model_1.processors = 4

        self.assertEqual(0, model_1.start_processor)
        self.assertEqual(3, model_1.end_processor)
        self.assertEqual(4, model_2.start_processor)
        self.assertEqual(6, model_2.end_processor)
        self.assertEqual(7, model_3.start_processor)
        self.assertEqual(17, model_3.end_processor)


if __name__ == '__main__':
    unittest.main()
