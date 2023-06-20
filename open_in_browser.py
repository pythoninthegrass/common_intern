#!/usr/bin/env python3

import json
import webbrowser
from pathlib import Path

# get latest json export
latest_export = max(Path('exports').glob('urls_*.json'))

# read json export
with open(latest_export, 'r') as f:
    urls = json.load(f)

# open new browser window with blank tab
browser = "open -a /Applications/Firefox.app %s"
webbrowser.get(browser).open('about:blank', new=1)

# open urls in browser
[webbrowser.open(url) for url in urls]
