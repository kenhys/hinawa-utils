from re import match

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

__all__ = ['BebobUnit']

class BebobUnit(Hinawa.SndUnit):
    REG_INFO = 0xffffc8020000

    def __init__(self, path):
        if match('/dev/snd/hwC[0-9]*D0', path):
            super().__init__()
            self.open(path)
            if self.get_property('type') != 3:
                raise ValueError('The character device is not for BeBoB unit')
            self._on_juju = False,
            self.listen()
        elif match('/dev/fw[0-9]*', path):
            # Just using parent class.
            super(Hinawa.FwUnit, self).__init__()
            Hinawa.FwUnit.open(self, path)
            Hinawa.FwUnit.listen(self)
            self._on_juju = True
        else:
            raise ValueError('Invalid argument for character device')
        self.fcp = Hinawa.FwFcp()
        self.fcp.listen(self)
        self.firmware_info = self._get_firmware_info()

    def _get_firmware_info(self):
        def _get_string_literal(params):
            if params[0] == 0 and params[1] == 0:
                return '00000000'
            return bytes([(params[0] >> 24) & 0xff,
                          (params[0] >> 16) & 0xff,
                          (params[0] >> 8) & 0xff,
                           params[0] & 0xff,
                          (params[1] >> 24) & 0xff,
                          (params[1] >> 16) & 0xff,
                          (params[1] >> 8) & 0xff,
                           params[1] & 0xff]).decode()
        def _get_time_literal(params):
            if params[0] == 0 and params[1] == 0:
                return '000000'
            return bytes([(params[0] >> 24) & 0xff,
                          (params[0] >> 16) & 0xff,
                          (params[0] >> 8) & 0xff,
                           params[0] & 0xff,
                          (params[1] >> 24) & 0xff,
                          (params[1] >> 16) & 0xff]).decode()
        def _get_version_literal(param):
            return '{0}.{1}.{2}'.format((param >> 24) & 0xff,
                                        (param >> 16) & 0xff,
                                        (param >> 8) & 0xff)
        def _get_id(param):
            return int(param >> 24)

        req = Hinawa.FwReq()
        params = req.read(self, BebobUnit.REG_INFO, 26)

        info = {}
        info['manufacturer'] = \
            _get_string_literal(params[0:2])
        info['protocol-version'] = \
            _get_version_literal(params[2])
        info['guid'] = \
            (params[4] << 32) | params[5]
        info['model-id'] = \
            _get_id(params[6])
        info['model-revision'] = \
            _get_id(params[7])
        info['software'] = {
            'build-date':   _get_string_literal(params[8:10]),
            'build-time':   _get_time_literal(params[10:12]),
            'id':           _get_id(params[12]),
            'version':      _get_version_literal(params[13]),
            'base-address': int(params[14]),
            'max-size':     int(params[15]),
        }
        info['bootloader'] = {
            'build-date':   _get_string_literal(params[16:18]),
            'build-time':   _get_time_literal(params[18:20]),
            'version':      _get_version_literal(params[3]),
        }
        info['debugger'] = {
            'build-date':   _get_string_literal(params[20:22]),
            'build-time':   _get_time_literal(params[22:24]),
            'id':           _get_id(params[24]),
            'version':      _get_version_literal(params[25]),
        }

        return info
