# 📚 DictCreator — English Vocabulary Learning & Review

A modern, fast, and convenient vocabulary training application designed for English learners. Review words, practice with example sentences, and **manage or delete words directly from your JSON files**.

---

## 🚀 Quick Start

### 🌐 1. Modern Web Interface (Recommended)
Run with Makefile:
```bash
make web
```
Or with Python:
```bash
python3 -m src --web
```
This automatically launches a modern web application in your browser (`http://localhost:8080/`).

#### Features of the Web Interface:
* 🗂️ **Interactive Flashcards**:
  - View word and pronunciation audio 🔊 (built-in speech synthesis, works offline without external APIs).
  - Click or press `Space` to reveal translations and context example sentences.
  - Rate words: `I Know This` (`1` / `→`) or `Review Later` (`2` / `↓`).
  - 🗑️ **Delete from JSON**: Click `Delete from JSON` (`Del`) to immediately and permanently remove the word directly from your JSON file (`vocabulary.json`) with confirmation.
* ✍️ **Quiz & Recall Mode**:
  - Type English translations with instant feedback and tolerant matching.
* 📖 **JSON Dictionary Manager**:
  - Search & filter all words in real time.
  - 🗑️ Direct deletion of any word from the JSON file on disk.
  - ➕ Add new words with translations and example sentences directly to the JSON file.
  - ✏️ Edit words and translations in-place.
* 🌓 **Dark & Light Mode** support.

---

### 💻 2. Terminal Practice (CLI Mode)
Run directly in your terminal:
```bash
make cli
```
Or:
```bash
python3 -m src --cli
```

#### Terminal Hotkeys during Practice:
* `Enter` — Show / reveal translation
* `n` or `next` — Move to next word
* `s` or `skip` — Move word to end of queue to repeat later
* `d`, `del`, or `delete` — **Permanently delete the word directly from the JSON file on disk** (prompts confirmation `y/N`, removes the word from the file, and loads a replacement word).

---

### 📖 3. Terminal Word Manager
To browse, search, and delete words from JSON directly in the terminal:
```bash
make manage
```
Or:
```bash
python3 -m src --manage
```

---

### 📋 Interactive Menu
Run without arguments to access the interactive main menu:
```bash
make run
# or
python3 -m src
```

---

## 📁 JSON Data Format
Your vocabulary files live in `data/` (or `data_for_fr/` for French).
DictCreator automatically handles standard list formats:
```json
[
  {
    "word": "behold",
    "translation": "տեսնել, նայել (բարձր ոճ)",
    "examples": [
      {
        "sentence_en": "(literary) Behold, the sun rises over the mountains.",
        "translation_am": "(գրական) Ահա՛, արևը բարձրանում է լեռների վրա։"
      }
    ]
  }
]
```
All deletions, additions, and updates are saved atomically with UTF-8 encoding and clean indentation.
