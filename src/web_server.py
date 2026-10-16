from __future__ import annotations

import json
import mimetypes
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, Optional

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
            total_words_in_folder = sum(f.get("word_count", 0) for f in files)
            self._send_json({
                "folders": folders,
                "current_folder": folder,
                "files": files,
                "total_words": total_words_in_folder
            })
            return

        # API: Words from file
        if path == "/api/words":
            file_name = query.get("file", ["vocabulary.json"])[0]
            folder_name = query.get("folder", ["data"])[0]
            root = get_project_root()

            if file_name in ["__all__", "all"]:
                folder_path = root / folder_name
                all_files = sorted(list(folder_path.glob("*.json")) + list(folder_path.glob("*.csv")))
                merged_words = []
                seen_words = set()
                for fp in all_files:
                    try:
                        w_list = load_words_from_file(fp)
                        for w in w_list:
                            k = w.get("word", "").strip().lower()
                            if k and k not in seen_words:
                                seen_words.add(k)
                                merged_words.append(w)
                    except Exception:
                        pass
                self._send_json({
                    "file": "__all__",
                    "folder": folder_name,
                    "is_json": False,
                    "total_count": len(merged_words),
                    "words": merged_words
                })
                return

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

            if file_name in ["__all__", "all"]:
                folder_path = root / folder_name
                result = {"success": False, "error": f"Word '{word}' not found in any JSON file"}
                for jf in folder_path.glob("*.json"):
                    res = delete_word_from_json(jf, word)
                    if res.get("success"):
                        result = res
                        break
            else:
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


class SafeHTTPServer(HTTPServer):
    """Single-threaded HTTP server with address reuse to avoid port collision and iSH pthread bugs."""
    allow_reuse_address = True
    daemon_threads = True


def is_ish() -> bool:
    """Detects if running inside the iSH iOS app."""
    if os.path.exists("/proc/ish") or os.path.exists("/proc/driver/ish"):
        return True
    if os.path.exists("/dev/location"):
        return True
    try:
        if os.path.exists("/proc/version"):
            with open("/proc/version", "r") as f:
                if "ish" in f.read().lower():
                    return True
    except Exception:
        pass
    return False


def get_local_ip() -> str:
    """Attempts to find the device's local network IP."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def start_ish_background_keeper() -> Optional[Any]:
    """
    Keeps iSH running in the background on iOS when switching to Safari.
    Reads from /dev/location which signals iOS that iSH is actively using location.
    """
    if not os.path.exists("/dev/location"):
        return None
    try:
        import subprocess
        proc = subprocess.Popen(
            ["cat", "/dev/location"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
        return proc
    except Exception:
        return None


def start_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    open_browser: bool = True,
    enable_bg: bool = True
) -> None:
    """Starts the HTTP server and optionally launches browser."""
    import webbrowser

    # Find an open port
    httpd = None
    actual_port = port
    for p in range(port, port + 10):
        try:
            httpd = SafeHTTPServer((host, p), DictHandler)
            actual_port = p
            break
        except OSError:
            continue

    if httpd is None:
        print(f"\033[31m[Error] Could not bind to any port in range {port}-{port+9}\033[0m")
        return

    in_ish = is_ish()
    local_ip = get_local_ip()

    local_url = f"http://localhost:{actual_port}/"
    ip_url = f"http://{local_ip}:{actual_port}/"

    ish_keeper = None
    if in_ish and enable_bg:
        ish_keeper = start_ish_background_keeper()

    print("\n\033[1;36m" + "═" * 58 + "\033[0m")
    print("\033[1;32m🚀 DictCreator Web Server is running!\033[0m")
    if in_ish:
        print("\033[1;35m📱 [iPhone / iSH Mode Detected]\033[0m")
        if ish_keeper:
            print("\033[33m⚡ Background keep-alive ACTIVE (keeps iSH alive in Safari)\033[0m")
            print("   \033[90m(If iOS asks for Location permission, tap 'Always' or 'While Using')\033[0m")
        print(f"\n👉 \033[1mOpen Safari on this iPhone:\033[0m")
        print(f"   \033[1;34m{local_url}\033[0m  or  \033[1;34mhttp://127.0.0.1:{actual_port}/\033[0m")
        if local_ip != "127.0.0.1":
            print(f"👉 \033[1mFrom another device (PC / Mac / iPad):\033[0m \033[1;34m{ip_url}\033[0m")
    else:
        print(f"👉 Local URL:   \033[1;34m{local_url}\033[0m")
        if local_ip != "127.0.0.1":
            print(f"👉 Network URL: \033[1;34m{ip_url}\033[0m")

    print("\n✨ Flashcards, audio speech, quiz, and JSON management")
    print("Press \033[1mCtrl+C\033[0m in terminal to stop.")
    print("\033[1;36m" + "═" * 58 + "\033[0m\n")

    # Only attempt browser launch on desktop with GUI display
    if open_browser and not in_ish:
        if sys.platform.startswith("linux") and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            pass
        else:
            try:
                webbrowser.open(local_url)
            except Exception:
                pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        if ish_keeper:
            try:
                ish_keeper.terminate()
            except Exception:
                pass
        try:
            httpd.server_close()
        except Exception:
            pass
        print("Server stopped.")
