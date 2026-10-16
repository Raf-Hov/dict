from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

# Ensure UTF-8 streams for Alpine / iSH environments
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from .argp import data_josn_pathfinder, get_data_files
from .csv_converter import jsn_loader
from .radomaizer import randomizer
from .storage import (
    add_word_to_json,
    delete_word_from_json,
    get_available_folders,
    get_project_root,
    list_data_files,
    load_words_from_file,
)
from .web_server import is_ish, start_server


def run_terminal_practice():
    """Terminal practice session with support for deleting words from JSON."""
    print("\n\033[1;34m─── Terminal Vocabulary Practice ───\033[0m")
    lang = input("Choose language (eng / fr) [default: eng]: ").strip().lower()
    folder = "data_for_fr" if lang == "fr" else "data"

    try:
        all_files = get_data_files(folder)
    except Exception as e:
        print(f"\033[31mError: {e}\033[0m")
        return

    print(f"\nAvailable files in {folder} folder:")
    default_idx = 1
    for i, file_path in enumerate(all_files, 1):
        is_json = file_path.suffix.lower() == ".json"
        tag = "\033[32m[JSON]\033[0m" if is_json else "[CSV]"
        print(f"  {i} : {tag} {file_path.name}")
        if file_path.name == "vocabulary.json":
            default_idx = i

    file_choice = input(f"\nSelect file number(s) (e.g. '{default_idx}') [default: {default_idx}]: ").strip().replace(",", " ")
    if not file_choice:
        file_choice = str(default_idx)

    selected_files = []
    for c in file_choice.split():
        try:
            idx = int(c)
            if 1 <= idx <= len(all_files):
                selected_files.append(all_files[idx - 1])
        except ValueError:
            pass

    if not selected_files:
        print("\033[31mError: Invalid files selected!\033[0m")
        return

    primary_file = selected_files[0]

    # If already a JSON file and only 1 file selected, we can directly load it
    if len(selected_files) == 1 and primary_file.suffix.lower() == ".json":
        words_list = load_words_from_file(primary_file)
        if not words_list:
            print("\033[31mFile is empty!\033[0m")
            return
        dict_name = primary_file.stem
        dict_data = {w["word"]: [w["translation"]] + w["examples"] for w in words_list}
        jsn = {dict_name: dict_data}
        chosen_name = dict_name
    else:
        filename = input("\nSave merged data to new JSON? (leave empty to skip): ").strip()
        if filename and not filename.endswith(".json"):
            filename += ".json"
        jsn = jsn_loader(selected_files, data_josn_pathfinder(filename))
        mix_all = {}
        for d in jsn.values():
            mix_all.update(d)
        jsn["mix_all"] = mix_all

        available_dicts = list(jsn.keys())
        print("\nAvailable dictionaries:")
        for i, name in enumerate(available_dicts, 1):
            print(f"  {i} : {name}")

        choice_input = input("\nSelect dictionary number to study [default: 1]: ").strip()
        if not choice_input:
            choice_input = "1"
        try:
            idx = int(choice_input)
            chosen_name = available_dicts[idx - 1]
        except (ValueError, IndexError):
            chosen_name = available_dicts[0]

    total_available = len(jsn[chosen_name])
    num_input = input(f"\nNumber of words to practice (1 - {total_available}) [default: {min(20, total_available)}]: ").strip()
    if not num_input:
        num = min(20, total_available)
    else:
        try:
            num = int(num_input)
        except ValueError:
            num = min(20, total_available)

    order_choice = input("Randomize words? (y/n) [default: y]: ").strip().lower()
    is_random = order_choice != "n"

    try:
        randomizer(jsn, num, chosen_name, is_random, source_file=primary_file)
    except Exception as e:
        print(f"\033[31mError during session: {e}\033[0m")


