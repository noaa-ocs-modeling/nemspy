from datetime import timedelta
import unittest

from NEMSpy.model import Earth, ModelVerbosity
from NEMSpy.nems import ModelSequence


class TestNEMS(unittest.TestCase):
    def test_nems(self):
        earth = Earth(ModelVerbosity.MAXIMUM)
        model_sequence = ModelSequence(timedelta(seconds=3600))


if __name__ == '__main__':
    unittest.main()
