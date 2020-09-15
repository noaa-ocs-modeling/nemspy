#! /usr/bin/env python
from datetime import timedelta

from nemspy import ModelingSystem
from nemspy.model.atmosphere import AtmosphericMesh
from nemspy.model.hydrology import NationalWaterModel
from nemspy.model.ocean import ADCIRC
from nemspy.model.waves import WaveMesh

if __name__ == '__main__':
    nems = ModelingSystem(timedelta(hours=1), ocean=ADCIRC(300),
                          wave=WaveMesh(),
                          atmospheric=AtmosphericMesh(),
                          hydrological=NationalWaterModel(769))
    nems.connect('atmospheric', 'ocean')
    nems.connect('wave', 'ocean')
    nems.connect('atmospheric', 'hydrological')
    nems.connect('wave', 'hydrological')
    nems.connect('ocean', 'hydrological')
    nems.write('nems.configure')
