from collections import Counter, defaultdict
import json
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
import numpy as np
from pathlib import Path
from pyopenalex import OpenAlex
import PyPDF2
import re
import requests

nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')
nltk.download('wordnet')

client = OpenAlex()

institutions = client.institutions.search("University of Tyumen").get()

inst = institutions.results[0]
print(f"ID: {inst.id}")
print(f"Название: {inst.display_name}")
print(f"Страна: {inst.country_code}")
print(f"Рейтинг: {inst.works_count} работ, {inst.cited_by_count} цитирований")
print(f"Сайт: {inst.homepage_url}")
print(f"ROR ID: {inst.ror}")

def unpack_abstract(abstract_inverted_index):
    """ Преобразует inverted index из OpenAlex в обычный текст.
    """
    if not abstract_inverted_index:
        return None

    # Находим максимальную позицию
    max_position = 0
    for positions in abstract_inverted_index.values():
        for pos in positions:
            if pos > max_position:
                max_position = pos

    # Создаем массив для текста
    text_array = [""] * (max_position + 1)

    # Заполняем массив словами
    for word, positions in abstract_inverted_index.items():
        for pos in positions:
            text_array[pos] = word

    # Собираем текст
    text = " ".join(text_array)

    # Исправляем пунктуацию
    text = re.sub(r' ([.,;:!?])', r'\1', text)
    text = re.sub(r' ([\)\]}])', r'\1', text)
    text = re.sub(r'([\(\[\{]) ', r'\1', text)
    text = re.sub(r'\s+', ' ', text)  # Убираем лишние пробелы

    return text.strip()

def get_works(limit=5, years="2023|2024|2025"):
    """ Get list of works.
    """
    return client.works                                       \
        .filter(**{"authorships.institutions.ror": inst.ror}) \
        .filter(publication_year=years)                       \
        .limit(limit)                                         \
        .get(all=True).results

def describe_work(work, index=None):
    """ Describe a piece of work.
    """
    print(f"Статья {index if index is not None else ''}")
    print(f" - Название: {work.title}")
    print(f" - Год: {work.publication_year}")
    print(f" - Цитирований: {work.cited_by_count}")
    print(f" - ID: {work.id}")
    print(f" - DOI: {work.doi}")
    if work.open_access and work.open_access.is_oa:
            print(f" - Открытый доступ: {work.open_access.oa_url}")

    institutions_list = []
    authors = []
    utmn_authors = []
    for authorship in work.authorships:
        authors.append(authorship.author.display_name)
        for inst_in_work in authorship.institutions:
            institutions_list.append(inst_in_work.display_name)
            if inst_in_work.display_name == "University of Tyumen":
                utmn_authors.append(authorship.author.display_name)
    unique_institutions = list(set(institutions_list))

    print(f" - Институты: {len(unique_institutions)} всего")
    print(f" - Авторы: {len(authors)} всего")
    print(f" - Авторы из ТюмГУ: {', '.join(utmn_authors)}")

    domains = []
    fields = []
    subfields = []
    topics = []
    for topic in work.topics:
        domains.append(topic.domain.get('display_name'))
        fields.append(topic.field.get('display_name'))
        subfields.append(topic.subfield.get('display_name'))
        topics.append(topic.display_name)

    print(f" - Домен: {', '.join(list(set(domains)))}")
    print(f" - Поле: {', '.join(list(set(fields)))}")
    print(f" - Подполе: {', '.join(list(set(subfields)))}")
    print(f" - Тема: {', '.join(list(set(topics)))}")

    print(f" - Аннотация: \"{unpack_abstract(work.abstract_inverted_index)}\"")

    print()

def dump_works(works, keywords, output_path):
    """ Dump info about works as JSON.
    """
    data = [
        {
            "title": work.title,
            "authors": [authorship.author.display_name for authorship in work.authorships],
            "utmn_authors": [
                authorship.author.display_name
                for authorship in work.authorships
                if any(map(lambda i: i.display_name == "University of Tyumen", authorship.institutions))
            ],
            "year": work.publication_year,
            "abstract": unpack_abstract(work.abstract_inverted_index),
            "doi": work.doi,
            "source_url": work.open_access.oa_url,
            "keywords": keywords[n] if n in keywords else None
        }
        for n, work in enumerate(works)
    ]
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

