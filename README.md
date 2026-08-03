# 25-й кадр — китайский язык

Desktop-приложение на PyQt5 для изучения китайского языка методом быстрого показа карточек (HSK 1–4, пользовательские списки, настройки показа, админ-панель).

## Требования

- Windows 10/11
- Python 3.10+

## Установка

```powershell
pip install -r requirements.txt
```

## Запуск из исходников

```powershell
python main.py
```

## Сборка exe

```powershell
python -m PyInstaller --noconfirm build\Reading25.spec
```

Готовый файл: `dist\Reading25.exe`

## Структура

- `main.py` — точка входа и UI
- `models/` — SQLite и настройки показа
- `services/` — авторизация, слайдшоу, импорт Excel, тема
- `views/main_window.ui` — интерфейс Qt Designer
- `data/hieroglyphs.py` — словарь HSK
