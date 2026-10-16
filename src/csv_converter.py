import csv
import json
from pathlib import Path


def jsn_loader(file_paths: list, json_path: str) -> dict[str, dict]:
    loaded_dicts: dict[str, dict] = {}
    for path in file_paths:
        if isinstance(path, str):
            path = Path(path)
        if path.suffix == '.csv':
            dict_like: dict[str, list[str]] = {}
            with open(path, "r", encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    if len(row) >= 2:
                        key = row[0].strip()
                        values = [v.strip() for v in row[1:] if v.strip()]
                        if key in dict_like:
                            dict_like[key].extend(values)
                        elif values:
                            dict_like[key] = values
            loaded_dicts[path.stem] = dict_like
        elif path.suffix == '.json':
            with open(path, "r", encoding='utf-8') as js_file:
                data = json.load(js_file)
                if isinstance(data, list):
                    dict_like = {}
                    for item in data:
                        if isinstance(item, dict) and "word" in item:
                            word = item["word"]
                            translation = item.get("translation", "")
                            examples = item.get("examples", [])
                            dict_like[word] = [translation] + examples
                    loaded_dicts[path.stem] = dict_like
                elif isinstance(data, dict):
                    for k, v in data.items():
                        dict_name = f"{path.stem}_{k}" if k in loaded_dicts else k
                        loaded_dicts[dict_name] = v
    if json_path != "":
        with open(json_path, "w", encoding='utf-8') as js_file:
            json.dump(loaded_dicts, js_file, ensure_ascii=False, indent=5)
    print("All processes done properly")
    return loaded_dicts
