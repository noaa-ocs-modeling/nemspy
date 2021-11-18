from os import PathLike

from nemspy.model.base import EntryType, FileForcingEntry, ModelEntry


class WaveModelEntry(ModelEntry):
    """
    abstract implementation of a generic wave model
    """

    entry_type = EntryType.WAVE

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)


class WaveWatch3ForcingEntry(WaveModelEntry, FileForcingEntry):
    """
    file forcing entry for WaveWatch III data

    >>> wave_mesh = WaveWatch3ForcingEntry(filename='ww3.Constant.20151214_sxy_ike_date.nc', processors=1)
    """

    name = 'ww3data'

    def __init__(self, filename: PathLike = None, processors: int = None, **kwargs):
        if processors is None:
            processors = 1
        # Uses ww3data as name but the implementation is model agnostic
        WaveModelEntry.__init__(self, processors, **kwargs)
        FileForcingEntry.__init__(self, self.entry_type, filename)


class WaveWatch3Entry(WaveModelEntry):
    """
    WaveWatch III model
    https://polar.ncep.noaa.gov/waves/wavewatch/
    """

    name = 'ww3'

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)


class SWANEntry(WaveModelEntry):
    """
    SWAN wave model
    http://swanmodel.sourceforge.net/
    """

    name = 'swan'

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)