def download_pdf(work, index, total, output_folder, timeout=30):
    """ Download work as PDF if available.
    """
    if not work.open_access or not work.open_access.is_oa:
        return None

    # define best link to url 
    pdf_url = None

    if hasattr(work, 'best_oa_location') and work.best_oa_location:
        if hasattr(work.best_oa_location, 'pdf_url') and work.best_oa_location.pdf_url:
            pdf_url = work.best_oa_location.pdf_url
        elif hasattr(work.best_oa_location, 'landing_page_url') and work.best_oa_location.landing_page_url:
            pdf_url = work.best_oa_location.landing_page_url
        elif hasattr(work.best_oa_location, 'url') and work.best_oa_location.url:
            pdf_url = work.best_oa_location.url

    if not pdf_url and work.open_access.oa_url:
        pdf_url = work.open_access.oa_url

    if not pdf_url and hasattr(work, 'locations'):
        for location in work.locations:
            if location.is_oa:
                if hasattr(location, 'pdf_url') and location.pdf_url:
                    pdf_url = location.pdf_url
                    break
                elif hasattr(location, 'landing_page_url') and location.landing_page_url:
                    if location.landing_page_url.endswith('.pdf') or 'pdf' in location.landing_page_url.lower():
                        pdf_url = location.landing_page_url
                        break

    if not pdf_url and hasattr(work, 'primary_location') and work.primary_location:
        if hasattr(work.primary_location, 'pdf_url') and work.primary_location.pdf_url:
            pdf_url = work.primary_location.pdf_url
        elif hasattr(work.primary_location, 'landing_page_url') and work.primary_location.landing_page_url:
            pdf_url = work.primary_location.landing_page_url
    
    if not pdf_url:
        return None

    if work.doi:
        doi_clean = work.doi.replace('https://doi.org/', '').replace('/', '_')
        filename = f"{doi_clean}.pdf"
    else:
        work_id = work.id.split('/')[-1]
        filename = f"{work_id}.pdf"

    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

    output_path = Path(output_folder) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[{index}/{total}] Скачивание: {pdf_url}")

    if output_path.exists():
        print(f"(+) PDF уже существует: {filename}")
        return str(output_path)

    # download
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(pdf_url, headers=headers, timeout=timeout, stream=True, allow_redirects=True)

        if response.status_code == 200:
            # check that this is actually PDF
            content_type = response.headers.get('content-type', '').lower()

            if 'pdf' not in content_type and not pdf_url.endswith('.pdf'):
                print(f"(-) Не PDF, а HTML: {filename}")
                return None

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # check for minimum PDF size
            if output_path.stat().st_size < 1024:  # less than 1KB
                print(f"(-) Файл слишком маленький: {filename}")
                output_path.unlink()  # delete
                return None

            print(f"(+) PDF скачан: {filename} ({output_path.stat().st_size / 1024:.1f} KB)")
            return str(output_path)
        else:
            print(f"(-) Ошибка {response.status_code}: {filename}")
            return None

    except requests.exceptions.Timeout:
        print(f"(-) Таймаут: {filename}")
        return None
    except Exception as e:
        print(f"(-) Ошибка загрузки: {filename} - {e}")
        return None

