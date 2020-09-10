import unittest

from NEMSpy.model.atmospheric import ATMESH, AtmosphericModel
from NEMSpy.model.hydrologic import HydrologicalModel, NationalWaterModel
from NEMSpy.model.model import Model
from NEMSpy.model.ocean import ADCIRC, OceanModel
from NEMSpy.model.wave import WaveModel, WaveWatch3


class TestModel(unittest.TestCase):
    def test_atmesh(self):
        model = ATMESH()
        assert isinstance(model, AtmosphericModel)
        assert isinstance(model, Model)

    def test_adcirc(self):
        model = ADCIRC()
        assert isinstance(model, OceanModel)
        assert isinstance(model, Model)

    def test_ww3(self):
        model = WaveWatch3()
        assert isinstance(model, WaveModel)
        assert isinstance(model, Model)

    def test_nwm(self):
        model = NationalWaterModel()
        assert isinstance(model, HydrologicalModel)
        assert isinstance(model, Model)


if __name__ == '__main__':
    unittest.main()
