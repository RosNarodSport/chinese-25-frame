import os
import shutil
import sqlite3
import sys
from typing import Any, Optional

from data.hieroglyphs import hsk

DB_FILENAME = 'hsk_base.db'
_connection: Optional[sqlite3.Connection] = None


def project_root() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bundled_resource_path(relative_path: str) -> str:
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(project_root(), relative_path)


def get_db_path() -> str:
    db_path = os.path.join(project_root(), DB_FILENAME)
    if not os.path.exists(db_path):
        bundled = bundled_resource_path(DB_FILENAME)
        if os.path.exists(bundled):
            shutil.copy2(bundled, db_path)
    return db_path


def get_connection() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(get_db_path())
        _connection.row_factory = sqlite3.Row
    return _connection


def _execute(sql: str, params: tuple = ()) -> None:
    conn = get_connection()
    conn.execute(sql, params)
    conn.commit()


def _fetchone(sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
    return get_connection().execute(sql, params).fetchone()


def _fetchall(sql: str, params: tuple = ()) -> list:
    return get_connection().execute(sql, params).fetchall()


def create_tables() -> None:
    conn = get_connection()
    conn.executescript(
        '''
        CREATE TABLE IF NOT EXISTS main_table_for_show(
            number INTEGER,
            hieroglyph TEXT,
            pinyin TEXT,
            translation TEXT,
            phrase TEXT,
            hsk TEXT
        );

        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT UNIQUE NOT NULL,
            user_password TEXT NOT NULL,
            login_count INTEGER DEFAULT 0,
            work_time_total REAL DEFAULT 0,
            last_date TEXT,
            is_admin INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS settings_presets(
            preset_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            preset_name TEXT NOT NULL,
            word_source TEXT DEFAULT 'HSK1',
            custom_list_id INTEGER,
            speed_slider REAL DEFAULT 5.0,
            color TEXT DEFAULT '#008000',
            start_no INTEGER DEFAULT 1,
            article_count INTEGER DEFAULT 150,
            font_size INTEGER DEFAULT 20,
            shuffle INTEGER DEFAULT 0,
            tilt_degrees INTEGER DEFAULT 0,
            show_hieroglyph INTEGER DEFAULT 1,
            show_pinyin INTEGER DEFAULT 1,
            show_translation INTEGER DEFAULT 1,
            show_phrase INTEGER DEFAULT 1,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS custom_word_lists(
            list_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            card_count INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS custom_words(
            word_id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id INTEGER NOT NULL,
            number INTEGER NOT NULL,
            hieroglyph TEXT,
            pinyin TEXT,
            translation TEXT,
            phrase TEXT,
            FOREIGN KEY(list_id) REFERENCES custom_word_lists(list_id)
        );

        CREATE TABLE IF NOT EXISTS app_stats(
            stat_key TEXT PRIMARY KEY,
            stat_value REAL DEFAULT 0
        );
        '''
    )
    conn.commit()


def seed_hsk() -> None:
    row = _fetchone('SELECT COUNT(*) AS cnt FROM main_table_for_show')
    if row and row['cnt'] > 0:
        return
    conn = get_connection()
    for entry in hsk:
        conn.execute(
            'INSERT INTO main_table_for_show VALUES(?,?,?,?,?,?)',
            (entry[0], entry[1], entry[2], entry[3], entry[4], entry[5]),
        )
    conn.commit()


def seed_admin_and_stats() -> None:
    admin = _fetchone('SELECT user_id FROM users WHERE user_name = ?', ('admin',))
    if not admin:
        _execute(
            'INSERT INTO users(user_name, user_password, login_count, work_time_total, last_date, is_admin) '
            'VALUES(?,?,?,?,?,?)',
            ('admin', 'admin', 0, 0, '', 1),
        )
    stats = _fetchone('SELECT stat_value FROM app_stats WHERE stat_key = ?', ('total_app_opens',))
    if not stats:
        _execute('INSERT INTO app_stats(stat_key, stat_value) VALUES(?,?)', ('total_app_opens', 0))


def ensure_database() -> None:
    create_tables()
    seed_hsk()
    seed_admin_and_stats()


def increment_app_opens() -> None:
    _execute(
        'INSERT INTO app_stats(stat_key, stat_value) VALUES(?, 1) '
        'ON CONFLICT(stat_key) DO UPDATE SET stat_value = stat_value + 1',
        ('total_app_opens',),
    )


def get_app_opens() -> int:
    row = _fetchone('SELECT stat_value FROM app_stats WHERE stat_key = ?', ('total_app_opens',))
    return int(row['stat_value']) if row else 0


def select_row(number: int) -> Optional[sqlite3.Row]:
    return _fetchone('SELECT * FROM main_table_for_show WHERE number = ?', (number,))


def select_row_field(number: int, field_index: int) -> Any:
    row = select_row(number)
    if not row:
        return ''
    columns = ['number', 'hieroglyph', 'pinyin', 'translation', 'phrase', 'hsk']
    return row[columns[field_index]]


def get_hsk_entries(hsk_group: str) -> list:
    normalized = hsk_group.upper()
    if not normalized.startswith('HSK'):
        normalized = f'HSK{normalized.replace("HSK", "")}'
    return _fetchall(
        'SELECT * FROM main_table_for_show WHERE hsk = ? ORDER BY number',
        (normalized,),
    )


def get_hsk_count(hsk_group: str) -> int:
    normalized = hsk_group.upper()
    if not normalized.startswith('HSK'):
        normalized = f'HSK{normalized.replace("HSK", "")}'
    row = _fetchone(
        'SELECT COUNT(*) AS cnt FROM main_table_for_show WHERE hsk = ?',
        (normalized,),
    )
    return int(row['cnt']) if row else 0


def get_custom_words(list_id: int) -> list:
    return _fetchall(
        'SELECT * FROM custom_words WHERE list_id = ? ORDER BY number',
        (list_id,),
    )


def get_custom_word_row(list_id: int, number: int) -> Optional[sqlite3.Row]:
    return _fetchone(
        'SELECT * FROM custom_words WHERE list_id = ? AND number = ?',
        (list_id, number),
    )