def file_extract_text(path):
    """ Extract text fron a PDF file.
    """
    try:
        text = ""
        with open(path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Ошибка при чтении PDF {path}: {e}")
        return ""

def text_preprocess(text):
    """ Preprocess text: tokenize, lemmatize, remove stopwords.
    """
    if not text:
        return []

    sentences = sent_tokenize(text)
    words = []

    stop_words = set(stopwords.words('english') + stopwords.words('russian'))

    # stopwords specific for articles
    stop_words.update([
        'et', 'al', 'fig', 'table', 'figure', 'equation', 'however',
        'therefore', 'thus', 'also', 'using', 'used', 'shown', 'show',
        'shows', 'fig', 'ref', 'reference', 'one', 'two', 'three',
        'may', 'can', 'will', 'would', 'could', 'should', 'might',
        'abstract', 'introduction', 'method', 'result', 'conclusion',
        'study', 'paper', 'research', 'analysis', 'data', 'results',
        'found', 'shown', 'observed', 'increased', 'decreased',
        'wa', 'doi', 'http', 'property', 'sci'
    ])

    lemmatizer = WordNetLemmatizer()

    for sent in sentences:
        tokens = word_tokenize(sent.lower())
        tokens = [token for token in tokens if token.isalpha() and len(token) > 2]
        tokens = [lemmatizer.lemmatize(token) for token in tokens]
        tokens = [token for token in tokens if token not in stop_words]
        words.extend(tokens)

    return words

def text_keywords_tfidf(words, top_n=20):
    """ Extract keywords from text using TF-IDF.
    """
    if not words:
        return []

    # count word frequency
    word_freq = Counter(words)

    # remove too frequent or rare words
    total_words = len(words)
    filtered_words = {
        word: count for word, count in word_freq.items()
        if 0.001 < count / total_words < 0.5  # between 0.1% and 50%
    }

    sorted_words = sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)

    return [word for word, _ in sorted_words[:top_n]]

def text_keywords_rake(words, top_n=20):
    """ Extract keywords from text using RAKE.
    """
    if not words:
        return []

    # bigrams and trigrams
    bigrams = [' '.join(words[i:i+2]) for i in range(len(words)-1)]
    trigrams = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
    
    # frequency of all phrases
    all_phrases = words + bigrams + trigrams
    phrase_freq = Counter(all_phrases)

    # filter out too long phrases
    filtered_phrases = {
        phrase: count for phrase, count in phrase_freq.items()
        if count > 1 and len(phrase.split()) <= 3
    }

    sorted_phrases = sorted(filtered_phrases.items(), key=lambda x: x[1], reverse=True)

    return [phrase for phrase, _ in sorted_phrases[:top_n]]

def text_keywords_textrank(words, top_n=20, window_size=2, iterations=30, damping=.85):
    """ Extract keywords from text using TextRank (PageRank для текста).
    """
    if not words:
        return []

    if len(words) < 3:
        return words[:top_n] if words else []

    # Убираем дубликаты для построения графа (сохраняем порядок)
    unique_words = []
    seen = set()
    for word in words:
        if word not in seen:
            unique_words.append(word)
            seen.add(word)

    if len(unique_words) < 3:
        return unique_words[:top_n]

    # Строим граф связей между словами
    word_to_index = {word: i for i, word in enumerate(unique_words)}
    graph = np.zeros((len(unique_words), len(unique_words)))

    # Проходим по тексту и строим связи между словами в окне
    for i in range(len(words)):
        for j in range(i + 1, min(i + window_size + 1, len(words))):
            if words[i] in word_to_index and words[j] in word_to_index:
                idx_i = word_to_index[words[i]]
                idx_j = word_to_index[words[j]]
                graph[idx_i][idx_j] += 1
                graph[idx_j][idx_i] += 1

    # Нормализуем граф
    for i in range(len(graph)):
        row_sum = graph[i].sum()
        if row_sum > 0:
            graph[i] = graph[i] / row_sum

    # Алгоритм PageRank
    scores = np.ones(len(unique_words)) / len(unique_words)

    for _ in range(iterations):
        new_scores = (1 - damping) / len(unique_words) + damping * scores @ graph
        # Проверяем сходимость
        if np.linalg.norm(new_scores - scores) < 1e-6:
            break
        scores = new_scores

    # Сортируем слова по важности
    word_scores = [(unique_words[i], scores[i]) for i in range(len(unique_words))]
    word_scores.sort(key=lambda x: x[1], reverse=True)

    # Возвращаем топ-N слов
    result = [word for word, _ in word_scores[:top_n]]

    return result

