import unittest

from nemspy.model.atmosphere import AtmosphericMesh
from nemspy.model.ocean import ADCIRC
from nemspy.model.waves import WaveMesh


class TestModel(unittest.TestCase):
    def test_model(self):
        model = AtmosphericMesh(1, verbose=False, test='value', test2=5)

        self.assertEqual(str(model),
                         'ATM_model:                      atmesh\n' \
                         'ATM_petlist_bounds:             0 0\n' \
                         'ATM_attributes::\n' \
                         '  Verbosity = min\n' \
                         '  test = value\n' \
                         '  test2 = 5\n' \
                         '::')

    def test_processors(self):
        model_1 = AtmosphericMesh(1)
        model_2 = WaveMesh(1)
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


if __name__ == '__main__':
    unittest.main()
