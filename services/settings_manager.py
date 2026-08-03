import datetime
from typing import List, Optional, Tuple

from models.database import _execute, _fetchall, _fetchone, get_connection
from models.show_settings import ShowSettings

MAX_PRESETS = 10


def auto_preset_name(login_count: int) -> str:
    now = datetime.datetime.now()
    return f'{login_count}-{now.strftime("%d-%m-%Y-%H:%M")}'


def list_presets(user_id: int) -> List:
    return _fetchall(
        'SELECT * FROM settings_presets WHERE user_id = ? ORDER BY preset_id DESC LIMIT ?',
        (user_id, MAX_PRESETS),
    )


def get_preset(preset_id: int):
    return _fetchone('SELECT * FROM settings_presets WHERE preset_id = ?', (preset_id,))


def preset_to_settings(row) -> ShowSettings:
    return ShowSettings.from_row(row)


def save_preset(user_id: int, settings: ShowSettings, preset_name: str) -> int:
    now = datetime.datetime.now().isoformat(timespec='seconds')
    conn = get_connection()
    conn.execute(
        '''
        INSERT INTO settings_presets(
            user_id, preset_name, word_source, custom_list_id, speed_slider, color,
            start_no, article_count, font_size, shuffle, tilt_degrees,
            show_hieroglyph, show_pinyin, show_translation, show_phrase, created_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''',
        (
            user_id,
            preset_name[:15],
            settings.word_source,
            settings.custom_list_id,
            settings.speed_slider,
            settings.color,
            settings.start_no,
            settings.article_count,
            settings.font_size,
            int(settings.shuffle),
            settings.tilt_degrees,
            int(settings.show_hieroglyph),
            int(settings.show_pinyin),
            int(settings.show_translation),
            int(settings.show_phrase),
            now,
        ),
    )
    conn.commit()
    _trim_presets(user_id)
    row = _fetchone(
        'SELECT preset_id FROM settings_presets WHERE user_id = ? ORDER BY preset_id DESC LIMIT 1',
        (user_id,),
    )
    return int(row['preset_id'])


def _trim_presets(user_id: int) -> None:
    rows = _fetchall(
        'SELECT preset_id FROM settings_presets WHERE user_id = ? ORDER BY preset_id DESC',
        (user_id,),
    )
    if len(rows) <= MAX_PRESETS:
        return
    for row in rows[MAX_PRESETS:]:
        _execute('DELETE FROM settings_presets WHERE preset_id = ?', (row['preset_id'],))


def delete_preset(user_id: int, preset_id: int) -> bool:
    row = _fetchone(
        'SELECT preset_id FROM settings_presets WHERE preset_id = ? AND user_id = ?',
        (preset_id, user_id),
    )
    if not row:
        return False
    _execute('DELETE FROM settings_presets WHERE preset_id = ?', (preset_id,))
    return True


def rename_preset(user_id: int, preset_id: int, new_name: str) -> Tuple[bool, str]:
    new_name = new_name.strip()[:15]
    if not new_name:
        return False, 'Имя не может быть пустым.'
    row = _fetchone(
        'SELECT preset_id FROM settings_presets WHERE preset_id = ? AND user_id = ?',
        (preset_id, user_id),
    )
    if not row:
        return False, 'Настройка не найдена.'
    _execute(
        'UPDATE settings_presets SET preset_name = ? WHERE preset_id = ?',
        (new_name, preset_id),
    )
    return True, new_name


def count_user_presets(user_id: int) -> int:
    row = _fetchone(
        'SELECT COUNT(*) AS cnt FROM settings_presets WHERE user_id = ?',
        (user_id,),
    )
    return int(row['cnt']) if row else 0


def count_all_presets() -> int:
    row = _fetchone('SELECT COUNT(*) AS cnt FROM settings_presets')
    return int(row['cnt']) if row else 0


def get_latest_preset(user_id: int) -> Optional[ShowSettings]:
    row = _fetchone(
        'SELECT * FROM settings_presets WHERE user_id = ? ORDER BY preset_id DESC LIMIT 1',
        (user_id,),
    )
    if row:
        return preset_to_settings(row)
    return None
