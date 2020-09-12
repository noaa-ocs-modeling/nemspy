#! /usr/bin/env python
from datetime import timedelta

from nemspy import NEMS, model


def main():
    nems = NEMS(
        ocean=model.ocean.ADCIRC(300),
        atmospheric=model.atmospheric.AtmosphericMeshData(),
        waves=model.waves.WaveMeshData(),
        hydrologic=model.hydrologic.NationalWaterModel(300)
        )
    print(nems.configuration)
    seq = nems.add_sequence(timedelta(hours=1))
    print(nems.configuration)
    seq.connect('atm', 'ocn')
    seq.connect('wav', 'ocn')
    seq.connect('atm', 'hyd')
    seq.connect('wav', 'hyd')
    seq.connect('ocn', 'hyd')
    # The order of execution is implied by the connectors.
    # The back end needs to analyze the connectors and write out the execution
    # order correctly. The user does not need to specify execution order.
    nems.write('nems.configure')


if __name__ == '__main__':
    main()
