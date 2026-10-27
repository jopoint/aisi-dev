"""Focused Motion UI; state and activation remain on the existing HTTP contract."""
import json
from pathlib import Path


def build_motion_html(state):
    assets = Path(__file__).with_name('learning_format_assets')
    page = (assets/'index.html').read_text(encoding='utf-8')
    settings = json.dumps(state, ensure_ascii=False).replace('<', '\\u003c').replace('&', '\\u0026')
    return (page.replace('{{STYLE}}', (assets/'style.css').read_text(encoding='utf-8'))
            .replace('{{SCRIPT}}', (assets/'app.js').read_text(encoding='utf-8'))
            .replace('{{STATE}}', settings))
