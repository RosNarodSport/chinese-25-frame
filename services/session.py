from models.database import get_app_opens, increment_app_opens


def record_app_open() -> int:
    increment_app_opens()
    return get_app_opens()
