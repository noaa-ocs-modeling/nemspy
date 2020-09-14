import unittest

from nemspy.model import ModelMediation, ModelVerbosity
from nemspy.model.atmospheric import AtmosphericMesh
from nemspy.model.wave import WaveMesh


class TestModel(unittest.TestCase):
    def test_model(self):
        model = AtmosphericMesh(1, verbosity=ModelVerbosity.MINIMUM,
                                test='test2')

        self.assertEqual('ATM_model:                      atmesh\n' \
                         'ATM_petlist_bounds:             0 0\n' \
                         'ATM_attributes::\n' \
                         '  Verbosity = min\n' \
                         '  test = test2\n' \
                         '::',
                         str(model))

    def test_connection(self):
        model_1 = AtmosphericMesh(1)
        model_2 = WaveMesh(1)

        model_1.connect(model_2, ModelMediation.REDISTRIBUTE)

        self.assertEqual('ATM -> WAV   :remapMethod=redist',
                         str(model_1.connections[0]))


if __name__ == '__main__':
    unittest.main()
