import sys, os
from playwright.sync_api import sync_playwright
from pathlib import Path
out=os.environ['TEMP']
with sync_playwright() as pw:
    b=pw.chromium.launch(channel="msedge"); pg=b.new_page(viewport={'width':794,'height':1123})
    pg.goto(Path('programme.html').resolve().as_uri())
    for n in map(int, sys.argv[1:]):
        pg.locator('section.page').nth(n-1).screenshot(path=f"{out}/p{n}.png")
    b.close()
