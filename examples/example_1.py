#! /usr/bin/env python
# flake8: noqa
import sys
import pathlib
sys.path.insert(0, str((pathlib.Path(__file__).parent / '..').resolve())) # This can be removed if setup.py is created

from datetime import timedelta

from nemspy.configuration import NEMSConfiguration as NEMS # I would just call it NEMS

from nesmpy import model # the model namespace is too long having to acces each model from each file.


from adcircpy import AdcircRun
from NWMPy import NWMDriver  # This doesn't exist.


def main():
    args = []
    kwargs = {}
    ocn = model.ADCIRC(300, AdcircRun(*args, **kwargs))
    wnd = model.ATMesh('/path/to/wind_data.nc')  # this is always 1 core
    wav = model.WW3Data('/path/to/wave_data.nc') # this is always 1 core
    hyd = model.NationalWaterModel(300, NWMDriver(*args, **kwargs))
    nems = NEMS(ocn=ocn, atm=wnd, wav=wav, hyd=hyd)
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
