from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


def get_project_root() -> Path:
    """Returns the root directory of the project."""
    return Path(__file__).resolve().parent.parent


def get_available_folders() -> List[str]:
    """Returns available data folders."""
    root = get_project_root()
    folders = []
    for name in ["data", "data_for_fr", "data_json"]:
        p = root / name
        if p.exists() and p.is_dir():
            folders.append(name)
    return folders


def list_data_files(folder_name: str = "data") -> List[Dict[str, Any]]:
    """Lists all JSON and CSV files in the given folder with metadata."""
    root = get_project_root()
    folder_path = root / folder_name
    if not folder_path.exists():
        return []

    files_info = []
    # Search for json and csv files
    all_files = sorted(list(folder_path.glob("*.json")) + list(folder_path.glob("*.csv")))
    for fp in all_files:
        try:
            words = load_words_from_file(fp)
            word_count = len(words)
        except Exception:
            word_count = 0

        files_info.append({
            "name": fp.name,
            "filename": fp.name,
            "folder": folder_name,
            "rel_path": str(fp.relative_to(root)),
            "full_path": str(fp),
            "extension": fp.suffix.lower(),
            "is_json": fp.suffix.lower() == ".json",
            "word_count": word_count,
            "size_bytes": fp.stat().st_size
        })
    return files_info


def normalize_word_entry(word: str, raw_val: Any, source_file: str = "") -> Dict[str, Any]:
    """Normalizes any internal representation into standard word dict."""
    translation = ""
    examples: List[Dict[str, str]] = []

    if isinstance(raw_val, dict):
        translation = raw_val.get("translation", "")
        raw_ex = raw_val.get("examples", [])
        for ex in raw_ex:
            if isinstance(ex, dict):
                sentence_en = ex.get("sentence_en", ex.get("en", ""))
                translation_am = ex.get("translation_am", ex.get("am", ex.get("ru", "")))
                examples.append({
                    "sentence_en": sentence_en,
                    "translation_am": translation_am
                })
            elif isinstance(ex, str):
                examples.append({"sentence_en": ex, "translation_am": ""})

    elif isinstance(raw_val, list):
        if len(raw_val) > 0 and isinstance(raw_val[0], str):
            translation = raw_val[0]
            raw_ex = raw_val[1:]
        else:
            raw_ex = raw_val

        for ex in raw_ex:
            if isinstance(ex, dict):
                examples.append({
                    "sentence_en": ex.get("sentence_en", ex.get("en", "")),
                    "translation_am": ex.get("translation_am", ex.get("am", ex.get("ru", "")))
                })
            elif isinstance(ex, str):
                examples.append({"sentence_en": ex, "translation_am": ""})

    elif isinstance(raw_val, str):
        translation = raw_val

    return {
        "word": word.strip(),
        "translation": translation.strip(),
        "examples": examples,
        "source_file": source_file
    }


def load_words_from_file(file_path: Union[Path, str]) -> List[Dict[str, Any]]:
    """Loads and normalizes words from a JSON or CSV file."""
    path = Path(file_path)
    if not path.is_absolute():
        path = get_project_root() / path

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    words: List[Dict[str, Any]] = []

    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "word" in item:
                    w = item["word"]
                    tr = item.get("translation", "")
                    raw_ex = item.get("examples", [])
                    ex_list = []
                    for ex in raw_ex:
                        if isinstance(ex, dict):
                            ex_list.append({
                                "sentence_en": ex.get("sentence_en", ex.get("en", "")),
                                "translation_am": ex.get("translation_am", ex.get("am", ex.get("ru", "")))
                            })
                        elif isinstance(ex, str):
                            ex_list.append({"sentence_en": ex, "translation_am": ""})

                    words.append({
                        "word": str(w).strip(),
                        "translation": str(tr).strip(),
                        "examples": ex_list,
                        "source_file": str(path.relative_to(get_project_root()))
                    })

        elif isinstance(data, dict):
            # Check if this is a nested dict of dicts (e.g. {"vocabulary": {"tap": ...}})
            for k, v in data.items():
                if isinstance(v, dict) and not ("translation" in v or "examples" in v):
                    # Nested dictionary
                    for sub_w, sub_v in v.items():
                        entry = normalize_word_entry(sub_w, sub_v, str(path.relative_to(get_project_root())))
                        words.append(entry)
                else:
                    entry = normalize_word_entry(k, v, str(path.relative_to(get_project_root())))
                    words.append(entry)

    elif path.suffix.lower() == ".csv":
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    w = row[0].strip()
                    tr = row[1].strip()
                    ex = [{"sentence_en": r.strip(), "translation_am": ""} for r in row[2:] if r.strip()]
                    words.append({
                        "word": w,
                        "translation": tr,
                        "examples": ex,
                        "source_file": str(path.relative_to(get_project_root()))
                    })

    return words


