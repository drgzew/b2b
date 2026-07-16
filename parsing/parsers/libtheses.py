import requests
from bs4 import BeautifulSoup
import json
import time
import re
import argparse
from urllib.parse import urljoin

# Базовые URL
BASE_URL = "https://library.utmn.ru"
SEARCH_URL = urljoin(BASE_URL, "/search/result")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

def get_soup(url, params=None):
    """Получает HTML-страницу и возвращает объект BeautifulSoup."""
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке страницы {url}: {e}")
        return None

def extract_title_parts(full_title):
    """
    Извлекает русское и английское название из полного заголовка.
    Формат: "Авторы. Русское название = English title: описание ВКР"
    Или: "Авторы. Русское название: описание ВКР" (без английского)
    """
    title_ru = None
    title_en = None
    
    # Сначала убираем авторов из начала строки
    # Формат: "Фамилия, Имя Отчество. Название работы = English title: ..."
    if '. ' in full_title:
        parts = full_title.split('. ', 1)
        if len(parts) == 2:
            title_part = parts[1]
        else:
            title_part = full_title
    else:
        title_part = full_title
    
    # Проверяем наличие английского названия
    if ' = ' in title_part:
        # Есть английское название
        parts = title_part.split(' = ', 1)
        title_ru = parts[0].strip()
        title_en_part = parts[1].strip()
        
        # Очищаем английское название от суффиксов
        suffixes = [
            ': выпускная квалификационная работа',
            ': выпускная квалификационная работа бакалавра',
            ': магистерская диссертация',
            ': дипломная работа',
            ': выпускная квалификационная работа магистра',
            ', выпускная квалификационная работа',
            ', выпускная квалификационная работа бакалавра',
            ', магистерская диссертация',
            ', дипломная работа',
            ', выпускная квалификационная работа магистра'
        ]
        
        for suffix in suffixes:
            if suffix in title_en_part:
                title_en = title_en_part.split(suffix)[0].strip()
                break
        
        # Если не нашли суффикс, пытаемся найти по паттерну ": направление" или ", направление"
        if not title_en:
            match = re.search(r'([^:,]+?)\s*[,:]\s*направление', title_en_part, re.IGNORECASE)
            if match:
                title_en = match.group(1).strip()
            else:
                # Если ничего не нашли, берем всю строку до двоеточия или запятой
                match = re.search(r'^([^:,]+)', title_en_part)
                if match:
                    title_en = match.group(1).strip()
                else:
                    title_en = title_en_part
    else:
        # Нет английского названия - берем русское название
        # Нужно отделить название от описания ВКР
        title_ru = title_part.strip()
        
        # Очищаем русское название от суффиксов
        suffixes = [
            ': выпускная квалификационная работа',
            ': выпускная квалификационная работа бакалавра',
            ': магистерская диссертация',
            ': дипломная работа',
            ': выпускная квалификационная работа магистра',
            ': выпускная квалифицированная работа',
            ': выпускная квалифицированная работа (бакалаврская работа)',
        ]
        for suffix in suffixes:
            if suffix in title_ru:
                title_ru = title_ru.split(suffix)[0].strip()
                break
        
        title_en = ""
    
    # Очищаем русское название от суффиксов (если не очистилось выше)
    if title_ru:
        suffixes = [
            ': выпускная квалификационная работа',
            ': выпускная квалификационная работа бакалавра',
            ': магистерская диссертация',
            ': дипломная работа',
            ': выпускная квалификационная работа магистра',
            ': выпускная квалифицированная работа',
            ': выпускная квалифицированная работа (бакалаврская работа)',
        ]
        for suffix in suffixes:
            if suffix in title_ru:
                title_ru = title_ru.split(suffix)[0].strip()
                break
    
    return title_ru, title_en

def extract_abstract_parts(soup):
    """Извлекает русскую и английскую аннотацию."""
    abstract_ru = None
    abstract_en = None
    
    accordions = soup.find_all('div', class_='accordion')
    for accordion in accordions:
        header = accordion.find('h2')
        if header and 'Аннотация' in header.get_text():
            content_div = accordion.find('div')
            if content_div:
                abstract_paragraphs = content_div.find_all('p', class_='annotation')
                if abstract_paragraphs:
                    # Обычно первый абзац - русский, второй - английский
                    texts = [p.get_text(strip=True) for p in abstract_paragraphs if p.get_text(strip=True)]
                    if len(texts) >= 2:
                        abstract_ru = texts[0]
                        abstract_en = texts[1]
                    elif len(texts) == 1:
                        # Если только один абзац, пробуем определить язык
                        text = texts[0]
                        if re.search(r'[а-яА-Я]', text):
                            abstract_ru = text
                        else:
                            abstract_en = text
                else:
                    # Если нет классов annotation, берем весь текст
                    all_text = content_div.get_text(strip=True)
                    # Пытаемся разделить русский и английский
                    if '\n' in all_text:
                        parts = all_text.split('\n')
                        if len(parts) >= 2:
                            abstract_ru = parts[0].strip()
                            abstract_en = parts[1].strip()
                        else:
                            abstract_ru = all_text
            break
    
    return abstract_ru, abstract_en

