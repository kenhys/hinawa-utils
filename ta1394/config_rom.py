from ieee1394.config_rom import Ieee1394ConfigRom

from struct import unpack

__all__ = ['1394taConfigRom', ]

class Ta1394ConfigRom(Ieee1394ConfigRom):
    def __init__(self, spec_entry_defs, vendor_entry_defs):
        super().__init__(spec_entry_defs, vendor_entry_defs)
