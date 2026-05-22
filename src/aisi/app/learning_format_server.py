"""Small local web server to select the current learning format.

This uses only the Python standard library. Open the server on a tablet or in a
browser on the same network and choose between input, groupwork, and discussion.
The selected value is written to data/aisi/state/learning_format.json.
"""

from __future__ import annotations

import argparse
import json
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


DEFAULT_PORT = 8080
DEFAULT_LEARNING_FORMAT = "groupwork"
VALID_LEARNING_FORMATS = {"input", "groupwork", "discussion"}
DEFAULT_SHOW_PERSONS = True
DEFAULT_SHOW_CHAIRS = True
DEFAULT_TRANSFORMATION_STRENGTH = 0.5


def clamp_transformation_strength(value: object) -> float:
    """Clamp the slider value to the expected 0.0..1.0 range."""

    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return DEFAULT_TRANSFORMATION_STRENGTH


def default_state() -> dict[str, object]:
    """Return the default state for the web UI and JSON file."""
    return {
        "learning_format": DEFAULT_LEARNING_FORMAT,
        "show_persons": DEFAULT_SHOW_PERSONS,
        "show_chairs": DEFAULT_SHOW_CHAIRS,
        "transformation_strength": DEFAULT_TRANSFORMATION_STRENGTH,
    }


def repo_root() -> Path:
    """Return the repository root based on this file location."""
    return Path(__file__).resolve().parents[3]


def state_dir() -> Path:
    """Return the folder that stores the learning format state."""
    folder = repo_root() / "data" / "aisi" / "state"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def state_file_path() -> Path:
    """Return the JSON file that stores the current learning format."""
    return state_dir() / "learning_format.json"


def ensure_state_file() -> None:
    """Create the state file with a default value if it does not exist yet."""
    path = state_file_path()
    if not path.exists():
        write_state(default_state())


def read_state() -> dict[str, object]:
    """Read the current UI state and fall back to defaults if needed."""
    state = default_state()
    path = state_file_path()
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return state

    learning_format = data.get("learning_format", DEFAULT_LEARNING_FORMAT)
    if learning_format in VALID_LEARNING_FORMATS:
        state["learning_format"] = learning_format

    if isinstance(data.get("show_persons"), bool):
        state["show_persons"] = data["show_persons"]

    if isinstance(data.get("show_chairs"), bool):
        state["show_chairs"] = data["show_chairs"]

    state["transformation_strength"] = clamp_transformation_strength(
        data.get("transformation_strength", DEFAULT_TRANSFORMATION_STRENGTH)
    )

    return state


def read_learning_format() -> str:
    """Read the currently stored learning format."""
    return str(read_state()["learning_format"])


def write_state(state: dict[str, object]) -> bool:
    """Write the full UI state to disk."""
    payload = default_state()

    learning_format = state.get("learning_format", DEFAULT_LEARNING_FORMAT)
    if learning_format in VALID_LEARNING_FORMATS:
        payload["learning_format"] = learning_format

    if isinstance(state.get("show_persons"), bool):
        payload["show_persons"] = state["show_persons"]

    if isinstance(state.get("show_chairs"), bool):
        payload["show_chairs"] = state["show_chairs"]

    payload["transformation_strength"] = clamp_transformation_strength(
        state.get("transformation_strength", DEFAULT_TRANSFORMATION_STRENGTH)
    )

    path = state_file_path()
    temp_path = path.with_suffix(".tmp")

    try:
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        temp_path.replace(path)
        return True
    except OSError as exc:
        print(f"Could not save learning format state: {exc}")
        return False


def write_learning_format(value: str) -> bool:
    """Write a new learning format to disk. Invalid values are ignored."""
    if value not in VALID_LEARNING_FORMATS:
        return False

    state = read_state()
    state["learning_format"] = value
    return write_state(state)


def toggle_state_flag(key: str) -> bool:
    """Toggle a boolean flag in the stored UI state."""
    state = read_state()
    current_value = state.get(key, False)
    if not isinstance(current_value, bool):
        current_value = False
    state[key] = not current_value
    return write_state(state)


