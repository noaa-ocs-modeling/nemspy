from nemspy.model import ADCIRCEntry, AtmosphericMeshEntry, WaveWatch3MeshEntry
from nemspy.utilities import repository_root

REFERENCE_DIRECTORY = repository_root() / 'tests/reference'
ATMOSPHERIC_MESH_FILENAME = REFERENCE_DIRECTORY / 'wind_atm_fin_ch_time_vec.nc'
WAVE_MESH_FILENAME = REFERENCE_DIRECTORY / 'ww3.Constant.20151214_sxy_ike_date.nc'


def test_model():
    model = AtmosphericMeshEntry(
        ATMOSPHERIC_MESH_FILENAME, Verbosity='off', test='value', test2=5,
    )
    model.start_processor = 0

    assert (
        str(model) == 'ATM_model:                      atmesh\n'
        'ATM_petlist_bounds:             0 0\n'
        'ATM_attributes::\n'
        '  Verbosity = off\n'
        '  test = value\n'
        '  test2 = 5\n'
        '::'
    )


def test_processors():
    model_1 = AtmosphericMeshEntry(ATMOSPHERIC_MESH_FILENAME)
    model_2 = WaveWatch3MeshEntry(WAVE_MESH_FILENAME)
    model_3 = ADCIRCEntry(11)

    model_1.next = model_2
    model_2.next = model_3

    assert model_1.start_processor is None
    assert model_1.end_processor is None
    assert model_2.start_processor is None
    assert model_2.end_processor is None
    assert model_3.start_processor is None
    assert model_3.end_processor is None

    model_1.start_processor = 0

    assert model_1.start_processor == 0
    assert model_1.end_processor == 0
    assert model_2.start_processor == 1
    assert model_2.end_processor == 1
    assert model_3.start_processor == 2
    assert model_3.end_processor == 12

    model_2.processors = 3
    model_1.processors = 4

    assert model_1.start_processor == 0
    assert model_1.end_processor == 3
    assert model_2.start_processor == 4
    assert model_2.end_processor == 6
    assert model_3.start_processor == 7
    assert model_3.end_processor == 17


def test_from_string():
    model = AtmosphericMeshEntry.from_string(
        'ATM_model:                      atmesh\n'
        'ATM_petlist_bounds:             0 0\n'
        'ATM_attributes::\n'
        '  Verbosity = off\n'
        '  test = value\n'
        '  test2 = 5\n'
        '::',
        filename='wind.nc',
    )

    assert isinstance(model, AtmosphericMeshEntry)

    assert model.name == 'atmesh'
    assert model.processors == 1
    assert model.attributes == {
        'Verbosity': 'off',
        'test': 'value',
        'test2': '5',
    }
