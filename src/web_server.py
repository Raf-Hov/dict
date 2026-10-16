import json
import mimetypes
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict

from .storage import (
    add_word_to_json,
    delete_word_from_json,
    get_available_folders,
    get_project_root,
    list_data_files,
    load_words_from_file,
    update_word_in_json,
)


class DictHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        """Custom logging for clean server output."""
        sys.stderr.write(f"[WebUI] {self.address_string()} - {format % args}\n")

    def _send_json(self, data: Any, status: int = 200) -> None:
        """Sends a JSON response with CORS headers."""
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, content: str, status: int = 200) -> None:
        """Sends HTML content."""
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        """Handles CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        """Handles GET requests for static files and REST API."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # Static index route
        if path in ["/", "/index.html"]:
            html_file = Path(__file__).parent / "web" / "index.html"
            if html_file.exists():
                with open(html_file, "r", encoding="utf-8") as f:
                    self._send_html(f.read())
            else:
                self._send_html("<h1>DictCreator Web UI: index.html not found</h1>", status=404)
            return

        # API: Available folders and files
        if path == "/api/files":
            folder = query.get("folder", ["data"])[0]
            folders = get_available_folders()
            files = list_data_files(folder)
            self._send_json({
                "folders": folders,
                "current_folder": folder,
                "files": files
            })
            return

        # API: Words from file
        if path == "/api/words":
            file_name = query.get("file", ["vocabulary.json"])[0]
            folder_name = query.get("folder", ["data"])[0]
            root = get_project_root()
            target_path = root / folder_name / file_name

            if not target_path.exists():
                self._send_json({"error": f"File {file_name} not found in {folder_name}"}, status=404)
                return

            try:
                words = load_words_from_file(target_path)
                self._send_json({
                    "file": file_name,
                    "folder": folder_name,
                    "is_json": target_path.suffix.lower() == ".json",
                    "total_count": len(words),
                    "words": words
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return

        self._send_json({"error": "Endpoint not found"}, status=404)

    def do_POST(self) -> None:
        """Handles POST requests for mutating JSON words."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            self._send_json({"error": "Invalid JSON body"}, status=400)
            return

        root = get_project_root()

        # API: Delete word from JSON
        if path == "/api/delete_word":
            file_name = body.get("file", "vocabulary.json")
            folder_name = body.get("folder", "data")
            word = body.get("word", "").strip()

            if not word:
                self._send_json({"error": "Word parameter is required"}, status=400)
                return

            target_path = root / folder_name / file_name
            result = delete_word_from_json(target_path, word)
            status = 200 if result.get("success") else 400
            self._send_json(result, status=status)
            return

        # API: Add word to JSON
        if path == "/api/add_word":
            file_name = body.get("file", "vocabulary.json")
            folder_name = body.get("folder", "data")
            word = body.get("word", "").strip()
            translation = body.get("translation", "").strip()
            examples = body.get("examples", [])

            if not word:
                self._send_json({"error": "Word is required"}, status=400)
                return

            target_path = root / folder_name / file_name
            result = add_word_to_json(target_path, word, translation, examples)
            status = 200 if result.get("success") else 400
            self._send_json(result, status=status)
            return

        # API: Update word in JSON
        if path == "/api/update_word":
            file_name = body.get("file", "vocabulary.json")
            folder_name = body.get("folder", "data")
            old_word = body.get("old_word", "").strip()
            new_word = body.get("new_word", "").strip()
            translation = body.get("translation", "").strip()
            examples = body.get("examples", [])

            if not old_word or not new_word:
                self._send_json({"error": "Both old_word and new_word are required"}, status=400)
                return

            target_path = root / folder_name / file_name
            result = update_word_in_json(target_path, old_word, new_word, translation, examples)
            status = 200 if result.get("success") else 400
            self._send_json(result, status=status)
            return

        self._send_json({"error": "Endpoint not found"}, status=404)


def start_server(host: str = "127.0.0.1", port: int = 8080, open_browser: bool = True) -> None:
    """Starts the HTTP server and optionally launches browser."""
    import webbrowser

    server_address = (host, port)
    try:
        httpd = ThreadingHTTPServer(server_address, DictHandler)
    except OSError:
        # Try next port if busy
        port = 8081
        server_address = (host, port)
        httpd = ThreadingHTTPServer(server_address, DictHandler)

    url = f"http://{host}:{port}/"
    print("\n" + "=" * 60)
    print("🚀 DictCreator Web Interface is running!")
    print(f"👉 URL: {url}")
    print("✨ Convenient word practice, flashcards, audio & JSON deletion")
    print("Press Ctrl+C to stop the server.")
    print("=" * 60 + "\n")

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()
        print("Server stopped.")