def run_word_manager():
    """Terminal interface to view, search, and delete words directly from JSON."""
    print("\n\033[1;35m─── JSON Word Manager & Deletion ───\033[0m")
    folder = "data"
    files = list_data_files(folder)
    json_files = [f for f in files if f["is_json"]]

    if not json_files:
        print(f"No JSON files found in {folder}/")
        return

    print("\nSelect JSON file to manage:")
    for i, jf in enumerate(json_files, 1):
        print(f"  {i} : {jf['filename']} ({jf['word_count']} words)")

    choice = input("\nFile number [default: 1]: ").strip()
    idx = int(choice) if choice.isdigit() and 1 <= int(choice) <= len(json_files) else 1
    selected_file = json_files[idx - 1]
    file_path = selected_file["full_path"]

    while True:
        words = load_words_from_file(file_path)
        print(f"\n\033[1mManaging: {selected_file['filename']} ({len(words)} words)\033[0m")
        print("  [1] List all words")
        print("  [2] Search for a word")
        print("  [3] 🗑️  Delete a word permanently from JSON")
        print("  [4] ➕ Add a new word to JSON")
        print("  [0] Back to main menu")

        action = input("\nAction [1-4, 0]: ").strip()
        if action == "0":
            break

        if action == "1":
            print("\nWords in dictionary:")
            for i, w in enumerate(words, 1):
                ex_note = f" ({len(w.get('examples', []))} ex.)" if w.get("examples") else ""
                print(f"  {i:3d}. \033[1;32m{w['word']:<20}\033[0m : {w.get('translation', '')}{ex_note}")
            input("\nPress Enter to continue...")

        elif action == "2":
            q = input("\nEnter search query: ").strip().lower()
            if not q:
                continue
            matches = [w for w in words if q in w["word"].lower() or q in (w.get("translation") or "").lower()]
            print(f"\nFound {len(matches)} match(es):")
            for i, m in enumerate(matches, 1):
                print(f"  {i}. \033[1;32m{m['word']}\033[0m -> {m.get('translation', '')}")
            input("\nPress Enter to continue...")

        elif action == "3":
            target = input("\nEnter the English word to delete from JSON: ").strip()
            if not target:
                continue
            confirm = input(f"Are you sure you want to permanently delete '\033[31m{target}\033[0m' from {selected_file['filename']}? (y/N): ").strip().lower()
            if confirm in ["y", "yes", "да"]:
                res = delete_word_from_json(file_path, target)
                if res.get("success"):
                    print(f"\033[32m✔ Successfully deleted '{target}' from {selected_file['filename']}! Remaining: {res.get('remaining_count')}\033[0m")
                else:
                    print(f"\033[31m✘ Error: {res.get('error')}\033[0m")
            else:
                print("Cancelled.")

        elif action == "4":
            new_w = input("\nEnglish word: ").strip()
            new_tr = input("Translation: ").strip()
            ex_en = input("Example sentence (English, optional): ").strip()
            ex_am = input("Example sentence (Translation, optional): ").strip()
            examples = []
            if ex_en or ex_am:
                examples.append({"sentence_en": ex_en, "translation_am": ex_am})
            if new_w:
                res = add_word_to_json(file_path, new_w, new_tr, examples)
                if res.get("success"):
                    print(f"\033[32m✔ Added '{new_w}' directly to {selected_file['filename']}!\033[0m")
                else:
                    print(f"\033[31m✘ Error: {res.get('error')}\033[0m")


def run_csv_conversion():
    """Converts CSV to JSON."""
    all_files = get_data_files("data")
    csv_files = [f for f in all_files if f.suffix.lower() == ".csv"]
    if not csv_files:
        print("No CSV files found in data/")
        return
    print("\nCSV files found:")
    for i, cf in enumerate(csv_files, 1):
        print(f"  {i} : {cf.name}")
    choice = input("\nSelect CSV file number to convert [default: 1]: ").strip()
    idx = int(choice) if choice.isdigit() and 1 <= int(choice) <= len(csv_files) else 1
    selected = csv_files[idx - 1]
    out_name = input(f"Output JSON name [default: {selected.stem}.json]: ").strip()
    if not out_name:
        out_name = f"{selected.stem}.json"
    if not out_name.endswith(".json"):
        out_name += ".json"
    dest_path = data_josn_pathfinder(out_name)
    jsn_loader([selected], dest_path)
    print(f"\033[32mSaved JSON to {dest_path}\033[0m")


def main():
    parser = argparse.ArgumentParser(description="DictCreator - Vocabulary Learning & Review")
    parser.add_argument("--web", "-w", action="store_true", help="Launch the Web UI")
    parser.add_argument("--cli", "-c", action="store_true", help="Run interactive practice directly in terminal")
    parser.add_argument("--manage", "-m", action="store_true", help="Manage and delete words from JSON in terminal")
    parser.add_argument("--host", "-H", type=str, default="0.0.0.0", help="Host IP to bind web server (default: 0.0.0.0)")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Port for the Web UI server (default: 8080)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open desktop browser")
    parser.add_argument("--no-bg", action="store_true", help="Disable iSH iOS background keep-alive")

    args = parser.parse_args()

    if args.web:
        start_server(host=args.host, port=args.port, open_browser=not args.no_browser, enable_bg=not args.no_bg)
        return

    if args.cli:
        run_terminal_practice()
        return

    if args.manage:
        run_word_manager()
        return

    in_ish = is_ish()

    # Interactive Menu
    while True:
        term_cols = shutil.get_terminal_size((60, 20)).columns
        div = "─" * max(20, min(term_cols - 2, 58))

        print(f"\n\033[1;36m{div}\033[0m")
        print("\033[1;36m  📚 DictCreator - Vocabulary Trainer\033[0m")
        if in_ish:
            print("\033[35m  📱 Running on iPhone (iSH)\033[0m")
        print(f"\033[1;36m{div}\033[0m")
        print("  \033[1;32m[1] 🌐 Launch Web UI\033[0m (Recommended: Safari localhost:8080)")
        print("  \033[1;34m[2] 💻 Practice in Terminal\033[0m (CLI flashcards & recall)")
        print("  \033[1;35m[3] 📖 View & Delete Words in Terminal\033[0m")
        print("  \033[1;33m[4] ⚙️  Convert CSV to JSON\033[0m")
        print("  \033[90m[0] ❌ Exit\033[0m")
        print(f"\033[1;36m{div}\033[0m")

        choice = input("Select an option [default: 1]: ").strip()
        if not choice or choice == "1":
            start_server(host=args.host, port=args.port, open_browser=not args.no_browser, enable_bg=not args.no_bg)
            break
        elif choice == "2":
            run_terminal_practice()
        elif choice == "3":
            run_word_manager()
        elif choice == "4":
            run_csv_conversion()
        elif choice in ["0", "q", "exit"]:
            print("Goodbye! Happy learning!")
            break
        else:
            print("Invalid option, please choose between 0 and 4.")


if __name__ == "__main__":
    main()