def extract_themes(soup):
    """Извлекает тематику из блока 'Тематика' на странице."""
    themes = []
    
    # Ищем блок с тематикой
    # На странице тематика находится в блоке <p> с <span class="title">Тематика:</span>
    description_div = soup.find('div', id='description')
    if description_div:
        # Ищем все параграфы внутри description
        for p in description_div.find_all('p'):
            # Ищем span с текстом "Тематика:"
            title_span = p.find('span', class_='title')
            if title_span and 'Тематика:' in title_span.get_text():
                # Нашли блок с тематикой
                # Все ссылки внутри этого параграфа - это темы
                for keyword_span in p.find_all('span', class_='keyword'):
                    # Извлекаем текст из ссылки внутри keyword
                    link = keyword_span.find('a')
                    if link:
                        theme_text = link.get_text(strip=True)
                        if theme_text:
                            themes.append(theme_text)
                    else:
                        # Если ссылки нет, берем текст напрямую
                        theme_text = keyword_span.get_text(strip=True)
                        # Убираем точку с запятой в конце
                        if theme_text.endswith(';'):
                            theme_text = theme_text[:-1]
                        if theme_text:
                            themes.append(theme_text)
                break
    
    # Если не нашли через описанный выше способ, пробуем альтернативный
    if not themes:
        # Ищем все элементы с классом 'keyword' внутри 'description'
        description_div = soup.find('div', id='description')
        if description_div:
            # Находим блок с тематикой по тексту
            all_p = description_div.find_all('p')
            for p in all_p:
                if 'Тематика:' in p.get_text():
                    for keyword_span in p.find_all('span', class_='keyword'):
                        link = keyword_span.find('a')
                        if link:
                            theme_text = link.get_text(strip=True)
                            if theme_text:
                                themes.append(theme_text)
                        else:
                            theme_text = keyword_span.get_text(strip=True)
                            if theme_text.endswith(';'):
                                theme_text = theme_text[:-1]
                            if theme_text:
                                themes.append(theme_text)
                    break
    
    return themes

def extract_institute_and_major(title_text):
    """Извлекает институт и направление подготовки из заголовка."""
    institute = None
    major = None
    
    # Ищем институт/школу
    institute_patterns = [
        r'(?:Тюменский государственный университет,\s*)?([^,]+?(?:институт|школа|факультет|академия)[^,]*?)(?:,|\.|\s*—)',
        r'(?:филиал\)\s*)?([^,]+?(?:институт|школа)[^,]*?)(?:,|\.|\s*—)',
        r'([^,]+?институт[^,]*?)(?:,|\.|\s*—)',
        r'([^,]+?школа[^,]*?)(?:,|\.|\s*—)',
    ]
    
    for pattern in institute_patterns:
        match = re.search(pattern, title_text, re.IGNORECASE)
        if match:
            institute = match.group(1).strip()
            # Очищаем от лишних запятых и точек
            institute = re.sub(r'^,\s*', '', institute)
            institute = re.sub(r'\s*,\s*$', '', institute)
            break
    
    # Ищем направление подготовки (специальность)
    # Исправленный паттерн с сохранением кавычек
    major_patterns = [
        r'направление\s+([0-9]{2}\.[0-9]{2}\.[0-9]{2}\s+[«"]([^»"]+)[»"])',  # С кавычками
        r'направление\s+([0-9]{2}\.[0-9]{2}\.[0-9]{2}\s+[^,]+?)(?:,|\.|\s*—)',  # Без кавычек
        r'специальность\s+([0-9]{2}\.[0-9]{2}\.[0-9]{2}\s+[«"]([^»"]+)[»"])',
        r'профиль\s+["\']([^"\']+)["\']',
        r'программа\s+["\']([^"\']+)["\']',
    ]
    
    for pattern in major_patterns:
        match = re.search(pattern, title_text, re.IGNORECASE)
        if match:
            # Если захватили группу с кавычками
            if match.lastindex and match.lastindex >= 2:
                major = match.group(1).strip()
            else:
                major = match.group(1).strip()
            # Очищаем от лишних символов в конце
            major = re.sub(r'[,:.]$', '', major)
            major = re.sub(r'\s+', ' ', major)
            break
    
    # Если институт не найден, ищем по характерным словам
    if not institute:
        institutes = [
            'Институт социально-гуманитарных наук',
            'Институт государства и права',
            'Институт физической культуры',
            'Школа естественных наук',
            'Школа компьютерных наук',
            'Школа перспективных исследований',
            'Ишимский педагогический институт',
            'Тобольский пединститут'
        ]
        for inst in institutes:
            if inst in title_text:
                institute = inst
                break
    
    return institute, major

