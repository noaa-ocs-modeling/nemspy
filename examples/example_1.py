#! /usr/bin/env python
# flake8: noqa
import sys
import pathlib
sys.path.insert(0, str((pathlib.Path(__file__).parent / '..').resolve()))

from datetime import timedelta

from nemspy.configuration import NEMSConfiguration as NEMS
from nesmpy import model

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
    nems.write('nems.configure')


if __name__ == '__main__':
    main()
