# NEMSpy

[![tests](https://github.com/noaa-ocs-modeling/NEMSpy/workflows/tests/badge.svg)](https://github.com/noaa-ocs-modeling/NEMSpy/actions?query=workflow%3Atests)
[![codecov](https://codecov.io/gh/noaa-ocs-modeling/nemspy/branch/master/graph/badge.svg?token=uyeRvhmBtD)](https://codecov.io/gh/noaa-ocs-modeling/nemspy)
[![build](https://github.com/noaa-ocs-modeling/NEMSpy/workflows/build/badge.svg)](https://github.com/noaa-ocs-modeling/NEMSpy/actions?query=workflow%3Abuild)
[![version](https://img.shields.io/pypi/v/nemspy)](https://pypi.org/project/nemspy)
[![license](https://img.shields.io/github/license/noaa-ocs-modeling/nemspy)](https://creativecommons.org/share-your-work/public-domain/cc0)
[![style](https://sourceforge.net/p/oitnb/code/ci/default/tree/_doc/_static/oitnb.svg?format=raw)](https://sourceforge.net/p/oitnb/code)
[![documentation](https://readthedocs.org/projects/nemspy/badge/?version=latest)](https://nemspy.readthedocs.io/en/latest/?badge=latest)

NEMSpy generates configuration files (`nems.configure`, `config.rc`, `model_configure`, `atm_namelist.rc`)
for coupled modeling applications run with a compiled NEMS binary (not included).

```shell
pip install nemspy
```

NEMS implements
the [National Unified Operational Prediction Capability (NUOPC)](https://www.earthsystemcog.org/projects/nuopc/), and
configuration files built for NEMS will also work for most NUOPC applications.

Documentation can be found at https://nemspy.readthedocs.io

## organization / responsibility

NEMSpy is developed by the [Coastal Marine Modeling Branch (CMMB)](https://coastaloceanmodels.noaa.gov) of the Office of Coast Survey (OCS), a part of the [National Oceanic and Atmospheric Administration (NOAA)](https://www.noaa.gov), an agency of the United States federal government.

- Zachary Burnett (**lead**) - zachary.burnett@noaa.gov
- Saeed Moghimi - saeed.moghimi@noaa.gov
- Jaime Calzada (past)

## usage

```python
from datetime import datetime, timedelta
from pathlib import Path

from nemspy import ModelingSystem
from nemspy.model import ADCIRCEntry, AtmosphericForcingEntry, WaveWatch3ForcingEntry

# directory to which configuration files should be written
output_directory = Path(__file__).parent / 'nems_configuration'

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

```

## output

### `nems.configure`

```fortran
# `nems.configure` generated with NEMSpy 1.0.0
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

### `model_configure`

```fortran
# `model_configure` generated with NEMSpy 1.0.0
total_member:            1
print_esmf:              .true.
namelist:                atm_namelist.rc
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

### `config.rc`

```fortran
# `config.rc` generated with NEMSpy 1.0.0
 atm_dir: ~/forcings
 atm_nam: wind_atm_fin_ch_time_vec.nc
 wav_dir: ~/forcings
 wav_nam: ww3.Constant.20151214_sxy_ike_date.nc
```

## related projects

- [NOAA-EMC/NEMS](https://github.com/NOAA-EMC/NEMS)
- [esmf-org/esmf](https://github.com/esmf-org/esmf)
- [noaa-ocs-modeling/ADC-WW3-NWM-NEMS](https://github.com/noaa-ocs-modeling/ADC-WW3-NWM-NEMS)