def get_local_ip() -> str:
    """Best-effort helper to show the local network IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def build_html(current_format: str, show_persons: bool, show_chairs: bool, transformation_strength: float) -> str:
    """Build a very simple mobile-friendly HTML page."""
    persons_text = "on" if show_persons else "off"
    chairs_text = "on" if show_chairs else "off"
    strength_percent = int(round(clamp_transformation_strength(transformation_strength) * 100.0))
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>AISI Learning Format</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 24px;
      background: #111;
      color: #fff;
    }}
    h1 {{
      font-size: 2.2rem;
      margin-bottom: 12px;
    }}
    p {{
      font-size: 1.3rem;
      line-height: 1.4;
    }}
    .buttons {{
      display: flex;
      flex-direction: column;
      gap: 16px;
      margin-top: 24px;
      max-width: 420px;
    }}
        .slider-card {{
            margin-top: 20px;
            max-width: 420px;
            padding: 18px;
            border-radius: 18px;
            background: #1c1c1c;
        }}
        .slider-label {{
            display: flex;
            justify-content: space-between;
            gap: 12px;
            font-size: 1.2rem;
            margin-bottom: 10px;
        }}
        input[type="range"] {{
            width: 100%;
        }}
        .slider-value {{
            color: #9fe29f;
            font-weight: bold;
        }}
        .toggles {{
            display: flex;
            flex-direction: column;
            gap: 16px;
            margin-top: 18px;
            max-width: 420px;
        }}
    button {{
      font-size: 2rem;
      padding: 22px 18px;
      border: 0;
      border-radius: 18px;
      cursor: pointer;
      background: #2a2a2a;
      color: #fff;
    }}
    button:active {{
      transform: scale(0.99);
    }}
    .current {{
      margin-top: 18px;
      font-size: 1.5rem;
      color: #9fe29f;
    }}
        .state {{
            margin-top: 12px;
            font-size: 1.3rem;
            color: #d7e4ff;
        }}
    .input {{ background: #4b6cff; }}
    .groupwork {{ background: #2f9e44; }}
    .discussion {{ background: #c92a2a; }}
    .toggle {{ background: #444; }}
  </style>
</head>
<body>
  <h1>AISI Learning Format</h1>
  <p>Choose the current learning format for the simulation.</p>
  <form class=\"buttons\" method=\"post\" action=\"/set\">
    <button class=\"input\" type=\"submit\" name=\"learning_format\" value=\"input\">1. Input</button>
    <button class=\"groupwork\" type=\"submit\" name=\"learning_format\" value=\"groupwork\">2. Groupwork</button>
    <button class=\"discussion\" type=\"submit\" name=\"learning_format\" value=\"discussion\">3. Discussion</button>
  </form>
    <form class="slider-card" method="post" action="/set">
        <div class="slider-label">
            <span>Umbauintensität</span>
            <span class="slider-value" id="transformation-strength-value">{strength_percent}%</span>
        </div>
        <input
            id="transformation-strength"
            type="range"
            name="transformation_strength"
            min="0"
            max="100"
            step="1"
            value="{strength_percent}"
            onchange="this.form.submit()"
            oninput="document.getElementById('transformation-strength-value').textContent = this.value + '%'"
        >
    </form>
    <form class="toggles" method="post" action="/set">
        <button class="toggle" type="submit" name="toggle" value="persons">Persons: {persons_text}</button>
        <button class="toggle" type="submit" name="toggle" value="chairs">Chairs: {chairs_text}</button>
    </form>
    <div class="current">Current learning format: {current_format}</div>
    <div class="state">Persons: {persons_text}</div>
    <div class="state">Chairs: {chairs_text}</div>
</body>
</html>"""


class LearningFormatHandler(BaseHTTPRequestHandler):
    """Handle the simple HTML page and form submissions."""

    def do_GET(self) -> None:
        """Return the HTML page."""
        if urlparse(self.path).path not in {"/", ""}:
            self.send_error(404, "Not found")
            return

        state = read_state()
        html = build_html(
            str(state["learning_format"]),
            bool(state["show_persons"]),
            bool(state["show_chairs"]),
            float(state["transformation_strength"]),
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def do_POST(self) -> None:
        """Store the selected learning format and show the updated page."""
        parsed_path = urlparse(self.path)
        if parsed_path.path != "/set":
            self.send_error(404, "Not found")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        form_data = parse_qs(body)
        selected = form_data.get("learning_format", [""])[0]
        toggle = form_data.get("toggle", [""])[0]
        transformation_strength_raw = form_data.get("transformation_strength", [""])[0]

        state = read_state()
        changed = False

        if selected in VALID_LEARNING_FORMATS:
            state["learning_format"] = selected
            changed = True
        elif toggle == "persons":
            state["show_persons"] = not bool(state.get("show_persons", DEFAULT_SHOW_PERSONS))
            changed = True
        elif toggle == "chairs":
            state["show_chairs"] = not bool(state.get("show_chairs", DEFAULT_SHOW_CHAIRS))
            changed = True

        if transformation_strength_raw != "":
            try:
                state["transformation_strength"] = clamp_transformation_strength(int(transformation_strength_raw) / 100.0)
                changed = True
            except ValueError:
                pass

        if changed:
            write_state(state)

        html = build_html(
            str(state["learning_format"]),
            bool(state["show_persons"]),
            bool(state["show_chairs"]),
            float(state["transformation_strength"]),
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, format: str, *args: object) -> None:
        """Keep the console output simple and readable."""
        print(format % args)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the AISI learning format server.")
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="HTTP port (default: 8080).",
    )
    return parser.parse_args()


def main() -> None:
    """Start the local web server."""
    args = parse_args()
    ensure_state_file()

    local_ip = get_local_ip()
    server = HTTPServer(("0.0.0.0", args.port), LearningFormatHandler)

    print(f"Learning format server running at http://127.0.0.1:{args.port}")
    print(f"Open this URL on a tablet in the same network: http://{local_ip}:{args.port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
