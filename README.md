# NEMSpy
### configuration for the NOAA Environmental Modeling System (NEMS)

[![tests](https://github.com/noaa-ocs-modeling/NEMSpy/workflows/tests/badge.svg)](https://github.com/noaa-ocs-modeling/NEMSpy/actions?query=workflow%3Atests)
[![build](https://github.com/noaa-ocs-modeling/NEMSpy/workflows/build/badge.svg)](https://github.com/noaa-ocs-modeling/NEMSpy/actions?query=workflow%3Abuild)

NEMSpy generates configuration files (`nems.configure`, `config.rc`, `model_configure`, `atm_namelist.rc`) 
for coupled modeling applications run with a compiled NEMS binary (not included). 

NEMS implements the [National Unified Operational Prediction Capability (NUOPC)](https://www.earthsystemcog.org/projects/nuopc/), 
and configuration files built for NEMS will also work for most NUOPC applications.

#### Usage:
```python
from datetime import datetime, timedelta

from nemspy import ModelingSystem
from nemspy.model import ADCIRC, AtmosphericMesh, NationalWaterModel, WaveMesh

# model run time
start_time = datetime(2020, 6, 1)
duration = timedelta(days=1)

# returning interval of main run sequence
interval = timedelta(hours=1)

# directory to which configuration files should be written
output_directory = '~/nems_configuration/'

# model entries
atmospheric_mesh = AtmosphericMesh('~/wind_atm_fin_ch_time_vec.nc')
wave_mesh = WaveMesh('~/ww3.Constant.20151214_sxy_ike_date.nc')
ocean_model = ADCIRC(processors=11, verbose=True, DumpFields=False)
hydrological_model = NationalWaterModel(processors=769, DebugFlag=0)

# instantiate model system with a specified order of execution
nems = ModelingSystem(start_time, duration, interval,
                      atmospheric=atmospheric_mesh,
                      wave=wave_mesh, 
                      ocean=ocean_model,
                      hydrological=hydrological_model)

# form connections between models using `.connect()`
nems.connect('atmospheric', 'ocean')
nems.connect('wave', 'ocean')
nems.connect('atmospheric', 'hydrological')
nems.connect('wave', 'hydrological')
nems.connect('ocean', 'hydrological')

# write configuration files to the given directory
nems.write(output_directory)
```

#### Output:

###### nems.configure
```fortran
#############################################
####  NEMS Run-Time Configuration File  #####
#############################################

# EARTH #
EARTH_component_list: ATM WAV OCN HYD
EARTH_attributes::
  Verbosity = min
::

# ATM #
ATM_model:                      atmesh
ATM_petlist_bounds:             0 0
ATM_attributes::
  Verbosity = min
::

# WAV #
WAV_model:                      ww3data
WAV_petlist_bounds:             1 1
WAV_attributes::
  Verbosity = min
::

# OCN #
OCN_model:                      adcirc
OCN_petlist_bounds:             2 12
OCN_attributes::
  Verbosity = max
  DumpFields = false
::

# HYD #
HYD_model:                      nwm
HYD_petlist_bounds:             13 781
HYD_attributes::
  Verbosity = min
  DebugFlag = 0
::

# Run Sequence #
runSeq::
  @3600
    ATM -> OCN   :remapMethod=redist
    WAV -> OCN   :remapMethod=redist
    ATM -> HYD   :remapMethod=redist
    WAV -> HYD   :remapMethod=redist
    OCN -> HYD   :remapMethod=redist
    ATM
    WAV
    OCN
    HYD
  @
::
```

###### config.rc
```fortran
 atm_dir: ~
 atm_nam: wind_atm_fin_ch_time_vec.nc
 wav_dir: ~
 wav_nam: ww3.Constant.20151214_sxy_ike_date.nc
```

###### model_configure
```fortran
core: gfs
print_esmf:     .true.

nhours_dfini=0

#nam_atm +++++++++++++++++++++++++++
nlunit:                  35
deltim:                  900.0
fhrot:                   0
namelist:                atm_namelist
total_member:            1
grib_input:              0
PE_MEMBER01:             782
PE_MEMBER02
PE_MEMBER03
PE_MEMBER04
PE_MEMBER05
PE_MEMBER06
PE_MEMBER07
PE_MEMBER08
PE_MEMBER09
PE_MEMBER10
PE_MEMBER11
PE_MEMBER12
PE_MEMBER13
PE_MEMBER14
PE_MEMBER15
PE_MEMBER16
PE_MEMBER17
PE_MEMBER18
PE_MEMBER19:
PE_MEMBER20:
PE_MEMBER21:

# For stochastic perturbed runs -  added by Dhou and Wyang
--------------------------------------------------------
#  ENS_SPS, logical control for application of stochastic perturbation scheme
#  HH_START, start hour of forecast, and modified ADVANCECOUNT_SETUP
#  HH_INCREASE and HH_FINAL are fcst hour increment and end hour of forecast
#  ADVANCECOUNT_SETUP is an integer indicating the number of time steps between integration_start and the time when model state is saved for the _ini of the GEFS_Coupling, currently is 0h.

HH_INCREASE:             600
HH_FINAL:                600
HH_START:                0
ADVANCECOUNT_SETUP:      0

ENS_SPS:                 .false.
HOUTASPS:                10000

#ESMF_State_Namelist +++++++++++++++

RUN_CONTINUE:            .false.

#
dt_int:                  900
dt_num:                  0
dt_den:                  1
start_year:              2020
start_month:             6
start_day:               1
start_hour:              0
start_minute:            0
start_second:            0
nhours_fcst:             24
restart:                 .false.
nhours_fcst1:            24
im:                      192
jm:                      94
global:                  .true.
nhours_dfini:            0
adiabatic:               .false.
lsoil:                   4
passive_tracer:          .true.
dfilevs:                 64
ldfiflto:                .true.
num_tracers:             3
ldfi_grd:                .false.
lwrtgrdcmp:              .false.
nemsio_in:               .false.


#jwstart added quilt
###############################
#### Specify the I/O tasks ####
###############################


quilting:                .false.   #For asynchronous quilting/history writes
read_groups:             0
read_tasks_per_group:    0
write_groups:            1
write_tasks_per_group:   3

num_file:                3                   #
filename_base:           'SIG.F' 'SFC.F' 'FLX.F'
file_io_form:            'bin4' 'bin4' 'bin4'
file_io:                 'DEFERRED' 'DEFERRED' 'DEFERRED' 'DEFERRED'  #
write_dopost:            .false.          # True--> run do on quilt
post_gribversion:        grib1      # True--> grib version for post output files
gocart_aer2post:         .false.
write_nemsioflag:        .TRUE.       # True--> Write nemsio run history files
nfhout:                  3
nfhout_hf:               1
nfhmax_hf:               0
nsout:                   0

io_recl:                 100
io_position:             ' '
io_action:               'WRITE'
io_delim:                ' '
io_pad:                  ' '

#jwend
```

#### Related:
- https://github.com/NOAA-EMC/NEMS
- https://github.com/esmf-org/esmf
