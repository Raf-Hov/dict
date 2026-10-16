from pathlib import Path
from .erros import Csv_not_found


def get_data_files(folder_name: str = "data") -> list:
    data_dir = Path(__file__).resolve().parent.parent / folder_name
    if not data_dir.exists():
        raise FileNotFoundError(f"Folder {folder_name} not found")
    files = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.json"))
    if not files:
        raise Csv_not_found("CSV or JSON files not found")
    return files


def data_josn_pathfinder(name: str) -> str:
    if name == "":
        return ""
    data_json_dir = Path(__file__).resolve().parent.parent / "data_json"
    data_json_dir.mkdir(parents=True, exist_ok=True)
    full_file_path = data_json_dir / name
    return str(full_file_path)
