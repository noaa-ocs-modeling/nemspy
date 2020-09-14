import unittest

from nemspy.model import ModelMediation, ModelVerbosity
from nemspy.model.atmospheric import ATMeshData
from nemspy.model.wave import WaveWatch3Data


class TestModel(unittest.TestCase):
    def test_model(self):
        model = ATMeshData(1, verbosity=ModelVerbosity.MINIMUM, test='test2')

        assert str(model) == 'ATM_model:                      atmesh\n' \
                             'ATM_petlist_bounds:             0 0\n' \
                             'ATM_attributes::\n' \
                             '  Verbosity = min\n' \
                             '  test = test2\n' \
                             '::'

    def test_connection(self):
        model_1 = ATMeshData(1)
        model_2 = WaveWatch3Data(1)

        model_1.connect(model_2, ModelMediation.REDISTRIBUTE)

        assert str(model_1.connections[0]) == \
               'ATM -> WAV   :remapMethod=redist'


if __name__ == '__main__':
    unittest.main()
