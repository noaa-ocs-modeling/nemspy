from datetime import timedelta
import unittest

from nemspy.configuration import ModelSequence
from nemspy.model import Earth, ModelVerbosity
from nemspy.model.atmospheric import ATMeshData
from nemspy.model.hydrologic import NationalWaterModel
from nemspy.model.ocean import ADCIRC
from nemspy.model.wave import WaveWatch3Data


class TestNEMS(unittest.TestCase):
    def test_nems(self):
        atm = ATMeshData(1)
        wav = WaveWatch3Data(1, previous=atm)
        ocn = ADCIRC(11, previous=wav)
        hyd = NationalWaterModel(769, previous=ocn)

        earth = Earth(ModelVerbosity.MAXIMUM, ATMOSPHERIC=atm, WAVE=wav,
                      OCEAN=ocn, HYD=hyd)
        model_sequence = ModelSequence(timedelta(hours=1))


if __name__ == '__main__':
    unittest.main()
