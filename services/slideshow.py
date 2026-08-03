import random
from typing import Callable, List, Optional

from PyQt5.QtCore import QTimer, Qt

from models.database import get_custom_word_row, get_custom_words, get_hsk_entries, select_row
from models.show_settings import ShowSettings
from services.auth import add_work_time


class CardData:
    __slots__ = ('number', 'hieroglyph', 'pinyin', 'translation', 'phrase', 'hsk')

    def __init__(self, number, hieroglyph, pinyin, translation, phrase, hsk=''):
        self.number = number
        self.hieroglyph = hieroglyph
        self.pinyin = pinyin
        self.translation = translation
        self.phrase = phrase
        self.hsk = hsk


class SlideshowController:
    def __init__(self, on_update: Callable, on_finished: Callable):
        self._on_update = on_update
        self._on_finished = on_finished
        self._timer = QTimer()
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.timeout.connect(self._tick)
        self._settings = ShowSettings.defaults()
        self._queue: List[CardData] = []
        self._index = 0
        self._paused = False
        self._running = False
        self._user_id: Optional[int] = None
        self._elapsed_since_save = 0.0

    @property
    def is_running(self) -> bool:
        return self._running and not self._paused

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def current_index(self) -> int:
        return self._index

    @property
    def total(self) -> int:
        return len(self._queue)

    @property
    def settings(self) -> ShowSettings:
        return self._settings

    def set_user_id(self, user_id: Optional[int]) -> None:
        self._user_id = user_id

    def apply_settings(self, settings: ShowSettings) -> None:
        was_running = self._running
        was_paused = self._paused
        old_index = self._index
        self.stop()
        self._settings = settings
        self._queue = self.build_queue(settings)
        self._index = min(old_index, max(0, len(self._queue) - 1))
        if self._queue:
            self._emit_current()
        if was_running:
            self._running = True
            self._paused = was_paused
            if not was_paused:
                self._start_timer()

    def build_queue(self, settings: ShowSettings) -> List[CardData]:
        cards: List[CardData] = []
        if settings.custom_list_id:
            rows = get_custom_words(settings.custom_list_id)
            for row in rows:
                cards.append(
                    CardData(
                        row['number'],
                        row['hieroglyph'],
                        row['pinyin'],
                        row['translation'],
                        row['phrase'],
                        'custom',
                    )
                )
        else:
            rows = get_hsk_entries(settings.word_source)
            for row in rows:
                cards.append(
                    CardData(
                        row['number'],
                        row['hieroglyph'],
                        row['pinyin'],
                        row['translation'],
                        row['phrase'],
                        row['hsk'],
                    )
                )

        if not cards:
            return []

        start_idx = max(0, settings.start_no - 1)
        if start_idx >= len(cards):
            start_idx = 0
        ordered = cards[start_idx:] + cards[:start_idx]
        count = min(settings.article_count, len(ordered))
        ordered = ordered[:count]

        if settings.shuffle:
            random.shuffle(ordered)
        return ordered

    def start(self, settings: ShowSettings) -> None:
        self.stop()
        self._settings = settings
        self._queue = self.build_queue(settings)
        self._index = 0
        self._running = True
        self._paused = False
        if not self._queue:
            self._on_finished()
            return
        self._emit_current()
        self._start_timer()

    def pause(self) -> None:
        if not self._running:
            return
        self._paused = True
        self._timer.stop()
        self._save_elapsed()

    def resume(self) -> None:
        if not self._running or not self._paused:
            return
        self._paused = False
        self._start_timer()

    def stop(self) -> None:
        self._timer.stop()
        self._save_elapsed()
        self._running = False
        self._paused = False

    def _start_timer(self) -> None:
        self._timer.start(self._settings.delay_ms)

    def _tick(self) -> None:
        if not self._queue:
            self.stop()
            self._on_finished()
            return
        self._save_elapsed()
        self._index += 1
        if self._index >= len(self._queue):
            self.stop()
            self._on_finished()
            return
        self._emit_current()

    def _save_elapsed(self) -> None:
        if self._user_id and self._elapsed_since_save > 0:
            add_work_time(self._user_id, self._elapsed_since_save)
        self._elapsed_since_save = 0.0

    def _emit_current(self) -> None:
        if not self._queue or self._index >= len(self._queue):
            return
        card = self._queue[self._index]
        progress = int((self._index + 1) / len(self._queue) * 100)
        self._on_update(card, progress, self._settings, self._index)
        self._elapsed_since_save += self._settings.delay_sec

    def get_current_card(self) -> Optional[CardData]:
        if not self._queue or self._index >= len(self._queue):
            return None
        return self._queue[self._index]

    @staticmethod
    def fetch_card(settings: ShowSettings, number: int) -> Optional[CardData]:
        if settings.custom_list_id:
            row = get_custom_word_row(settings.custom_list_id, number)
            if not row:
                return None
            return CardData(
                row['number'],
                row['hieroglyph'],
                row['pinyin'],
                row['translation'],
                row['phrase'],
                'custom',
            )
        row = select_row(number)
        if not row:
            return None
        return CardData(
            row['number'],
            row['hieroglyph'],
            row['pinyin'],
            row['translation'],
            row['phrase'],
            row['hsk'],
        )
