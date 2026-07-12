from datetime import datetime
import json
from pathlib import Path
from typing import List, Dict

def normalize_keywords(keywords: List[str], max_keywords: int = 10) -> List[str]:
    """ Normalize keywords: remove duplicates, limit to max_keywords.
    """
    if not keywords:
        return []
    unique_keywords = list(dict.fromkeys(keywords))
    return unique_keywords[:max_keywords]

def map_artifact_type(work: Dict, source: str = "openalex") -> str:
    """ Mapping of work type onto backend's artefact.
    """
    # Для ВКР из libtheses — всегда "vkr"
    if source == "libtheses":
        return "vkr"

    # Для OpenAlex — определяем по типу
    artifact_type = "article"
    if work.get('type'):
        type_lower = work['type'].lower()
        if 'dissertation' in type_lower or 'thesis' in type_lower:
            artifact_type = "vkr"
        elif 'book' in type_lower or 'chapter' in type_lower:
            artifact_type = "article"
        elif 'conference' in type_lower or 'proceedings' in type_lower:
            artifact_type = "talk"
        elif 'editorial' in type_lower or 'letter' in type_lower:
            artifact_type = "article"

    return artifact_type

def determine_access_level(work: Dict) -> str:
    """ Determine level of possible access to the artifact.
    """
    # check for open access
    if work.get('source_url') or work.get('doi'):
        if work.get('source_url') or work.get('doi'):
            return "full"
    if work.get('abstract'):
        return "annotation_only"
    return "none"

def normalize_openalex_work(work: Dict, index: int) -> Dict:
    """ Turn one OpenAlex record into Artifact format.
    """
    normalized_keywords = normalize_keywords(work.get('keywords', []))
    artifact_type = map_artifact_type(work, "openalex")
    access_level = determine_access_level(work)

    artifact = {
        "id": None,  # ID is up to database
        "title": work.get('title', f"Статья без названия {index}"),
        "type": artifact_type,
        "annotation": work.get('abstract', '') or "",
        # "file_path": None,  # path to PDF file
        "curator_status": "draft",  # draft by default
        "access_level": access_level,
        "author_name": ", ".join(work.get('authors', [])) if work.get('authors') else None,
        "created_at": datetime.utcnow().isoformat(),
        "embedding": None,  # fill it later
        "tags": [{"name": tag} for tag in normalized_keywords],  # tags based off keywords
        "doi": work.get('doi'),
        "source_url": work.get('source_url'),
        "year": work.get('year'),
        "openalex_id": work.get('openalex_id'),
        "institute": None,
        "major": None,
        "source": "openalex"
    }

    return artifact

def normalize_libtheses_work(work: Dict, index: int) -> Dict:
    """ Turn one UTMN library thesis record into Artifact format.
    """
    access_level = determine_access_level(work)
    authors = work.get('authors', [])
    author_name = ", ".join(authors) if authors else None

    artifact = {
        "id": None,  # ID is up to database
        "title": work.get('title', f"ВКР без названия {index}"),
        "type": "vkr",
        "annotation": work.get('abstract', '') or "",
        "curator_status": "draft",
        "access_level": access_level,
        "author_name": author_name,
        "created_at": datetime.utcnow().isoformat(),
        "embedding": None,  # fill it later
        "tags": [],  # there are no keywords defined by the library
        "doi": None,  # У ВКР нет DOI
        "source_url": work.get('source_url'),
        "year": work.get('year'),
        "openalex_id": None,  # У ВКР нет OpenAlex ID
        "institute": work.get('institute'),
        "major": work.get('major'),
        "source": "utmnlib"
    }

    return artifact

def load_openalex_data(file_path: str) -> List[Dict]:
    """ Load OpenAlex data from JSON file.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"Файл {file_path} не найден")
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'works' in data:
        return data['works']
    else:
        print(f"Неверный формат данных в {file_path}")
        return []

def load_libtheses_data(file_path: str) -> List[Dict]:
    """ Load  UTMN library thesis data from JSON file.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"Файл {file_path} не найден")
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    else:
        print(f"Неверный формат данных в {file_path}")
        return []

def save_normalized_data(artifacts: List[Dict], output_path: str):
    """ Save normalized data as JSON.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(artifacts, f, ensure_ascii=False, indent=2)
    print(f"Всего артефактов: {len(artifacts)}")

def main():
    artifacts = []

    print("Загрузка данных OpenAlex")
    openalex_works = load_openalex_data("data/raw/openalex.json")
    total_openalex = len(openalex_works)
    
    for n, work in enumerate(openalex_works):
        try:
            artifact = normalize_openalex_work(work, n + 1)
            artifacts.append(artifact)
        except Exception as e:
            print(f"Ошибка при нормализации статьи OpenAlex {n + 1}: {e}")

    print("Загрузка данных библиотеки ТюмГУ")
    libtheses_works = load_libtheses_data("data/raw/libtheses.json")
    total_libtheses = len(libtheses_works)
    for n, work in enumerate(libtheses_works):
        try:
            artifact = normalize_libtheses_work(work, n + 1)
            artifacts.append(artifact)
        except Exception as e:
            print(f"Ошибка при нормализации ВКР из библиотеки ТюмГУ {n + 1}: {e}")

    save_normalized_data(artifacts, "data/normalized.json")
    print(f"Нормализовано артефактов: {len(artifacts)}")
    print(f" - Из OpenAlex: {total_openalex}")
    print(f" - Из библиотеки ТюмГУ: {total_libtheses}")

if __name__ == '__main__':
    main()
