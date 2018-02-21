from bebob.bebob_unit import BebobUnit

from bebob.maudio_protocol_normal import MaudioProtocolNormal
from bebob.maudio_protocol_fw410 import MaudioProtocolFw410
from bebob.maudio_protocol_special import MaudioProtocolSpecial

from ta1394.config_rom import Ta1394ConfigRom

__all__ = ['MaudioUnit']

class MaudioUnit(BebobUnit):
    _SUPPORTED_MODELS = (
        # VendorID, ModelID, ModelName, Protocol
        (0x000d6c, 0x00000a, MaudioProtocolNormal),  # Ozonic
        (0x000d6c, 0x010062, MaudioProtocolNormal),  # Firewire Solo
        (0x000d6c, 0x010060, MaudioProtocolNormal),  # Firewire Audiophile
        (0x000d6c, 0x010081, MaudioProtocolNormal),  # NRV10
        (0x000d6c, 0x0100a1, MaudioProtocolNormal),  # Profire Lightbridge
        (0x0007f5, 0x010046, MaudioProtocolFw410),   # Firewire 410
        (0x000d6c, 0x010071, MaudioProtocolSpecial), # Firewire 1814
        (0x000d6c, 0x010091, MaudioProtocolSpecial), # ProjectMix I/O
    )

    def __init__(self, path):
        super().__init__(path)

        rom_parser = Ta1394ConfigRom(None, None)
        info = rom_parser.parse(self.get_config_rom())
        vendor_id = -1
        model_id = -1
        for root_entry in info['root-directory']:
            if root_entry[0] == 'vendor' and root_entry[1] == 'immediate':
                vendor_id = root_entry[2]
            if root_entry[0] == 'unit' and root_entry[1] == 'directory':
                for unit_entry in root_entry[2]:
                    if (unit_entry[0] == 'model' and
                        unit_entry[1] == 'immediate'):
                        model_id = unit_entry[2]

        for entry in self._SUPPORTED_MODELS:
            if entry[0] == vendor_id and entry[1] == model_id:
                self.protocol = entry[2](self, False, model_id)
                break
        else:
            raise OSError('Not supported.')
