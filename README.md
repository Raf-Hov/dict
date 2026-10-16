# 📚 DictCreator — English Vocabulary Learning & Review

A modern, fast, and convenient vocabulary training application designed for English learners. Review words, practice with example sentences, and **manage or delete words directly from your JSON files**.

---

## 📱 iPhone / iOS (iSH) Quick Start

To run DictCreator directly on your **iPhone 16 Pro** using the **iSH** app:

### 1. Install prerequisites in iSH:
```bash
apk update
apk add python3 git
```

### 2. Run DictCreator:
```bash
sh run.sh web
# or: python3 main.py --web
```

### 3. Open in Safari on your iPhone:
Open Safari and go to:
👉 **`http://localhost:8080`** (or `http://127.0.0.1:8080`)

> 💡 **Keep iSH active in the background**:
> DictCreator automatically enables iOS background keep-alive so the web server continues running when you switch from iSH to Safari. When iOS asks for **Location permission**, tap **"Always"** or **"While Using App"**.
> You can also run CLI practice directly inside iSH with `sh run.sh cli`.

---

## 🚀 Desktop Quick Start

### 🌐 1. Modern Web Interface (Recommended)
Run with turnkey script:
```bash
./run.sh web
```
Or with Python / Makefile:
```bash
python3 main.py --web
# or: make web
```
This automatically launches the modern web application (`http://localhost:8080/`).

#### Features of the Web Interface:
* 🗂️ **Interactive Flashcards**:
  - **Word count selection**: Choose 5, 10, 20, 50, all words, or enter any custom count (`Своё: N`).
  - View word and pronunciation audio 🔊 (built-in speech synthesis, works offline without external APIs).
  - Click or press `Space` to reveal translations and context example sentences.
  - Rate words: `I Know This` (`1` / `→`) or `Review Later` (`2` / `↓`).
  - Mobile swipe gestures: swipe right (know) or swipe left (repeat later).
  - 🗑️ **Delete from JSON**: Click `Delete from JSON` (`Del`) to immediately and permanently remove the word directly from your JSON file (`vocabulary.json`) with confirmation.
* ✍️ **Quiz & Recall Mode (Equivalent to Terminal Practice)**:
  - **Select how many words to ask**: Choose quick presets (5, 10, 20, 50, all) or input any custom number (`1 - Total`, default 20).
  - **Random or sequential order**: `🎲 Random` or `🔢 In order`.
  - **Practice directions**: `🔤 Word ➔ Translation` (prompt English, answer translation — just like terminal practice!), `🌐 Translation ➔ Word`, or `🎲 Mixed`.
  - **Input formats**: `✍️ Typing` mode with smart tolerant matching (handles synonyms, articles, punctuation, and subwords) or `🔘 4 Multiple Choice` for fast mobile practice.
  - **Active learning queue**: Failed or skipped words move to the end of the queue so you keep practicing until 100% of chosen words are mastered!
  - 💡 Context example sentences with masked word hints.
  - 🏆 Session completion screen with first-try accuracy stats, mistake review, and one-click repeat of difficult words.
* 🌟 **Combined Vocabulary**: Option to practice all words from all files in a folder simultaneously (`🌟 Все файлы папки`).
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
