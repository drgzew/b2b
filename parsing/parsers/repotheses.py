import requests
from bs4 import BeautifulSoup
import json
import time
import re
import argparse
from urllib.parse import urljoin

BASE_URL = "https://elib.utmn.ru"
COLLECTION_URL = urljoin(BASE_URL, "/jspui/handle/ru-tsu/33")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def get_soup(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Ошибка загрузки {url}: {e}")
        return None

def parse_full_metadata_page(detail_url):
    """Парсит страницу с полными метаданными."""
    print(f"  Парсинг: {detail_url}")
    soup = get_soup(detail_url)
    if not soup:
        return None

    data = {
        "title": None,
        "title_en": None,
        "authors": [],
        "authors_en": [],
        "keywords": [],
        "year": None,
        "source_url": detail_url,
        "institute": None,
        "major": None,
        "abstract": None,
        "abstract_en": None
    }

    # --- СПОСОБ 1: Парсинг мета-тегов ---
    for meta in soup.find_all('meta'):
        name = meta.get('name', '').lower()
        content = meta.get('content', '').strip()
        lang = meta.get('xml:lang', '')
        
        if not content:
            continue
            
        if name == 'dc.title':
            data['title'] = content
        elif name in ['dcterms.alternative', 'dc.title.alternative']:
            data['title_en'] = content
        elif name == 'dc.creator':
            if lang == 'ru':
                data['authors'].append(content)
            elif lang == 'en':
                data['authors_en'].append(content)
        elif name == 'dc.subject':
            if ';' in content:
                for kw in content.split(';'):
                    kw = kw.strip()
                    if kw and kw not in data['keywords']:
                        data['keywords'].append(kw)
            else:
                data['keywords'].append(content)
        elif name in ['dcterms.issued', 'dc.date.issued']:
            try:
                data['year'] = int(content)
            except:
                pass
        elif name == 'dcterms.abstract':
            if lang == 'ru':
                data['abstract'] = content
            elif lang == 'en':
                data['abstract_en'] = content

    # --- СПОСОБ 2: Парсинг таблицы (основной способ для institute и major) ---
    # Ищем div с классом panel-body, в котором находится таблица
    panel = soup.find('div', class_='panel-body')
    if panel:
        # Ищем таблицу внутри panel-body
        table = panel.find('table', class_='itemDisplayTable')
        if not table:
            table = panel.find('table', class_='table')
        
        if table:
            for row in table.find_all('tr'):
                # Название поля в <th>
                label_cell = row.find('th', class_='metadataFieldLabel')
                if not label_cell:
                    continue
                    
                label = label_cell.get_text(strip=True)
                
                # Значение поля в <td>
                value_cell = row.find('td', class_='metadataFieldValue')
                if not value_cell:
                    continue
                
                # Получаем текст значения
                value = value_cell.get_text(strip=True)
                
                # Определяем поля по названию
                if label == 'dc.title' and not data['title']:
                    data['title'] = value
                elif label == 'dc.title.alternative' and not data['title_en']:
                    data['title_en'] = value
                elif label == 'dc.contributor.author':
                    # Ищем ссылки на авторов
                    authors = value_cell.find_all('a', class_='author')
                    if authors:
                        data['authors'] = [a.get_text(strip=True) for a in authors]
                    elif ';' in value:
                        data['authors'] = [a.strip() for a in value.split(';') if a.strip()]
                    else:
                        data['authors'] = [value]
                elif label == 'dc.subject':
                    # Ищем ссылки на ключевые слова
                    keywords = value_cell.find_all('a', class_='subject')
                    if keywords:
                        data['keywords'] = [k.get_text(strip=True) for k in keywords]
                    elif ';' in value:
                        data['keywords'] = [k.strip() for k in value.split(';') if k.strip()]
                    else:
                        data['keywords'] = [value]
                elif label == 'dc.date.issued' and not data['year']:
                    try:
                        data['year'] = int(value)
                    except:
                        pass
                elif label == 'dc.description.abstract' and not data['abstract']:
                    data['abstract'] = value
                elif label == 'local.contributor.department':
                    data['institute'] = value
                elif label == 'local.thesis.discipline':
                    data['major'] = value

    # Если институт не найден, пробуем извлечь из библиографической ссылки
    if not data['institute']:
        citation = soup.find('meta', {'name': 'DCTERMS.bibliographicCitation'})
        if citation and citation.get('content'):
            text = citation.get('content')
            # Ищем институт
            inst_patterns = [
                r'(?:Тюменский государственный университет,\s*)?([^,]+?(?:институт|школа|факультет|академия)[^,]*?)(?:,|\.|$)',
                r'([^,]+?институт[^,]*?)(?:,|\.|$)',
                r'([^,]+?школа[^,]*?)(?:,|\.|$)',
            ]
            for pattern in inst_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    inst = match.group(1).strip()
                    inst = re.sub(r'^,\s*', '', inst)
                    inst = re.sub(r'\s*,\s*$', '', inst)
                    if inst and len(inst) > 3:
                        data['institute'] = inst
                        break

    # Если специальность не найдена, пробуем извлечь из библиографической ссылки
    if not data['major']:
        citation = soup.find('meta', {'name': 'DCTERMS.bibliographicCitation'})
        if citation and citation.get('content'):
            text = citation.get('content')
            # Ищем специальность
            major_match = re.search(r'направление\s+([0-9]{2}\.[0-9]{2}\.[0-9]{2}\s+[^,]+?)(?:,|\.|$)', text, re.IGNORECASE)
            if major_match:
                data['major'] = major_match.group(1).strip()
            else:
                # Пробуем найти в таблице local.thesis.discipline, но уже пробовали выше
                pass

    # --- Очистка данных ---
    if data['authors']:
        data['authors'] = list(dict.fromkeys(data['authors']))
    if data['authors_en']:
        data['authors_en'] = list(dict.fromkeys(data['authors_en']))
    if data['keywords']:
        data['keywords'] = list(dict.fromkeys(data['keywords']))

    if not data['abstract_en'] and data['abstract']:
        if re.search(r'[A-Za-z]{20,}', data['abstract']):
            data['abstract_en'] = data['abstract']
            data['abstract'] = None

    return data

def parse_collection_page(soup):
    """Парсит страницу коллекции и возвращает список ссылок на детальные страницы."""
    detail_links = []
    
    table = soup.find('table', class_='table')
    if not table:
        print("Таблица с результатами не найдена")
        return detail_links
    
    rows = table.find_all('tr')
    for row in rows[1:]:
        cells = row.find_all('td')
        if len(cells) < 3:
            continue
            
        title_cell = cells[1]
        link = title_cell.find('a')
        if link and link.get('href'):
            href = link['href']
            if href.startswith('/'):
                full_link = urljoin(BASE_URL, href)
            else:
                full_link = urljoin(BASE_URL, href)
            
            if '?' in full_link:
                full_link += '&mode=full'
            else:
                full_link += '?mode=full'
            
            if full_link not in detail_links:
                detail_links.append(full_link)
    
    return detail_links

def get_next_page_url(soup):
    """Ищет ссылку на следующую страницу."""
    pagination = soup.find('div', class_='prev-next-links')
    if pagination:
        next_link = pagination.find('a', string=re.compile(r'дальше|>'))
        if next_link and next_link.get('href'):
            href = next_link['href']
            if href.startswith('/'):
                return urljoin(BASE_URL, href)
            return href
    
    for link in soup.find_all('a', href=True):
        text = link.get_text(strip=True)
        if text in ['дальше', '>', 'Next']:
            return urljoin(BASE_URL, link['href'])
    
    return None

def parse_theses(limit=None):
    """Основная функция парсинга магистерских диссертаций."""
    all_theses = []
    current_url = COLLECTION_URL
    
    page_count = 0
    
    while current_url and (limit is None or len(all_theses) < limit):
        page_count += 1
        print(f"\n{'='*60}")
        print(f"Обработка страницы {page_count}: {current_url}")
        print(f"Собрано работ: {len(all_theses)} из {limit if limit else '∞'}")
        print(f"{'='*60}")
        
        soup = get_soup(current_url)
        if not soup:
            print("Не удалось загрузить страницу. Завершаем.")
            break
        
        detail_links = parse_collection_page(soup)
        
        if not detail_links:
            print("Не найдено ссылок на детальные страницы.")
            with open(f"debug_repo_page_{page_count}.html", "w", encoding="utf-8") as f:
                f.write(str(soup))
            print(f"Сохранен HTML страницы в debug_repo_page_{page_count}.html")
            break
        
        print(f"Найдено {len(detail_links)} работ на странице.")
        
        for i, link in enumerate(detail_links, 1):
            if limit and len(all_theses) >= limit:
                break
            
            print(f"  [{i}/{len(detail_links)}] Обработка работы...")
            thesis_data = parse_full_metadata_page(link)
            
            if thesis_data and thesis_data.get("title"):
                if not thesis_data["year"]:
                    thesis_data["year"] = 0
                
                all_theses.append(thesis_data)
                print(f"    ✓ Добавлена работа:")
                print(f"      Название: {thesis_data['title'][:80]}...")
                print(f"      Год: {thesis_data['year']}")
                print(f"      Авторы (рус): {', '.join(thesis_data['authors'][:2]) if thesis_data['authors'] else 'Нет'}")
                print(f"      Авторы (англ): {', '.join(thesis_data['authors_en'][:2]) if thesis_data['authors_en'] else 'Нет'}")
                print(f"      Институт: {thesis_data['institute'] or 'Не указан'}")
                print(f"      Специальность: {thesis_data['major'] or 'Не указана'}")
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
        time.sleep(2)
    
    return all_theses

def main():
    """Главная функция с обработкой аргументов командной строки."""
    parser = argparse.ArgumentParser(description='Парсер магистерских диссертаций из репозитория ТюмГУ')
    parser.add_argument(
        '-n', '--number',
        type=int,
        default=None,
        help='Количество работ для парсинга (по умолчанию: все)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='data/raw/repotheses.json',
        help='Имя выходного файла (по умолчанию: data/raw/repotheses.json)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Задержка между запросами в секундах (по умолчанию: 1.0)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("ПАРСЕР МАГИСТЕРСКИХ ДИССЕРТАЦИЙ (РЕПОЗИТОРИЙ ТюмГУ)")
    print("="*60)
    print(f"Лимит работ: {args.number if args.number else 'Без лимита (все)'}")
    print(f"Выходной файл: {args.output}")
    print(f"Задержка: {args.delay} сек")
    print("="*60)
    
    start_time = time.time()
    theses = parse_theses(limit=args.number)
    elapsed_time = time.time() - start_time
    
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
