#! /usr/bin/env python
from datetime import datetime, timedelta
from pathlib import Path

from nemspy import ModelingSystem
from nemspy.model import ADCIRCEntry, AtmosphericForcingEntry, WaveWatch3ForcingEntry

# directory to which configuration files should be written
output_directory = Path(__file__).parent / 'output' / 'example_1'

# directory containing forcings
forcings_directory = Path(__file__).parent / 'forcings'

# model run time
start_time = datetime(2020, 6, 1)
duration = timedelta(days=1)
end_time = start_time + duration

# returning interval of main run sequence
interval = timedelta(hours=1)

# model entries
ocean_model = ADCIRCEntry(processors=11, Verbosity='max', DumpFields=False)
atmospheric_mesh = AtmosphericForcingEntry(
    filename=forcings_directory / 'wind_atm_fin_ch_time_vec.nc', processors=1
)
wave_mesh = WaveWatch3ForcingEntry(
    filename=forcings_directory / 'ww3.Constant.20151214_sxy_ike_date.nc', processors=1
)

# instantiate model system with model entries
nems = ModelingSystem(
    start_time=start_time,
    end_time=end_time,
    interval=interval,
    ocn=ocean_model,
    atm=atmospheric_mesh,
    wav=wave_mesh,
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
nems.write(directory=output_directory, overwrite=True, include_version=True)
