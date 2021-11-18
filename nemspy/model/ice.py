from os import PathLike

from nemspy.model.base import EntryType, FileForcingEntry, ModelEntry


class IceModelEntry(ModelEntry):
    """
    abstraction of a generic ice model
    """

    entry_type = EntryType.ICE

    def __init__(self, processors: int, **kwargs):
        super().__init__(processors, **kwargs)


class IceForcingEntry(IceModelEntry, FileForcingEntry):
    """
    file forcing entry of an ice model
    """

    name = 'icemesh'

    def __init__(self, filename: PathLike = None, processors: int = None, **kwargs):
        if processors is None:
            processors = 1
        # Uses ww3data as name but the implementation is model agnostic
        IceModelEntry.__init__(self, processors, **kwargs)
        FileForcingEntry.__init__(self, self.entry_type, filename)
