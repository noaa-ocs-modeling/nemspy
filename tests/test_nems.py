from datetime import timedelta
from pathlib import Path
import tempfile
import unittest

from nemspy import repository_root
from nemspy.configuration import ModelSequence, NEMSConfiguration
from nemspy.model import Earth, ModelType, ModelVerbosity
from nemspy.model.atmospheric import ATMeshData
from nemspy.model.hydrologic import NationalWaterModel
from nemspy.model.ocean import ADCIRC
from nemspy.model.wave import WaveWatch3Data


class TestConfiguration(unittest.TestCase):
    def test_configuration(self):
        atmesh = ATMeshData(1)
        ww3data = WaveWatch3Data(1, previous=atmesh)
        adcirc = ADCIRC(11, previous=ww3data)
        nwm = NationalWaterModel(769, previous=adcirc)

        atmesh.connect(adcirc)
        ww3data.connect(adcirc)
        atmesh.connect(nwm)
        adcirc.connect(nwm)

        order = [ModelType.ATMOSPHERIC, ModelType.WAVE, ModelType.OCEAN,
                 ModelType.HYDROLOGICAL]

        earth = Earth(ModelVerbosity.MAXIMUM, ATMOSPHERIC=atmesh, WAVE=ww3data,
                      OCEAN=adcirc, HYDROLOGICAL=nwm)
        model_sequence = ModelSequence(timedelta(hours=1), order, EARTH=earth)
        configuration = NEMSConfiguration(earth, model_sequence)

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_filename = Path(temporary_directory) / 'test.configure'
            configuration.write(temporary_filename)
            with open(temporary_filename) as temporary_file:
                with open(repository_root() /
                          'tests/reference/nems.configure') as reference_file:
                    assert temporary_file.read() == reference_file.read()


if __name__ == '__main__':
    unittest.main()
