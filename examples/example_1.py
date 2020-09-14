#! /usr/bin/env python
from datetime import timedelta

from nemspy import NEMS, model


def main():
    nems = NEMS()
    print(str(nems))
    nems.ocean = model.ocean.ADCIRC(300)
    nems.add_sequence(timedelta(hours=1))
    print(str(nems))
    # earth.ocean = model.ocean.ADCIRC(300)
    # earth.atmospheric = model.atmospheric.AtmosphericMeshData()
    # earth.wave = model.wave.WaveMeshData()
    # earth.hydrological = model.hydrologic.NationalWaterModel(300)
    # nems = earth.add_sequence(timedelta(hours=1))
    # nems.connect('atm', 'ocn')
    # nems.connect('wav', 'ocn')
    # nems.connect('atm', 'hyd')
    # nems.connect('wav', 'hyd')
    # nems.connect('ocn', 'hyd')
    # The order of execution is implied by the connectors.
    # The back end needs to analyze the connectors and write out the execution
    # order correctly. The user does not need to specify execution order.
    # nems.write('nems.configure')


if __name__ == '__main__':
    main()
