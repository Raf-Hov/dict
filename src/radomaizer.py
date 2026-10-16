import random
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .storage import delete_word_from_json, get_project_root


def _prompt_delete_word(word: str, source_file: Optional[Path | str] = None) -> bool:
    """Prompts the user to confirm deleting a word directly from JSON and performs deletion."""
    root = get_project_root()
    target_path = None

    if source_file:
        p = Path(source_file)
        if not p.is_absolute():
            p = root / p
        if p.exists() and p.suffix.lower() == ".json":
            target_path = p

    # If source_file not given or not a json, search in data folders for a json containing this word
    if not target_path:
        for folder in ["data", "data_for_fr", "data_json"]:
            for jf in (root / folder).glob("*.json"):
                try:
                    with open(jf, "r", encoding="utf-8") as f:
                        content = f.read()
                        if f'"{word}"' in content or f"'{word}'" in content:
                            target_path = jf
                            break
                except Exception:
                    pass
            if target_path:
                break

    if not target_path:
        # Default fallback to data/vocabulary.json if it exists
        default_vocab = root / "data" / "vocabulary.json"
        if default_vocab.exists():
            target_path = default_vocab

    if not target_path or not target_path.exists():
        print(f"\033[31m[Error] Could not locate JSON file to delete '{word}'.\033[0m")
        return False

    confirm = input(f"\n\033[33m⚠️  Are you sure you want to permanently delete '\033[1m{word}\033[0m\033[33m' from {target_path.name}? (y/N): \033[0m").strip().lower()
    if confirm in ["y", "yes", "да"]:
        res = delete_word_from_json(target_path, word)
        if res.get("success"):
            print(f"\033[32m✔ Permanently deleted '{word}' directly from {target_path.name}! (Remaining words: {res.get('remaining_count', '?')})\033[0m\n")
            return True
        else:
            print(f"\033[31m[Error] {res.get('error', 'Failed to delete word')}\033[0m\n")
            return False
    else:
        print("\033[90mDeletion cancelled.\033[0m\n")
        return False


