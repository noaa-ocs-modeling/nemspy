from datetime import datetime, timedelta

from nemspy import ModelingSystem
from nemspy.model import ADCIRC, AtmosphericMesh, NationalWaterModel, WaveMesh

if __name__ == '__main__':
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
                          atm=atmospheric_mesh,
                          wav=wave_mesh,
                          ocn=ocean_model,
                          hyd=hydrological_model)

    # form connections between models
    nems.connect('WAV', 'OCN')
    nems.connect('ATM', 'HYD')
    nems.connect('WAV', 'HYD')

    # form mediations between models with custom functions
    nems.mediate('ATM', 'OCN', ['MedPhase_atm_ocn_flux'])
    nems.mediate('HYD', None)
    nems.mediate(None, 'OCN', ['MedPhase_prep_ocn'], processors=2)

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
        'HYD -> MED'
    ]

    # write configuration files to the given directory
    nems.write(output_directory, overwrite=True)
