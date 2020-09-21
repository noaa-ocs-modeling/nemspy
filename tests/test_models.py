from datetime import timedelta
import unittest

from nemspy.configuration import ModelSequence
from nemspy.model.atmosphere import AtmosphericMesh
from nemspy.model.base import ModelType
from nemspy.model.ocean import ADCIRC
from nemspy.model.waves import WaveMesh
from nemspy.utilities import repository_root

REFERENCE_DIRECTORY = repository_root() / 'tests/reference'
ATMOSPHERIC_MESH_FILENAME = REFERENCE_DIRECTORY / 'wind_atm_fin_ch_time_vec.nc'
WAVE_MESH_FILENAME = REFERENCE_DIRECTORY / 'ww3.Constant.20151214_sxy_ike_date.nc'


class TestModel(unittest.TestCase):
    def test_model(self):
        model = AtmosphericMesh(ATMOSPHERIC_MESH_FILENAME, verbose=False,
                                test='value', test2=5)

        self.assertEqual(str(model),
                         'ATM_model:                      atmesh\n' \
                         'ATM_petlist_bounds:             0 0\n' \
                         'ATM_attributes::\n' \
                         '  Verbosity = min\n' \
                         '  test = value\n' \
                         '  test2 = 5\n' \
                         '::')

    def test_processors(self):
        model_1 = AtmosphericMesh(ATMOSPHERIC_MESH_FILENAME)
        model_2 = WaveMesh(WAVE_MESH_FILENAME)
        model_3 = ADCIRC(11)

        self.assertEqual(model_1.start_processor, 0)
        self.assertEqual(model_1.end_processor, 0)
        self.assertEqual(model_2.start_processor, 0)
        self.assertEqual(model_2.end_processor, 0)
        self.assertEqual(model_3.start_processor, 0)
        self.assertEqual(model_3.end_processor, 10)

        model_1.next = model_2
        model_2.next = model_3

        self.assertEqual(model_1.start_processor, 0)
        self.assertEqual(model_1.end_processor, 0)
        self.assertEqual(model_2.start_processor, 1)
        self.assertEqual(model_2.end_processor, 1)
        self.assertEqual(model_3.start_processor, 2)
        self.assertEqual(model_3.end_processor, 12)

        model_2.processors = 3
        model_1.processors = 4

        self.assertEqual(model_1.start_processor, 0)
        self.assertEqual(model_1.end_processor, 3)
        self.assertEqual(model_2.start_processor, 4)
        self.assertEqual(model_2.end_processor, 6)
        self.assertEqual(model_3.start_processor, 7)
        self.assertEqual(model_3.end_processor, 17)

    def test_sequence(self):
        sequence = ModelSequence(timedelta(hours=1),
                                 atmospheric=AtmosphericMesh(
                                     ATMOSPHERIC_MESH_FILENAME),
                                 wave=WaveMesh(WAVE_MESH_FILENAME),
                                 ocean=ADCIRC(11))

        self.assertEqual(sequence.sequence, [ModelType.ATMOSPHERIC,
                                             ModelType.WAVE, ModelType.OCEAN])

        models = sequence.models

        self.assertEqual(models[0].start_processor, 0)
        self.assertEqual(models[0].end_processor, 0)
        self.assertEqual(models[1].start_processor, 1)
        self.assertEqual(models[1].end_processor, 1)
        self.assertEqual(models[2].start_processor, 2)
        self.assertEqual(models[2].end_processor, 12)

        with self.assertRaises(ValueError):
            sequence.sequence = []
        with self.assertRaises(ValueError):
            sequence.sequence = [ModelType.ATMOSPHERIC]
        with self.assertRaises(ValueError):
            sequence.sequence = [ModelType.HYDROLOGICAL]

        self.assertEqual(sequence.sequence, [ModelType.ATMOSPHERIC,
                                             ModelType.WAVE, ModelType.OCEAN])

        sequence.sequence = [ModelType.OCEAN, ModelType.ATMOSPHERIC,
                             ModelType.WAVE]

        self.assertEqual(sequence.sequence, [ModelType.OCEAN,
                                             ModelType.ATMOSPHERIC,
                                             ModelType.WAVE])

        models = sequence.models

        self.assertEqual(models[0].start_processor, 0)
        self.assertEqual(models[0].end_processor, 10)
        self.assertEqual(models[1].start_processor, 11)
        self.assertEqual(models[1].end_processor, 11)
        self.assertEqual(models[2].start_processor, 12)
        self.assertEqual(models[2].end_processor, 12)


if __name__ == '__main__':
    unittest.main()