def randomizer(
    word_dicts: dict,
    num: int,
    dict_name: str,
    is_random: bool = True,
    source_file: Optional[Path | str] = None
) -> None:
    """
    Interactive vocabulary learning session in terminal.
    Supports instant word deletion from JSON file directly during practice.
    """
    if dict_name not in word_dicts:
        raise KeyError(f"Dictionary '{dict_name}' not found. Available options: {list(word_dicts.keys())}")

    all_words = list(word_dicts[dict_name].items())
    if len(all_words) < num:
        raise ValueError(f"In '{dict_name}' dictionary only {len(all_words)} words available.")

    if is_random:
        selected_list = random.sample(all_words, num)
        available_words = [w for w in all_words if w not in selected_list]
    else:
        selected_list = all_words[:num]
        available_words = all_words[num:]

    selected_words = deque(selected_list)
    print(f"\n\033[1;36m═══════════════════════════════════════════════════════════════\033[0m")
    print(f"\033[1;36m  🚀 Starting practice with '{dict_name}' ({num} words)  \033[0m")
    print(f"\033[90m  Commands: [Enter: reveal] [n/next: continue] [s/skip: review later]\033[0m")
    print(f"\033[90m            [d/del/delete: permanently delete word from JSON]\033[0m")
    print(f"\033[1;36m═══════════════════════════════════════════════════════════════\033[0m\n")

    while selected_words:
        current_item = selected_words.popleft()
        word, parts = current_item

        main_translation = ""
        examples: List[Any] = []

        if isinstance(parts, list) and len(parts) > 0 and isinstance(parts[0], str):
            main_translation = parts[0]
            examples = parts[1:]
        elif isinstance(parts, dict):
            main_translation = parts.get("translation", "")
            examples = parts.get("examples", [])
        elif isinstance(parts, str):
            main_translation = parts

        queue_status = f"[Queue: \033[1m{len(selected_words) + 1}\033[0m | Remaining: \033[1m{len(available_words)}\033[0m]"

        # Mode A: Sequential / Flashcard style
        if not is_random:
            print(f"{queue_status} Word: \033[1;32m{word}\033[0m")
            ans = input("  [Enter - show translation | 'n' - next | 's' - skip | 'd' - delete from JSON]: ").strip().lower()

            if ans in ["d", "del", "delete"]:
                if _prompt_delete_word(word, source_file):
                    if available_words:
                        new_item = available_words.pop(0)
                        selected_words.append(new_item)
                        print(f"Added replacement word: \033[32m{new_item[0]}\033[0m\n")
                    continue
                else:
                    # Cancelled deletion, put back to front
                    selected_words.appendleft(current_item)
                    continue

            if ans in ["n", "next"]:
                print(f"  Translation: \033[33m{main_translation}\033[0m")
                if available_words:
                    new_item = available_words.pop(0)
                    selected_words.append(new_item)
                    print("  Added replacement word!\n")
                continue

            if ans in ["s", "skip"]:
                print(f"  Translation: \033[33m{main_translation}\033[0m")
                print("  Word moved to end of queue.\n")
                selected_words.append(current_item)
                continue

            # Reveal translation
            print(f"  Translation: \033[1;33m{main_translation}\033[0m")

            # Handle examples
            if examples:
                _handle_terminal_examples(examples, word, source_file)

            print()
            continue

        # Mode B: Random / Active recall mode
        print(f"{queue_status}")
        answer = input(f"Translate the word '\033[1;32m{word}\033[0m' [or 'n' next / 's' skip / 'd' delete]: ").strip().lower()

        if answer in ["d", "del", "delete"]:
            if _prompt_delete_word(word, source_file):
                if available_words:
                    new_item = random.choice(available_words)
                    available_words.remove(new_item)
                    selected_words.append(new_item)
                    print(f"Added replacement word: \033[32m{new_item[0]}\033[0m\n")
                continue
            else:
                selected_words.appendleft(current_item)
                continue

        if answer in ["n", "next"]:
            print(f"  Translation: \033[33m{main_translation}\033[0m")
            if available_words:
                new_item = random.choice(available_words)
                available_words.remove(new_item)
                selected_words.append(new_item)
                print("  Added replacement word!\n")
            continue

        if answer in ["s", "skip"]:
            print(f"  Translation: \033[33m{main_translation}\033[0m")
            print("  Moved to end of queue.\n")
            selected_words.append(current_item)
            continue

        # Check translation correctness
        correct = False
        if answer:
            valid_answers = [x.strip().lower() for x in main_translation.replace(";", ",").split(",")]
            for valid in valid_answers:
                clean_valid = valid.replace("(", "").replace(")", "").strip()
                if answer == valid or answer == clean_valid:
                    correct = True
                    break
            if not correct:
                for valid in valid_answers:
                    clean_valid = valid.replace("(", "").replace(")", "").strip()
                    words_in_valid = clean_valid.split()
                    if answer in words_in_valid:
                        correct = True
                        break

        if correct:
            print("\033[1;32m✔ Correct :)!\033[0m")
            print(f"  Full translation: \033[33m{main_translation}\033[0m\n")
        else:
            print(f"  Translation: \033[1;31m{main_translation}\033[0m")
            print("  Incorrect! Moved to end of queue.\n")
            selected_words.append(current_item)

        if examples:
            _handle_terminal_examples(examples, word, source_file)

        print()

    print("\033[1;32m🎉 Congratulations! You have completed all words in this session!\033[0m\n")


def _handle_terminal_examples(examples: List[Any], word: str, source_file: Optional[Path | str] = None) -> None:
    """Interactively displays and tests example sentences in terminal."""
    print("  \033[90m─── Examples & Sentences ───\033[0m")
    idx = 0
    while idx < len(examples):
        part = examples[idx]
        if isinstance(part, dict):
            en = part.get("sentence_en", part.get("en", ""))
            am = part.get("translation_am", part.get("am", part.get("ru", "")))
            if am:
                print(f"  \033[36mTranslation: {am}\033[0m")
            ans = input("  English sentence [Enter - reveal / 'n' - next / 'd' - delete word]: ").strip().lower()
            if ans in ["d", "del", "delete"]:
                _prompt_delete_word(word, source_file)
                break
            if ans in ["n", "next", "stop"]:
                break
            print(f"  Correct English: \033[1;32m{en}\033[0m\n")
        else:
            print(f"  \033[36m• {part}\033[0m")
            ans = input("  [Enter - next sentence / 'n' - finish examples]: ").strip().lower()
            if ans in ["n", "next", "stop"]:
                break
        idx += 1
