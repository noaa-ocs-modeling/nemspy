from datetime import timedelta
from pathlib import Path
import tempfile
import unittest

from nemspy import repository_root
from nemspy.configuration import ModelSequence, NEMSConfiguration
from nemspy.model import ModelMediation, ModelType
from nemspy.model.atmospheric import AtmosphericMesh
from nemspy.model.hydrologic import NationalWaterModel
from nemspy.model.ocean import ADCIRC
from nemspy.model.wave import WaveMesh


class TestConfiguration(unittest.TestCase):
    def test_configuration(self):
        models = {
            ModelType.ATMOSPHERIC: AtmosphericMesh(1),
            ModelType.WAVE: WaveMesh(1),
            ModelType.OCEAN: ADCIRC(11),
            ModelType.HYDROLOGICAL: NationalWaterModel(769)
        }

        models[ModelType.ATMOSPHERIC].connect(models[ModelType.OCEAN],
                                              ModelMediation.REDISTRIBUTE)
        models[ModelType.WAVE].connect(models[ModelType.OCEAN],
                                       ModelMediation.REDISTRIBUTE)
        models[ModelType.ATMOSPHERIC].connect(models[ModelType.HYDROLOGICAL],
                                              ModelMediation.REDISTRIBUTE)
        models[ModelType.OCEAN].connect(models[ModelType.HYDROLOGICAL],
                                        ModelMediation.REDISTRIBUTE)

        model_sequence = ModelSequence(timedelta(hours=1),
                                       **{model_type.name: model for
                                          model_type, model in models.items()})
        configuration = NEMSConfiguration(model_sequence)

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_filename = Path(temporary_directory) / 'test.configure'
            configuration.write(temporary_filename)
            with open(temporary_filename) as temporary_file:
                with open(repository_root() /
                          'tests/reference/nems.configure') as reference_file:
                    self.assertEqual(temporary_file.read(),
                                     reference_file.read())


if __name__ == '__main__':
    unittest.main()
