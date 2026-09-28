"""Download the Wikimedia photos used by index.html, shrink them to WebP in img/,
and point the page at the local copies so it loads fast from GitHub Pages."""
import io, re, time, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image

UA = "joyce-family-europe-trip-2027/1.0 (https://github.com/brianskcheng/joyce-family-europe-trip-2027)"
root = Path(__file__).resolve().parent.parent
page = root / "index.html"
out = root / "img"; out.mkdir(exist_ok=True)
html = page.read_text(encoding="utf-8")

def fetch(url):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:
            print("  retry", attempt, url, e); time.sleep(3 * (attempt + 1))
    return None

cache = {}
def local(src, orig):
    if src in cache: return cache[src]
    name = urllib.parse.unquote(orig.rsplit("/", 1)[1])
    stem = re.sub(r"[^A-Za-z0-9]+", "-", name.rsplit(".", 1)[0]).strip("-").lower()[:60]
    dest = out / f"{stem}.webp"
    if not dest.exists():
        data = fetch(src) or fetch(orig)
        if not data:
            cache[src] = None; return None
        im = Image.open(io.BytesIO(data)).convert("RGB")
        im.thumbnail((1000, 1000))
        im.save(dest, "WEBP", quality=72, method=6)
        time.sleep(1)
    w, h = Image.open(dest).size
    cache[src] = (f"img/{dest.name}", w, h)
    print(dest.name, w, h, dest.stat().st_size // 1024, "KB")
    return cache[src]

def fix(m):
    tag = m.group(0)
    src = re.search(r'src="([^"]+)"', tag).group(1)
    orig = re.search(r'data-orig="([^"]+)"', tag)
    orig = orig.group(1) if orig else src
    got = local(src, orig)
    if not got: return tag
    path, w, h = got
    tag = tag.replace(f'src="{src}"', f'src="{path}" width="{w}" height="{h}"')
    tag = re.sub(r'\s(data-orig|referrerpolicy)="[^"]*"', "", tag)
    return tag

html = re.sub(r'<img\b[^>]*src="https://upload\.wikimedia\.org/[^"]+"[^>]*>', fix, html)
html = html.replace("Photos load from the internet, so open this page while online.", "")
page.write_text(html, encoding="utf-8")
left = html.count('src="https://upload.wikimedia.org')
print("remaining remote images:", left)
