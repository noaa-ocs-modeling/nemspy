from datetime import timedelta
import unittest

from nemspy.model import Earth, ModelVerbosity
from nemspy.nems import ModelSequence


class TestNEMS(unittest.TestCase):
    def test_nems(self):
        earth = Earth(ModelVerbosity.MAXIMUM)
        model_sequence = ModelSequence(timedelta(seconds=3600))


if __name__ == '__main__':
    unittest.main()
