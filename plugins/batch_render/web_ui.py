"""Browser assets belong to the plugin release, independently of the host."""
from pathlib import Path

_ASSETS = Path(__file__).parent / 'web_assets'
WEB_HTML = (_ASSETS / 'index.html').read_text(encoding='utf-8')
ACCESS_REQUIRED_HTML = (_ASSETS / 'access.html').read_text(encoding='utf-8')
