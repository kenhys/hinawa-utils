# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2018 Takashi Sakamoto

import sys
import string
from pathlib import Path

import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

__all__ = ['CuiKit']

class CuiKit():
    @staticmethod
    def _seek_snd_unit_from_guid(guid):
        for fullpath in Path('/dev/snd').glob('hw*'):
            fullpath = str(fullpath)
            try:
                unit = Hinawa.SndUnit()
                unit.open(fullpath)
                if unit.get_property('guid') == guid:
                    return fullpath
            except Exception as e:
                pass
            finally:
                del unit
        return None

    @staticmethod
    def _check_hexadecimal(literal):
        if literal.find('0x') == 0:
            literal = literal[2:]
        if len(literal) != 16:
            return False
        for character in literal:
            if character not in string.hexdigits:
                return False
        else:
            return True

    @staticmethod
    def _dump_help(cmdline):
        print('{0} CARD|GUID [FILE|CMD [ARGS]]'.format(cmdline))
        print('  CARD:  the number as ALSA sound card, see /proc/asound/cards.')
        print('  GUID:  global unique ID for your unit.')
        print('  FILE:  path for a file with command list')
        print('  CMD:   issue which you need')
        print('  ARGS:  arguments for the command')

    @staticmethod
    def _dump_commands(cmds):
        print('Available commands:')
        for name in cmds.keys():
            print('  {0}'.format(name))

    @classmethod
    def seek_snd_unit_path(cls):
        args = sys.argv
        if len(args) > 1:
            identity = args[1]
            # Assume as sound card number if it's digit literal.
            if identity.isdigit():
                return '/dev/snd/hwC{0}D0'.format(identity)
            # Assume as GUID on IEEE 1394 bus if it's hexadecimal literal.
            elif cls._check_hexadecimal(identity):
                return cls._seek_snd_unit_from_guid(int(identity, base=16))
        cls._dump_help(args[0])
        return None

    @classmethod
    def dispatch_command(cls, unit, cmds):
        args = sys.argv
        if len(args) > 2:
            if args[2] in cmds:
                cmd = args[2]
                return cmds[cmd](unit, args[3:])
            path = Path(args[2])
            if path.is_file():
                with path.open(mode='r') as fh:
                    for i, line in enumerate(fh):
                        args = line.rstrip().split(' ')
                        if len(args) == 0:
                            continue

                        cmd = args[0]
                        if len(cmd) == 0:
                            continue
                        if cmd[0] == '#':
                            continue
                        if cmd not in cmds:
                            print('Invalid command in {0}: {1}: {2}'.format(
                                                        str(path), i, cmd))
                            return False

                        if not cmds[cmd](unit, args[1:]):
                            print('Invalid arguments in {0}:{1}: {2}'.format(
                                                        str(path), i, cmd))
                            return False
                return True
        cls._dump_commands(cmds)
        return False