def parse_detail_page(detail_url):
    """Парсит страницу с детальной информацией о работе."""
    print(f"  Парсинг детальной страницы: {detail_url}")
    soup = get_soup(detail_url)
    if not soup:
        return None

    data = {
        "title": None,
        "title_en": None,
        "authors": [],
        "year": None,
        "abstract": None,
        "abstract_en": None,
        "source_url": detail_url,
        "institute": None,
        "major": None,
        "themes": []
    }

    # --- Извлечение названия ---
    title_tag = soup.find('h1', class_='v2')
    if title_tag:
        full_title = title_tag.get_text(strip=True)
        
        # Извлекаем русское и английское название
        title_ru, title_en = extract_title_parts(full_title)
        data["title"] = title_ru
        data["title_en"] = title_en
        
        # --- ПРАВИЛЬНОЕ ИЗВЛЕЧЕНИЕ АВТОРОВ ---
        # Формат: "Фамилия, Имя Отчество. Название работы = English title: ..."
        # Ищем авторов в начале строки до первой точки с пробелом
        if '. ' in full_title:
            # Берем часть до первой точки с пробелом
            author_part = full_title.split('. ', 1)[0]
            
            # Проверяем, содержит ли эта часть запятую (признак формата "Фамилия, Имя")
            if ',' in author_part:
                # Формат: "Фамилия, Имя Отчество" или "Фамилия, И. О."
                # Оставляем как есть - это полный формат автора
                data["authors"] = [author_part.strip()]
            else:
                # Возможно, несколько авторов через точку с запятой
                if ';' in author_part:
                    data["authors"] = [a.strip() for a in author_part.split(';') if a.strip()]
                else:
                    data["authors"] = [author_part.strip()]
        
        # Извлекаем институт и направление
        institute, major = extract_institute_and_major(full_title)
        data["institute"] = institute
        data["major"] = major

    # --- Извлечение года ---
    description_div = soup.find('div', id='description')
    if description_div:
        text = description_div.get_text()
        year_match = re.search(r'(19|20)\d{2}', text)
        if year_match:
            data["year"] = int(year_match.group(0))

    # Если год не найден, ищем в URL
    if not data["year"]:
        year_match = re.search(r'/(202[0-9]|201[0-9])/', detail_url)
        if year_match:
            data["year"] = int(year_match.group(1))

    # --- Извлечение аннотации ---
    abstract_ru, abstract_en = extract_abstract_parts(soup)
    data["abstract"] = abstract_ru
    data["abstract_en"] = abstract_en

    # --- Извлечение тематики ---
    themes = extract_themes(soup)
    data["themes"] = themes

    return data

def parse_search_page(soup):
    """Парсит страницу с результатами поиска и возвращает список ссылок на детальные страницы."""
    detail_links = []
    
    # Способ 1: Ищем ссылки в таблице результатов
    result_table = soup.find('table', class_='resultTable')
    if result_table:
        rows = result_table.find_all('tr')
        for row in rows:
            title_cell = row.find('td', class_='title')
            if title_cell:
                link = title_cell.find('a')
                if link and link.get('href'):
                    full_link = urljoin(BASE_URL, link['href'])
                    if full_link not in detail_links:
                        detail_links.append(full_link)
    
    # Способ 2: Ищем все ссылки, ведущие на /dl/.../info
    if not detail_links:
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/dl/' in href and href.endswith('/info'):
                full_link = urljoin(BASE_URL, href)
                if full_link not in detail_links:
                    detail_links.append(full_link)
    
    # Способ 3: Ищем ссылки на PDF и преобразуем в info
    if not detail_links:
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/dl/' in href and href.endswith('.pdf'):
                href = href.replace('.pdf', '.pdf/info')
                full_link = urljoin(BASE_URL, href)
                if full_link not in detail_links:
                    detail_links.append(full_link)

    return detail_links

