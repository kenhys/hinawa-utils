import gi
gi.require_version('Hinawa', '2.0')
from gi.repository import Hinawa

from tscm.tscm_unit import TscmUnit

__all__ = ['TscmConsoleUnit']

class TscmConsoleUnit(TscmUnit):
    def __init__(self, path):
        super().__init__(path)

    def bright_led(self, position, state):
        if state not in self.supported_led_status:
            raise ValueError('Invalid argument for LED state.')
        frames = bytearray(4)
        frames[3] = position
        if self.supported_led_status.index(state) == 1:
            frames[1] = 0x01
        self.write_quadlet(0x0404, frames)

    def set_master_fader(self, mode):
        frames = bytearray(4)
        if mode:
            frames[2] = 0x40
        else:
            frames[1] = 0x40
        self.write_quadlet(0x022c, frames)
    def get_master_fader(self):
        frames = self.read_quadlet(0x022c)
        return bool(frames[3] & 0x40)