# NEMSpy
[![tests](https://github.com/noaa-ocs-modeling/NEMSpy/workflows/tests/badge.svg)](https://github.com/noaa-ocs-modeling/NEMSpy/actions?query=workflow%3Atests)
[![build](https://github.com/noaa-ocs-modeling/NEMSpy/workflows/build/badge.svg)](https://github.com/noaa-ocs-modeling/NEMSpy/actions?query=workflow%3Abuild)
[![version](https://img.shields.io/pypi/v/nemspy)](https://pypi.org/project/nemspy)
[![license](https://img.shields.io/github/license/noaa-ocs-modeling/nemspy)](https://creativecommons.org/share-your-work/public-domain/cc0)
[![style](https://sourceforge.net/p/oitnb/code/ci/default/tree/_doc/_static/oitnb.svg?format=raw)](https://sourceforge.net/p/oitnb/code)

NEMSpy generates configuration files (`nems.configure`, `config.rc`, `model_configure`, `atm_namelist.rc`) 
for coupled modeling applications run with a compiled NEMS binary (not included). 

NEMS implements the [National Unified Operational Prediction Capability (NUOPC)](https://www.earthsystemcog.org/projects/nuopc/), 
and configuration files built for NEMS will also work for most NUOPC applications.

### Usage:
```python
from datetime import datetime, timedelta

from nemspy import ModelingSystem
from nemspy.model import (
    ADCIRCEntry,
    AtmosphericMeshEntry,
    WaveMeshEntry,
)

# model run time
start_time = datetime(2020, 6, 1)
duration = timedelta(days=1)

# returning interval of main run sequence
interval = timedelta(hours=1)

# directory to which configuration files should be written
output_directory = '~/nems_configuration/'

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
```

### Output:
#### nems.configure
```fortran
# `nems.configure` generated with NEMSpy 0.5.0
# EARTH #
EARTH_component_list: ATM WAV OCN
EARTH_attributes::
  Verbosity = off
::

# ATM #
ATM_model:                      atmesh
ATM_petlist_bounds:             0 0
ATM_attributes::
  Verbosity = off
::

# WAV #
WAV_model:                      ww3data
WAV_petlist_bounds:             1 1
WAV_attributes::
  Verbosity = off
::

# OCN #
OCN_model:                      adcirc
OCN_petlist_bounds:             2 12
OCN_attributes::
  Verbosity = max
  DumpFields = false
::

# Run Sequence #
runSeq::
  @3600
    ATM -> OCN   :remapMethod=redist
    WAV -> OCN   :remapMethod=redist
    ATM
    WAV
    OCN
  @
::
```

#### model_configure
```fortran
# `model_configure` generated with NEMSpy 0.5.0
total_member:            1
print_esmf:              .true.
namelist:                atm_namelist
PE_MEMBER01:             13
start_year:              2020
start_month:             6
start_day:               1
start_hour:              0
start_minute:            0
start_second:            0
nhours_fcst:             24
RUN_CONTINUE:            .false.
ENS_SPS:                 .false.
```

#### config.rc
```fortran
# `config.rc` generated with NEMSpy 0.5.0
 atm_dir: ~
 atm_nam: wind_atm_fin_ch_time_vec.nc
 wav_dir: ~
 wav_nam: ww3.Constant.20151214_sxy_ike_date.nc
```

### Related:
- https://github.com/NOAA-EMC/NEMS
- https://github.com/esmf-org/esmf
