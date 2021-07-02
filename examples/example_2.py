#! /usr/bin/env python
from datetime import datetime, timedelta
from pathlib import Path

from nemspy import ModelingSystem
from nemspy.model import (
    ADCIRCEntry,
    AtmosphericMeshEntry,
    NationalWaterModelEntry,
    WaveWatch3MeshEntry,
)

# directory to which configuration files should be written
output_directory = Path(__file__).parent / 'output' / 'example_2'

# directory containing forcings
forcings_directory = Path(__file__).parent / 'forcings'

# model run time
start_time = datetime(2020, 6, 1)
duration = timedelta(days=1)

# returning interval of main run sequence
interval = timedelta(hours=1)

# model entries
ocean_model = ADCIRCEntry(processors=11, verbose=True, DumpFields=False)
hydrological_model = NationalWaterModelEntry(processors=769, DebugFlag=0)
atmospheric_mesh = AtmosphericMeshEntry(forcings_directory / 'wind_atm_fin_ch_time_vec.nc')
wave_mesh = WaveWatch3MeshEntry(forcings_directory / 'ww3.Constant.20151214_sxy_ike_date.nc')

# instantiate model system with model entries
nems = ModelingSystem(
    start_time,
    start_time + duration,
    interval,
    ocn=ocean_model,
    hyd=hydrological_model,
    atm=atmospheric_mesh,
    wav=wave_mesh,
)

# form connections between models
nems.connect('WAV', 'OCN')
nems.connect('ATM', 'HYD')
nems.connect('WAV', 'HYD')

# form mediations between models with custom functions
nems.mediate(sources='ATM', functions=['MedPhase_atm_ocn_flux'], targets='OCN')
nems.mediate(sources='HYD', functions=None, targets=None)
nems.mediate(sources=None, functions=['MedPhase_prep_ocn'], targets='OCN', processors=2)

# define execution order
nems.sequence = [
    'MED -> OCN',
    'ATM',
    'ATM -> MED -> OCN',
    'WAV -> OCN',
    'OCN',
    'WAV',
    'ATM -> HYD',
    'WAV -> HYD',
    'HYD',
    'HYD -> MED',
]

# write configuration files to the given directory
nems.write(output_directory, overwrite=True, include_version=True)