def get_next_page_url(soup):
    """Ищет ссылку на следующую страницу."""
    pagination = soup.find('div', class_='pagination')
    if pagination:
        next_link = pagination.find('a', string=re.compile(r'Вперёд|>|Следующая'))
        if next_link and next_link.get('href'):
            return urljoin(BASE_URL, next_link['href'])
    
    for link in soup.find_all('a', href=True):
        text = link.get_text(strip=True)
        if text in ['Вперёд', '>', 'Следующая', 'Next']:
            return urljoin(BASE_URL, link['href'])
    
    return None

def parse_theses(limit=None):
    """Основная функция парсинга ВКР."""
    all_theses = []
    current_url = SEARCH_URL
    params = {"f": "documentType:DT03"}
    
    page_count = 0
    
    while current_url and (limit is None or len(all_theses) < limit):
        page_count += 1
        print(f"\n{'='*60}")
        print(f"Обработка страницы {page_count}: {current_url}")
        print(f"Собрано ВКР: {len(all_theses)} из {limit if limit else '∞'}")
        print(f"{'='*60}")
        
        soup = get_soup(current_url, params=params if page_count == 1 else None)
        if not soup:
            print("Не удалось загрузить страницу. Завершаем.")
            break
        
        detail_links = parse_search_page(soup)
        
        if not detail_links:
            print("Не найдено ссылок на детальные страницы. Проверьте структуру сайта.")
            with open(f"debug_page_{page_count}.html", "w", encoding="utf-8") as f:
                f.write(str(soup))
            print(f"Сохранен HTML страницы в debug_page_{page_count}.html для анализа")
            break
        
        print(f"Найдено {len(detail_links)} работ на странице.")
        
        for i, link in enumerate(detail_links, 1):
            if limit and len(all_theses) >= limit:
                break
            
            print(f"  [{i}/{len(detail_links)}] Обработка работы...")
            thesis_data = parse_detail_page(link)
            
            if thesis_data and thesis_data.get("title"):
                if not thesis_data["year"]:
                    thesis_data["year"] = 0
                
                all_theses.append(thesis_data)
                print(f"    ✓ Добавлена работа:")
                print(f"      Название: {thesis_data['title'][:80]}...")
                print(f"      Год: {thesis_data['year']}")
                print(f"      Автор: {thesis_data['authors'][0] if thesis_data['authors'] else 'Неизвестен'}")
                print(f"      Институт: {thesis_data['institute'] or 'Не указан'}")
                print(f"      Тем: {len(thesis_data.get('themes', []))}")
            else:
                print(f"    ✗ Не удалось спарсить работу по ссылке {link}")
            
            time.sleep(1)
        
        if limit and len(all_theses) >= limit:
            break
            
        next_url = get_next_page_url(soup)
        if not next_url or next_url == current_url:
            print("Достигнут конец списка результатов.")
            break
        
        current_url = next_url
        params = None
        time.sleep(2)
    
    return all_theses

def main():
    """Главная функция с обработкой аргументов командной строки."""
    parser = argparse.ArgumentParser(description='Парсер ВКР Тюменского государственного университета')
    parser.add_argument(
        '-n', '--number',
        type=int,
        default=None,
        help='Количество ВКР для парсинга (по умолчанию: все)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='data/raw/libtheses.json',
        help='Имя выходного файла (по умолчанию: data/raw/libtheses.json)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Задержка между запросами в секундах (по умолчанию: 1.0)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("ПАРСЕР ВКР ТЮМЕНСКОГО ГОСУДАРСТВЕННОГО УНИВЕРСИТЕТА")
    print("="*60)
    print(f"Лимит работ: {args.number if args.number else 'Без лимита (все)'}")
    print(f"Выходной файл: {args.output}")
    print(f"Задержка: {args.delay} сек")
    print("="*60)
    
    start_time = time.time()
    theses = parse_theses(limit=args.number)
    elapsed_time = time.time() - start_time
    
    # Сортируем по году (по убыванию)
    theses.sort(key=lambda x: x.get('year', 0), reverse=True)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(theses, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print(f"Собрано {len(theses)} записей.")
    print(f"Время выполнения: {elapsed_time:.2f} секунд")
    print(f"Результат сохранён в {args.output}")
    print("="*60)

if __name__ == "__main__":
    main()
