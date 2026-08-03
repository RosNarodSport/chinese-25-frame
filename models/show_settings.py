from dataclasses import dataclass, field, asdict
from typing import Optional


COLOR_MAP = {
    'black': '#000000',
    'green': '#008000',
    'blue': '#0000FF',
    'red': '#FF0000',
}

COLOR_LABELS = {
    '#000000': 'чёрный',
    '#008000': 'зелёный',
    '#0000FF': 'синий',
    '#FF0000': 'красный',
}

SPEED_DELAY_MIN = 0.02
SPEED_DELAY_MAX = 10.0
SPEED_SLIDER_MAX = 1000


def slider_to_delay(slider_value: int) -> float:
    ratio = slider_value / SPEED_SLIDER_MAX
    delay = SPEED_DELAY_MIN + ratio * (SPEED_DELAY_MAX - SPEED_DELAY_MIN)
    return round(delay, 2)


def delay_to_slider(delay_sec: float) -> int:
    delay_sec = min(SPEED_DELAY_MAX, max(SPEED_DELAY_MIN, float(delay_sec)))
    ratio = (delay_sec - SPEED_DELAY_MIN) / (SPEED_DELAY_MAX - SPEED_DELAY_MIN)
    return int(round(ratio * SPEED_SLIDER_MAX))


@dataclass
class ShowSettings:
    preset_name: str = 'default'
    word_source: str = 'HSK1'
    custom_list_id: Optional[int] = None
    speed_slider: float = 5.0
    color: str = '#008000'
    start_no: int = 1
    article_count: int = 150
    font_size: int = 20
    shuffle: bool = False
    tilt_degrees: int = 0
    show_hieroglyph: bool = True
    show_pinyin: bool = True
    show_translation: bool = True
    show_phrase: bool = True

    @property
    def delay_sec(self) -> float:
        return min(SPEED_DELAY_MAX, max(SPEED_DELAY_MIN, round(float(self.speed_slider), 2)))

    @property
    def delay_ms(self) -> int:
        return max(20, int(round(self.delay_sec * 1000)))

    @property
    def word_source_label(self) -> str:
        if self.custom_list_id:
            return self.preset_name or 'Пользовательский список'
        return self.word_source.upper()

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_row(cls, row) -> 'ShowSettings':
        return cls(
            preset_name=row['preset_name'] or 'default',
            word_source=row['word_source'] or 'hsk1',
            custom_list_id=row['custom_list_id'],
            speed_slider=float(row['speed_slider']),
            color=row['color'] or '#008000',
            start_no=int(row['start_no']),
            article_count=int(row['article_count']),
            font_size=int(row['font_size']),
            shuffle=bool(row['shuffle']),
            tilt_degrees=int(row['tilt_degrees']),
            show_hieroglyph=bool(row['show_hieroglyph']),
            show_pinyin=bool(row['show_pinyin']),
            show_translation=bool(row['show_translation']),
            show_phrase=bool(row['show_phrase']),
        )

    @classmethod
    def defaults(cls) -> 'ShowSettings':
        return cls()

