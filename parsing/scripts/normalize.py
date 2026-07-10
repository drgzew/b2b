from datetime import datetime
import json
from pathlib import Path
import re
from typing import List, Dict, Optional
import uuid

def normalize_keywords(keywords: List[str], max_keywords: int = 10) -> List[str]:
    """ Normalize keywords: remove duplicates, limit to max_keywords.
    """
    if not keywords:
        return []
    unique_keywords = list(dict.fromkeys(keywords))
    return unique_keywords[:max_keywords]

def map_artifact_type(work: Dict) -> str:
    """ Mapping of work type onto backend's artefact.
    """
    # article by default
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

def normalize_work(work: Dict, index: int) -> Dict:
    """ Turn one OpenAlex record into Artifact format.
    """
    keywords = work.get('keywords', [])
    normalized_keywords = normalize_keywords(keywords)
    artifact_type = map_artifact_type(work)
    access_level = determine_access_level(work)
    artifact = {
        "id": None,  # ID is up to database
        "title": work.get('title', f"Untitled Article {index}"),
        "type": artifact_type,
        "annotation": work.get('abstract', '') or "",
        # "file_path": None,  # path to PDF file
        "curator_status": "draft",  # draft by default
        "access_level": access_level,
        "author_name": ", ".join(work.get('utmn_authors', [])) if work.get('utmn_authors') else None,
        "created_at": datetime.utcnow().isoformat(),
        "embedding": None,  # fill it later
        "tags": [{"name": tag} for tag in normalized_keywords],  # tags based off keywords
        "doi": work.get('doi'),
        "source_url": work.get('source_url'),
        "year": work.get('year'),
        "openalex_id": work.get('openalex_id')
    }
    return artifact

def load_openalex_data(file_path: str) -> List[Dict]:
    """ Load OpenAlex data.
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
        print(f"Неизвестный формат данных в {file_path}")
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
    works = load_openalex_data("data/raw/openalex.json")
    print(f"Загружено статей: {len(works)}")

    artifacts = []
    for n, work in enumerate(works):
        try:
            artifact = normalize_work(work, n + 1)
            artifacts.append(artifact)
        except Exception as e:
            print(f"Ошибка при нормализации статьи {n + 1}: {e}")
            continue

    save_normalized_data(artifacts, "data/normalized.json")
    print(f"Нормализовано артефактов: {len(artifacts)}")

if __name__ == '__main__':
    main()
