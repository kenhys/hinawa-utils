import gi
gi.require_version('Hinawa', '1.0')
from gi.repository import Hinawa

from ta1394.general import AvcConnection
from ta1394.streamformat import AvcStreamFormatInfo

import re

__all__ = ['OxfwUnit']

class OxfwUnit(Hinawa.SndUnit):
    def __init__(self, path):
        if re.match('/dev/snd/hwC[0-9]*D0', path):
            super().__init__()
            self.open(path)
            if self.get_property('type') != 4:
                raise ValueError('The character device is not for OXFW unit')
            self.listen()
            self._on_juju = False,
        elif re.match('/dev/fw[0-9]*', path):
            # Just using parent class.
            super(Hinawa.FwUnit, self).__init__()
            Hinawa.FwUnit.open(self, path)
            Hinawa.FwUnit.listen(self)
            self._on_juju = True
        else:
            raise ValueError('Invalid argument for character device')
        self.fcp = Hinawa.FwFcp()
        self.fcp.listen(self)

        self.hw_info = self._parse_hardware_info()
        self.supported_sampling_rates = self._parse_supported_sampling_rates()
        self.supported_stream_formats = self._parse_supported_stream_formats()

    def _parse_hardware_info(self):
        hw_info = {}
        req = Hinawa.FwReq()
        params = req.read(self, 0xfffff0050000, 1)
        val = params[0]
        hw_info['asic-type'] = \
            'FW{0}{1}{2}'.format((val >> 28) & 0xf,
                                 (val >> 24) & 0xf,
                                 (val >> 20) & 0xf)
        hw_info['firmware-version'] = \
            '{0}.{1}'.format((val >> 8) & 0xf,
                             (val & 0xf))
        params = req.read(self, 0xfffff0090020, 1)
        val = params[0]
        hw_info['asic-id'] = \
            bytes([(val >> 24) & 0xff,
                   (val >> 16) & 0xff,
                   (val >>  8) & 0xff,
                   (val >>  0) & 0xff]).decode().rstrip('\0')
        return hw_info

    def _parse_supported_sampling_rates(self):
        sampling_rates = {}
        playback = []
        capture  = []
        # Assume that PCM playback is available for all of models.
        for rate in AvcConnection.sampling_rates:
            if AvcConnection.ask_plug_signal_format(self.fcp, 'input', 0, rate):
                playback.append(rate)
        # PCM capture is not always available depending on models.
        for rate in AvcConnection.sampling_rates:
            if AvcConnection.ask_plug_signal_format(self.fcp, 'output', 0,rate):
                capture.append(rate)
        self._playback_only = (len(capture) == 0)
        for rate in AvcConnection.sampling_rates:
            if rate in playback or rate in capture:
                sampling_rates[rate] = True
        return sampling_rates

    def _parse_supported_stream_formats(self):
        supported_stream_formats = {}
        supported_stream_formats['playback'] = \
                        AvcStreamFormatInfo.get_formats(self.fcp, 'input', 0)
        if len(supported_stream_formats['playback']) == 0:
            supported_stream_formats['playback'] = \
                        self._assume_supported_stram_formats('input', 0)
            self._assumed = True
        else:
            self._assumed = False
        if not self._playback_only:
            supported_stream_formats['capture'] = \
                        AvcStreamFormatInfo.get_formats(self.fcp, 'output', 0)
            if len(supported_stream_formats['capture']) == 0:
                supported_stream_formats['capture'] = \
                        self._assume_supported_stram_formats('output', 0)
        return supported_stream_formats

    def _assume_supported_stram_formats(self, direction, plug):
        assumed_stream_formats = []
        fmt = AvcStreamFormatInfo.get_format(self.fcp, 'input', 0)
        for rate, state in self.supported_sampling_rates.items():
            if state:
                assumed = {
                    'sampling-rate':    rate,
                    'rate-control':     fmt['rate-control'],
                    'formation':        fmt['formation']}
                assumed_stream_formats.append(assumed)
        return assumed_stream_formats

    def set_stream_formats(self, playback, capture):
        if playback not in self.supported_stream_formats['playback']:
            raise ValueError('Invalid argument for playback stream format')
        if capture:
            if self._playback_only:
                raise ValueError('This unit is playback only')
            if capture not in self.supported_stream_formats['capture']:
                raise ValueError('Invalid argument for capture stream format')
            if playback['sampling-rate'] != capture['sampling-rate']:
                raise ValueError('Sampling rate mis-match between playback and capture')
        if self._assumed:
            rate = playback['sampling-rate']
            AvcConnection.set_plug_signal_format(self.fcp, 'output', 0, rate)
            AvcConnection.set_plug_signal_format(self.fcp, 'input', 0, rate)
        else:
            AvcStreamFormatInfo.set_format(self.fcp, 'input', 0, playback)
            if not self._playback_only:
                AvcStreamFormatInfo.set_format(self.fcp, 'output', 0, capture)

    def get_current_stream_formats(self):
        playback = AvcStreamFormatInfo.get_format(self.fcp, 'input', 0)
        if not self._playback_only:
            capture = AvcStreamFormatInfo.get_format(self.fcp, 'output', 0)
        else:
            capture = None
        return {'playback': playback, 'capture': capture}