def text_keywords_combined(text, top_n=20):
    prep = text_preprocess(text)

    kw_tfidf = text_keywords_tfidf(prep, top_n*2)
    kw_rake = text_keywords_rake(prep, top_n*2)
    kw_textrank = text_keywords_textrank(prep, top_n*2)

    word_weights = defaultdict(float)

    for idx, word in enumerate(kw_tfidf):
        weight = 1.0 - (idx / len(kw_tfidf)) if kw_tfidf else 0
        word_weights[word] += weight

    for idx, word in enumerate(kw_rake):
        weight = 1.0 - (idx / len(kw_rake)) if kw_rake else 0
        word_weights[word] += weight

    for idx, word in enumerate(kw_textrank):
        weight = 1.0 - (idx / len(kw_textrank)) if kw_textrank else 0
        word_weights[word] += weight

    sorted_words = sorted(word_weights.items(), key=lambda x: x[1], reverse=True)

    return [word for word, _ in sorted_words[:top_n]]

def build_taxonomy_flat(works):
    """ Build flat taxonomy of topics.
    """
    domains = []
    fields = []
    subfields = []
    topics = []
    for work in works:
        for topic in work.topics:
            domains.append(topic.domain.get('display_name'))
            fields.append(topic.field.get('display_name'))
            subfields.append(topic.subfield.get('display_name'))
            topics.append(topic.display_name)
    return list(set(domains)), list(set(fields)), list(set(subfields)), list(set(topics))

def build_taxonomy_hierarchy(works):
    """ Build hierarchical taxonomy of topics.
    """
    hierarchy = {}

    for work in works:
        if not hasattr(work, 'topics') or not work.topics:
            continue

        for topic in work.topics:
            domain_name = topic.domain.get('display_name')
            field_name = topic.field.get('display_name')
            subfield_name = topic.subfield.get('display_name')
            topic_name = topic.display_name

            if domain_name not in hierarchy:
                hierarchy[domain_name] = {
                    'name': domain_name,
                    'level': 1,
                    'fields': {}
                }

            if field_name not in hierarchy[domain_name]['fields']:
                hierarchy[domain_name]['fields'][field_name] = {
                    'name': field_name,
                    'level': 2,
                    'subfields': {}
                }

            if subfield_name not in hierarchy[domain_name]['fields'][field_name]['subfields']:
                hierarchy[domain_name]['fields'][field_name]['subfields'][subfield_name] = {
                    'name': subfield_name,
                    'level': 3,
                    'topics': []
                }

            if topic_name not in hierarchy[domain_name]['fields'][field_name]['subfields'][subfield_name]['topics']:
                hierarchy[domain_name]['fields'][field_name]['subfields'][subfield_name]['topics'].append(topic_name)

    return hierarchy

def print_taxonomy_hierarchy(hierarchy):
    """ Print hierarchical taxonomy of topics.
    """
    for domain_idx, (domain_name, domain_data) in enumerate(hierarchy.items(), 1):
        print(f" ├ Домен {domain_idx} - '{domain_name}'")
        print(f" │ Содержит полей: {len(domain_data['fields'])}")
        print(f" │ ")

        for field_idx, (field_name, field_data) in enumerate(domain_data['fields'].items(), 1):
            print(f" ├──┬ Поле {field_idx} - '{field_name}'")
            print(f" │  │ Содержит подполей: {len(field_data['subfields'])}")
            print(f" │  │ ")

            for subfield_idx, (subfield_name, subfield_data) in enumerate(field_data['subfields'].items(), 1):
                print(f" │  ├──┬ Подполе {subfield_idx} - '{subfield_name}'")
                print(f" │  │  │ Содержит тем: {len(subfield_data['topics'])}")
                print(f" │  │  │ ")

                for topic_idx, topic_name in enumerate(subfield_data['topics'], 1):
                    print(f" │  │  ├─── Тема {topic_idx}: {topic_name}")
                    print(f" │  │  │ ")

        print("═" * 60)

