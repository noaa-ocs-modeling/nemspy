#! /usr/bin/env python
from datetime import datetime, timedelta

from nemspy import ModelingSystem
from nemspy.model import (
    ADCIRCEntry,
    AtmosphericMeshEntry,
    WaveMeshEntry,
)

if __name__ == '__main__':
    # model run time
    start_time = datetime(2020, 6, 1)
    duration = timedelta(days=1)

    # returning interval of main run sequence
    interval = timedelta(hours=1)

    # directory to which configuration files should be written
    output_directory = 'example_2_output'

    # model entries
    ocean_model = ADCIRCEntry(processors=11, Verbosity='max', DumpFields=False)
    atmospheric_mesh = AtmosphericMeshEntry('~/wind_atm_fin_ch_time_vec.nc')
    wave_mesh = WaveMeshEntry('~/ww3.Constant.20151214_sxy_ike_date.nc')

    # instantiate model system with model entries
    nems = ModelingSystem(
        start_time, duration, interval, ocn=ocean_model, atm=atmospheric_mesh, wav=wave_mesh,
    )

    # form connections between models
    nems.connect('ATM', 'OCN')
    nems.connect('WAV', 'OCN')

    # define execution order
    nems.sequence = [
        'ATM -> OCN',
        'WAV -> OCN',
        'ATM',
        'WAV',
        'OCN',
    ]

    # write configuration files to the given directory
    nems.write(output_directory, overwrite=True, include_version=True)
