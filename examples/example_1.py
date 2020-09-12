#! /usr/bin/env python
# flake8: noqa
import sys
import pathlib
sys.path.insert(0, str((pathlib.Path(__file__).parent / '..').resolve())) # This can be removed if setup.py is created

from datetime import timedelta

from nemspy.configuration import NEMSConfiguration as NEMS # I would just call it NEMS

from nesmpy import model as models


from adcircpy import AdcircRun
from NWMPy import NWMDriver  # This doesn't exist.


def main():
    args = []
    kwargs = {}
    nems = NEMS(
        ocean=models.ADCIRC(300, AdcircRun(*args, **kwargs)),
        atmospheric=models.AtmosphericMeshData('/path/to/wind_data.nc'),  # this is always 1 core
        waves=models.WavesMeshData('/path/to/wave_data.nc'), # this is always 1 core
        hydrologic=models.NationalWaterModel(300, NWMDriver(*args, **kwargs))
        )
    seq = nems.add_sequence(timedelta(hours=1))
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
