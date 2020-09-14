#!/usr/bin/env python
# flake8: noqa

from datetime import timedelta
from pathlib import Path
import sys
import tempfile
import unittest

from nemspy.configuration import Configuration, ModelSequence
from nemspy.model.atmospheric import AtmosphericMesh
from nemspy.model.base import ModelType, RemapMethod
from nemspy.model.hydrologic import NationalWaterModel
from nemspy.model.ocean import ADCIRC
from nemspy.model.wave import WaveMesh
from nemspy.utilities import repository_root


class TestConfiguration(unittest.TestCase):
    def test_connection(self):
        model_sequence = ModelSequence(timedelta(hours=1),
                                       ocean=ADCIRC(11),
                                       wave=WaveMesh(1))

        model_sequence.connect(ModelType.WAVE, ModelType.OCEAN)

        self.assertEqual(str(model_sequence.connections[0]),
                         'WAV -> OCN   :remapMethod=redist')

    def test_configuration(self):
        model_sequence = ModelSequence(timedelta(hours=1),
                                       atmospheric=AtmosphericMesh(1),
                                       wave=WaveMesh(1),
                                       ocean=ADCIRC(11),
                                       hydrological=NationalWaterModel(769))

        model_sequence.connect(ModelType.ATMOSPHERIC, ModelType.OCEAN,
                               RemapMethod.REDISTRIBUTE)
        model_sequence.connect(ModelType.WAVE, ModelType.OCEAN,
                               RemapMethod.REDISTRIBUTE)
        model_sequence.connect(ModelType.ATMOSPHERIC, ModelType.HYDROLOGICAL,
                               RemapMethod.REDISTRIBUTE)
        model_sequence.connect(ModelType.WAVE, ModelType.HYDROLOGICAL,
                               RemapMethod.REDISTRIBUTE)
        model_sequence.connect(ModelType.OCEAN, ModelType.HYDROLOGICAL,
                               RemapMethod.REDISTRIBUTE)

        configuration = Configuration(model_sequence)

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
