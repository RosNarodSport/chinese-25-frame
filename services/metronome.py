import math
import os
import struct
import tempfile
import wave
from typing import Iterable

from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QSoundEffect

METRONOME_RATES = (40, 50, 60, 80, 100)
CLICK_TONE_HZ = 880


def _write_click_wav(path: str, volume: float, duration_ms: int = 60) -> None:
    sample_rate = 44100
    amplitude = max(0.0, min(1.0, volume))
    sample_count = max(1, int(sample_rate * duration_ms / 1000))
    with wave.open(path, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        frames = bytearray()
        for index in range(sample_count):
            t = index / sample_rate
            envelope = 1.0 - (index / sample_count)
            sample = int(
                32767 * amplitude * envelope * math.sin(2 * math.pi * CLICK_TONE_HZ * t)
            )
            frames.extend(struct.pack('<h', sample))
        wav_file.writeframes(frames)


class MetronomeController:
    def __init__(self):
        self.enabled = False
        self.bpm = 60
        self.volume = 0.8
        self._sound = QSoundEffect()
        self._wav_path = os.path.join(tempfile.gettempdir(), 'reading25_metronome.wav')
        self._refresh_sound()

    @property
    def frequency_label(self) -> str:
        return f'{self.bpm} / мин'

    def interval_ms(self) -> int:
        return max(100, int(60000 / self.bpm))

    def set_bpm(self, bpm: int) -> None:
        if bpm not in METRONOME_RATES:
            bpm = min(METRONOME_RATES, key=lambda value: abs(value - bpm))
        self.bpm = bpm

    def set_volume(self, volume_percent: int) -> None:
        self.volume = max(0.0, min(1.0, volume_percent / 100.0))
        self._sound.setVolume(self.volume)
        self._refresh_sound()

    def _refresh_sound(self) -> None:
        _write_click_wav(self._wav_path, self.volume)
        self._sound.setSource(QUrl.fromLocalFile(self._wav_path))
        self._sound.setVolume(self.volume)

    def play_tick(self) -> None:
        if not self.enabled or self.volume <= 0:
            return
        if self._sound.isPlaying():
            self._sound.stop()
        self._sound.play()


def format_rate_options(rates: Iterable[int] = METRONOME_RATES) -> str:
    return ', '.join(f'{rate} / мин' for rate in rates)
