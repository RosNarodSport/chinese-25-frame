import html
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

BASE = 'https://www.trainchinese.com/v2'
LOGIN = os.environ.get('TRAINCHINESE_USER', '')
PASSWORD = os.environ.get('TRAINCHINESE_PASS', '')
PARENT_FOLDER_ID = 27

CATEGORY_NAMES = [
    'Средства массовой информации',
    'Ванная комната',
    'Детская одежда',
    'Компьютер',
    'Кухонная посуда',
    'Кухонная посуда 2',
    'Мебель',
    'Одежда',
    'Письменные принадлежности',
    'Принадлежности для женщин',
    'Принадлежности для мужчин',
    'Уход за детьми',
    'Электрические системы',
    'Ювелирные изделия',
]


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
        }
    )
    return session


def login(session: requests.Session) -> str:
    if not LOGIN or not PASSWORD:
        raise RuntimeError('Задайте TRAINCHINESE_USER и TRAINCHINESE_PASS')
    response = session.post(
        f'{BASE}/index.php',
        data={
            'uname': LOGIN,
            'pass': PASSWORD,
            'rememberMe': '1',
            'tcLanguage': 'ru',
            'difTimeMin': '0',
        },
        timeout=30,
    )
    response.raise_for_status()
    rap = session.cookies.get('rAp')
    if not rap:
        raise RuntimeError('Не удалось войти на trainchinese.com')
    return rap


def fetch_list_js(session: requests.Session, rap: str, list_id: int) -> str:
    response = session.get(
        f'{BASE}/contentsGetList.php',
        params={'rAp': rap, 'xreg': 0, 'listNo': list_id, 'tcLanguage': 'ru'},
        timeout=60,
    )
    response.raise_for_status()
    return response.text


def fetch_folder_html(session: requests.Session, rap: str, parent_id: int) -> str:
    response = session.get(
        f'{BASE}/contentsGetList.php',
        params={'rAp': rap, 'xreg': 281, 'parentID': parent_id, 'tcLanguage': 'ru'},
        timeout=120,
    )
    response.raise_for_status()
    return response.text


def extract_list_page(js_text: str) -> str:
    match = re.search(r"listPage\s*=\s*'((?:\\'|[^'])*)'", js_text, re.DOTALL)
    if not match:
        match = re.search(r'listPage\s*=\s*"((?:\\"|[^"])*)"', js_text, re.DOTALL)
    if not match:
        return js_text
    payload = match.group(1)
    payload = payload.replace("\\'", "'").replace('\\"', '"')
    return html.unescape(payload)


def _normalize_name(text: str) -> str:
    text = re.sub(r'\s*\(\s*$', '', text)
    text = re.sub(r'\s*\(\d+\)\s*$', '', text).strip()
    text = text.replace('Cредства', 'Средства')  # site typo with Latin C
    return text


def parse_folder_lists(folder_html: str) -> dict[str, int]:
    entries: list[tuple[int, str]] = []
    for match in re.finditer(
        r"showList\((\d+)\)[^>]*>\s*<label[^>]*>([^<]+)",
        folder_html,
    ):
        list_id = int(match.group(1))
        name = _normalize_name(match.group(2))
        entries.append((list_id, name))

    found: dict[str, int] = {}
    for category in CATEGORY_NAMES:
        for list_id, name in entries:
            if category == name:
                found[category] = list_id
                break
    return found


def _clean_translation(raw: str) -> str:
    text = re.sub(r'\[[^\]]+\]\s*', '', raw).strip()
    return re.sub(r'\s+', ' ', text)


def parse_words_from_js(js_text: str) -> list[tuple[str, str, str]]:
    page_html = extract_list_page(js_text)
    soup = BeautifulSoup(page_html, 'html.parser')
    words: list[tuple[str, str, str]] = []
    seen: set[str] = set()

    for row in soup.find_all('tr', class_=re.compile(r'vl_line(odd|even)')):
        if row.get('colspan') or 'visible-xs' in row.get('class', []):
            continue
        chin_cell = row.find('td', class_='chin')
        if not chin_cell:
            continue
        hieroglyph = chin_cell.get_text(' ', strip=True)
        if not hieroglyph or hieroglyph in seen:
            continue

        pinyin_cell = row.find('td', class_='pinyin')
        pinyin = pinyin_cell.get_text(' ', strip=True) if pinyin_cell else ''

        translation = ''
        for td in row.find_all('td'):
            bold = td.find('b')
            if bold:
                translation = _clean_translation(bold.get_text(' ', strip=True))
                break
        if not translation:
            for td in row.find_all('td'):
                text = td.get_text(' ', strip=True)
                if text and text != hieroglyph and text != pinyin and not re.search(r'[\u4e00-\u9fff]', text):
                    if re.search(r'[а-яА-Яa-zA-Z]', text):
                        translation = _clean_translation(text)
                        break

        seen.add(hieroglyph)
        words.append((hieroglyph, pinyin, translation))

    return words


def main() -> int:
    session = make_session()
    rap = login(session)
    print('logged in, rAp=', rap)

    folder_html = fetch_folder_html(session, rap, PARENT_FOLDER_ID)
    categories = parse_folder_lists(folder_html)
    print('categories found:', len(categories), categories)

    if len(categories) < len(CATEGORY_NAMES):
        open('debug_folder.html', 'w', encoding='utf-8').write(folder_html)

    all_words: list[tuple[int, str, str, str, str]] = []
    number = 1
    for name in CATEGORY_NAMES:
        list_id = categories.get(name)
        if not list_id:
            print('skip missing category:', name)
            continue
        list_js = fetch_list_js(session, rap, list_id)
        items = parse_words_from_js(list_js)
        print(f'{name} ({list_id}): {len(items)} words')
        for hieroglyph, pinyin, translation in items:
            all_words.append((number, hieroglyph, pinyin, translation, ''))
            number += 1

    if not all_words:
        print('no words collected')
        return 1

    out_path = 'data/paket_slov_1.xlsx'
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = 'words'
    ws.append(['number', 'hieroglyph', 'pinyin', 'translation', 'phrase'])
    for row in all_words:
        ws.append(list(row))
    wb.save(out_path)
    print('saved', out_path, 'rows', len(all_words))

    sys.path.insert(0, '.')
    from models.database import _fetchone, ensure_database
    from services.excel_import import import_excel

    ensure_database()
    admin = _fetchone('SELECT user_id FROM users WHERE user_name = ?', ('admin',))
    if not admin:
        print('admin user not found')
        return 1

    from services.excel_import import delete_custom_list

    existing = _fetchone(
        'SELECT list_id FROM custom_word_lists WHERE user_id = ? AND name = ?',
        (admin['user_id'], 'Пакет слов 1'),
    )
    if existing:
        delete_custom_list(existing['list_id'])
        print('removed previous list', existing['list_id'])

    ok, msg, list_id = import_excel(admin['user_id'], out_path, 'Пакет слов 1')
    print('import', ok, msg, list_id)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
