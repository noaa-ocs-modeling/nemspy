#! /usr/bin/env python
from datetime import timedelta

from nemspy import ModelingSystem
from nemspy.model import ADCIRC, AtmosphericMesh, NationalWaterModel, WaveMesh

if __name__ == '__main__':
    # returning interval of main run sequence
    interval = timedelta(hours=1)

    # model entries
    ocean_model = ADCIRC(processors=300, verbose=True, DumpFields=False)
    wave_mesh = WaveMesh()
    atmospheric_mesh = AtmosphericMesh()
    hydrological_model = NationalWaterModel(processors=769, DebugFlag=0)

    # instantiate model system with a specified order of execution
    nems = ModelingSystem(interval, ocean=ocean_model, wave=wave_mesh,
                          atmospheric=atmospheric_mesh,
                          hydrological=hydrological_model)

    # form connections between models using `.connect()`
    nems.connect('atmospheric', 'ocean')
    nems.connect('wave', 'ocean')
    nems.connect('atmospheric', 'hydrological')
    nems.connect('wave', 'hydrological')
    nems.connect('ocean', 'hydrological')

    print(nems)
