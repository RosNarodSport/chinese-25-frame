import datetime
from dataclasses import dataclass
from typing import Optional, Tuple, Union

from models.database import _execute, _fetchone, get_connection


@dataclass
class UserSession:
    user_id: Optional[int]
    user_name: str
    is_guest: bool = False
    is_admin: bool = False
    login_count: int = 0
    work_time_total: float = 0.0
    last_date: str = ''


def _today() -> str:
    return datetime.date.today().strftime('%d-%m-%Y')


def get_user_by_name(user_name: str):
    return _fetchone('SELECT * FROM users WHERE user_name = ?', (user_name.strip(),))


def get_user_by_id(user_id: int):
    return _fetchone('SELECT * FROM users WHERE user_id = ?', (user_id,))


def register_user(user_name: str, user_password: str) -> Tuple[bool, Union[str, UserSession]]:
    user_name = user_name.strip()
    user_password = user_password.strip()
    if not user_name:
        return False, 'Введите имя пользователя.'
    if not user_password:
        return False, 'Введите пароль.'
    if get_user_by_name(user_name):
        return False, 'Пользователь с таким именем уже существует.'

    _execute(
        'INSERT INTO users(user_name, user_password, login_count, work_time_total, last_date, is_admin) '
        'VALUES(?,?,?,?,?,?)',
        (user_name, user_password, 0, 0, _today(), 0),
    )
    row = get_user_by_name(user_name)
    return True, _row_to_session(row)


def login_user(user_name: str, user_password: str) -> Tuple[bool, Union[str, UserSession]]:
    user_name = user_name.strip()
    user_password = user_password.strip()
    if not user_name or not user_password:
        return False, 'Введите имя и пароль.'

    user = get_user_by_name(user_name)
    if not user or user['user_password'] != user_password:
        return False, 'Введены некорректные данные!'

    new_count = int(user['login_count']) + 1
    _execute(
        'UPDATE users SET login_count = ?, last_date = ? WHERE user_id = ?',
        (new_count, _today(), user['user_id']),
    )
    row = get_user_by_id(user['user_id'])
    return True, _row_to_session(row)


def login_guest() -> UserSession:
    return UserSession(
        user_id=None,
        user_name='Гость',
        is_guest=True,
        is_admin=False,
        login_count=0,
        work_time_total=0.0,
        last_date=_today(),
    )


def _row_to_session(row) -> UserSession:
    return UserSession(
        user_id=row['user_id'],
        user_name=row['user_name'],
        is_guest=False,
        is_admin=bool(row['is_admin']),
        login_count=int(row['login_count']),
        work_time_total=float(row['work_time_total']),
        last_date=row['last_date'] or '',
    )


def add_work_time(user_id: int, seconds: float) -> None:
    if user_id is None:
        return
    _execute(
        'UPDATE users SET work_time_total = work_time_total + ? WHERE user_id = ?',
        (seconds, user_id),
    )


def get_work_time(user_id: int) -> float:
    row = get_user_by_id(user_id)
    return float(row['work_time_total']) if row else 0.0
