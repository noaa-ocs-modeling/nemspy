#! /usr/bin/env python
from datetime import timedelta

from nemspy import ModelingSystem
from nemspy.model import ADCIRC, AtmosphericMesh, NationalWaterModel, WaveMesh

if __name__ == '__main__':
    interval = timedelta(hours=1)
    ocean_model = ADCIRC(300)
    wave_mesh = WaveMesh()
    atmospheric_mesh = AtmosphericMesh()
    hydrological_model = NationalWaterModel(769)

    nems = ModelingSystem(interval, ocean=ocean_model, wave=wave_mesh,
                          atmospheric=atmospheric_mesh,
                          hydrological=hydrological_model)
    nems.connect('atmospheric', 'ocean')
    nems.connect('wave', 'ocean')
    nems.connect('atmospheric', 'hydrological')
    nems.connect('wave', 'hydrological')
    nems.connect('ocean', 'hydrological')

    print(nems)