def _safe_write_json(file_path: Path, data: Any) -> None:
    """Safely writes JSON data to file with fallback for iSH / iOS filesystems."""
    temp_file = file_path.with_suffix(f"{file_path.suffix}.tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        try:
            os.replace(temp_file, file_path)
        except OSError:
            # Fallback for iSH / iOS mounted filesystems where atomic replace fails
            if file_path.exists():
                try:
                    file_path.unlink()
                except OSError:
                    pass
            try:
                temp_file.rename(file_path)
            except OSError:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except OSError:
                        pass
    except Exception:
        # Emergency direct write
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def delete_word_from_json(file_path: Union[Path, str], target_word: str) -> Dict[str, Any]:
    """
    Permanently deletes a word directly from the JSON file on disk.
    Supports both list format (like vocabulary.json) and dict format.
    """
    path = Path(file_path)
    if not path.is_absolute():
        path = get_project_root() / path

    if not path.exists():
        return {"success": False, "error": f"File not found: {path}"}

    if path.suffix.lower() != ".json":
        return {"success": False, "error": "Direct word deletion is supported for JSON files."}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    target_clean = target_word.strip().lower()
    deleted_count = 0
    remaining_count = 0

    if isinstance(data, list):
        new_list = []
        for item in data:
            if isinstance(item, dict) and item.get("word", "").strip().lower() == target_clean:
                deleted_count += 1
            else:
                new_list.append(item)

        if deleted_count > 0:
            _safe_write_json(path, new_list)
            remaining_count = len(new_list)
            return {
                "success": True,
                "word": target_word,
                "deleted_count": deleted_count,
                "remaining_count": remaining_count,
                "file": path.name
            }
        else:
            return {"success": False, "error": f"Word '{target_word}' not found in {path.name}"}

    elif isinstance(data, dict):
        found_keys = [k for k in data.keys() if k.strip().lower() == target_clean]
        if found_keys:
            for k in found_keys:
                del data[k]
                deleted_count += 1
        else:
            # Check nested dictionaries
            for category, subdict in data.items():
                if isinstance(subdict, dict):
                    nested_keys = [k for k in subdict.keys() if k.strip().lower() == target_clean]
                    for k in nested_keys:
                        del subdict[k]
                        deleted_count += 1

        if deleted_count > 0:
            _safe_write_json(path, data)
            remaining_words = load_words_from_file(path)
            return {
                "success": True,
                "word": target_word,
                "deleted_count": deleted_count,
                "remaining_count": len(remaining_words),
                "file": path.name
            }
        else:
            return {"success": False, "error": f"Word '{target_word}' not found in {path.name}"}

    return {"success": False, "error": f"Unsupported JSON structure in {path.name}"}


def add_word_to_json(
    file_path: Union[Path, str],
    word: str,
    translation: str,
    examples: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """Adds a new word directly to the JSON file."""
    path = Path(file_path)
    if not path.is_absolute():
        path = get_project_root() / path

    if not path.exists():
        return {"success": False, "error": f"File not found: {path}"}

    word = word.strip()
    translation = translation.strip()
    if not word:
        return {"success": False, "error": "Word cannot be empty"}

    examples = examples or []
    cleaned_examples = []
    for ex in examples:
        if isinstance(ex, dict):
            s_en = ex.get("sentence_en", "").strip()
            s_am = ex.get("translation_am", "").strip()
            if s_en or s_am:
                cleaned_examples.append({"sentence_en": s_en, "translation_am": s_am})
        elif isinstance(ex, str) and ex.strip():
            cleaned_examples.append({"sentence_en": ex.strip(), "translation_am": ""})

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        # Check if already exists
        for item in data:
            if isinstance(item, dict) and item.get("word", "").strip().lower() == word.lower():
                return {"success": False, "error": f"Word '{word}' already exists in {path.name}"}

        data.append({
            "word": word,
            "translation": translation,
            "examples": cleaned_examples
        })
        _safe_write_json(path, data)
        return {"success": True, "word": word, "file": path.name, "total_words": len(data)}

    elif isinstance(data, dict):
        if word in data:
            return {"success": False, "error": f"Word '{word}' already exists in {path.name}"}
        data[word] = {
            "translation": translation,
            "examples": cleaned_examples
        }
        _safe_write_json(path, data)
        return {"success": True, "word": word, "file": path.name, "total_words": len(data)}

    return {"success": False, "error": "Unsupported JSON format"}


def update_word_in_json(
    file_path: Union[Path, str],
    old_word: str,
    new_word: str,
    translation: str,
    examples: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """Updates an existing word, translation, and examples in JSON file."""
    path = Path(file_path)
    if not path.is_absolute():
        path = get_project_root() / path

    if not path.exists():
        return {"success": False, "error": f"File not found: {path}"}

    new_word = new_word.strip()
    translation = translation.strip()
    if not new_word:
        return {"success": False, "error": "Word cannot be empty"}

    examples = examples or []
    cleaned_examples = []
    for ex in examples:
        if isinstance(ex, dict):
            s_en = ex.get("sentence_en", "").strip()
            s_am = ex.get("translation_am", "").strip()
            if s_en or s_am:
                cleaned_examples.append({"sentence_en": s_en, "translation_am": s_am})
        elif isinstance(ex, str) and ex.strip():
            cleaned_examples.append({"sentence_en": ex.strip(), "translation_am": ""})

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = False

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("word", "").strip().lower() == old_word.strip().lower():
                item["word"] = new_word
                item["translation"] = translation
                item["examples"] = cleaned_examples
                updated = True
                break

        if updated:
            _safe_write_json(path, data)
            return {"success": True, "word": new_word, "file": path.name}
        return {"success": False, "error": f"Word '{old_word}' not found in {path.name}"}

    elif isinstance(data, dict):
        match_key = None
        for k in data.keys():
            if k.strip().lower() == old_word.strip().lower():
                match_key = k
                break

        if match_key:
            del data[match_key]
            data[new_word] = {
                "translation": translation,
                "examples": cleaned_examples
            }
            _safe_write_json(path, data)
            return {"success": True, "word": new_word, "file": path.name}
        return {"success": False, "error": f"Word '{old_word}' not found in {path.name}"}

    return {"success": False, "error": "Unsupported JSON format"}
