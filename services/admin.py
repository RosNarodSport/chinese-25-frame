from typing import List, Tuple

from models.database import _execute, _fetchall, _fetchone
from services.settings_manager import count_all_presets


def list_users() -> List:
    return _fetchall('SELECT * FROM users ORDER BY user_id')


def count_users() -> int:
    row = _fetchone('SELECT COUNT(*) AS cnt FROM users')
    return int(row['cnt']) if row else 0


def delete_user(user_id: int) -> Tuple[bool, str]:
    user = _fetchone('SELECT * FROM users WHERE user_id = ?', (user_id,))
    if not user:
        return False, 'Пользователь не найден.'
    if user['user_name'] == 'admin':
        return False, 'Нельзя удалить admin.'
    _execute('DELETE FROM settings_presets WHERE user_id = ?', (user_id,))
    lists = _fetchall('SELECT list_id FROM custom_word_lists WHERE user_id = ?', (user_id,))
    for lst in lists:
        _execute('DELETE FROM custom_words WHERE list_id = ?', (lst['list_id'],))
    _execute('DELETE FROM custom_word_lists WHERE user_id = ?', (user_id,))
    _execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    return True, 'Пользователь удалён.'


def update_user_credentials(user_id: int, new_name: str, new_password: str) -> Tuple[bool, str]:
    new_name = new_name.strip()
    new_password = new_password.strip()
    if not new_name or not new_password:
        return False, 'Имя и пароль обязательны.'
    existing = _fetchone(
        'SELECT user_id FROM users WHERE user_name = ? AND user_id != ?',
        (new_name, user_id),
    )
    if existing:
        return False, 'Имя уже занято.'
    _execute(
        'UPDATE users SET user_name = ?, user_password = ? WHERE user_id = ?',
        (new_name, new_password, user_id),
    )
    return True, 'Данные обновлены.'


def get_admin_metrics(app_opens: int) -> dict:
    return {
        'users_count': count_users(),
        'presets_count': count_all_presets(),
        'app_opens': app_opens,
    }