def save_taxonomy_hierarchy(hierarchy, output_path):
    """ Save hierarchical taxonomy of topics as Markdown document.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Таксономия статей ТюмГУ")
    lines.append("")

    lines.append("## Содержание")
    lines.append("")
    for domain_idx, (domain_name, _) in enumerate(hierarchy.items(), 1):
        lines.append(f"{domain_idx}. [{domain_name}](#{domain_name.lower().replace(' ', '-')})")
    lines.append("")
    lines.append("---")
    lines.append("")

    for domain_idx, (domain_name, domain_data) in enumerate(hierarchy.items(), 1):
        lines.append(f"## {domain_idx}. {domain_name}")
        lines.append("")

        for field_idx, (field_name, field_data) in enumerate(domain_data['fields'].items(), 1):
            lines.append(f"{domain_idx}.{field_idx}. {field_name}")
            lines.append("")

            subfields_list = list(field_data['subfields'].keys())
            for subfield_idx, subfield_name in enumerate(subfields_list, 1):
                topics_count = len(field_data['subfields'][subfield_name]['topics'])
                lines.append(f"- {domain_idx}.{field_idx}.{subfield_idx}. {subfield_name}")
            lines.append("")

        lines.append("")

    lines.append("## Статистика")
    lines.append("")

    total_domains = len(hierarchy)
    total_fields = sum(len(domain['fields']) for domain in hierarchy.values())
    total_subfields = sum(
        sum(len(field['subfields']) for field in domain['fields'].values())
        for domain in hierarchy.values()
    )

    lines.append(f"- **Домены:** {total_domains}")
    lines.append(f"- **Области:** {total_fields}")
    lines.append(f"- **Подтемы:** {total_subfields}")
    lines.append("")
    lines.append("")
    lines.append("| Домен | Области | Подтемы |")
    lines.append("|-------|---------|---------|")

    for domain_name, domain_data in hierarchy.items():
        domain_fields = len(domain_data['fields'])
        domain_subfields = sum(len(field['subfields']) for field in domain_data['fields'].values())
        lines.append(f"| {domain_name} | {domain_fields} | {domain_subfields} |")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

def assign_taxonomy_tags(work, taxonomy):
    """ Assign tags based on taxonomy.
    """
    if not taxonomy:
        return []
    _, _, subfielfds, _ = build_taxonomy_flat([work])
    return subfielfds

def main():
    N = 200

    works = get_works(N)

    for n, work in enumerate(works):
        describe_work(work, n + 1)
    print()

    domains, fields, subfields, topics = build_taxonomy_flat(works)
    print(f"Домены ({len(domains)}): {', '.join(domains)}")
    print(f"Поля ({len(fields)}): {', '.join(fields)}")
    print(f"Подполя ({len(subfields)}): {', '.join(subfields)}")
    print(f"Темы ({len(topics)}): {', '.join(topics)}")
    print()

    hierarchy = build_taxonomy_hierarchy(works)
    print_taxonomy_hierarchy(hierarchy)
    save_taxonomy_hierarchy(hierarchy, "docs/taxonomy.md")
    with open("docs/taxonomy.json", 'w', encoding='utf-8') as file:
        json.dump(hierarchy, file, ensure_ascii=False, indent=2)

    downloaded_paths = {}
    for n, work in enumerate(works):
        if path := download_pdf(work, n + 1, N, "data/pdfs"):
            downloaded_paths[n] = path
    print(f"Скачано статей: {len(downloaded_paths)}")

    keywords = {}
    for n in range(len(works)):
        kws = assign_taxonomy_tags(works[n], hierarchy)
        if n in downloaded_paths:
            text = file_extract_text(downloaded_paths[n])
            kws += text_keywords_combined(text)
        keywords[n] = list(set(kws)) if kws else None

    dump_works(works, keywords, "data/raw/openalex.json")

if __name__ == '__main__':
    main()
