#!/usr/bin/env python3
"""Snapshot a Wayback capture into a self-contained static site.

Usage: wayback_snap.py <out_dir> <timestamp> <original_url>

Pulls raw (toolbar-free) HTML via the `id_` modifier, recurses one level
into framesets, downloads sub-resources (img/css/js/swf/background), scans
CSS for url(), and rewrites every reference to a local assets/ file. <a>
navigation links are rewritten to absolute Wayback URLs so exploring still
works without re-hosting the whole tree.
"""
import sys, os, re, hashlib, urllib.request, urllib.parse
from html.parser import HTMLParser

OUT, TS, ROOT_URL = sys.argv[1], sys.argv[2], sys.argv[3]
WB = "https://web.archive.org/web/"
ASSETS_DIR = os.path.join(OUT, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (museum-archiver)"}
_cache = {}

def fetch(url, timeout=45):
    if url in _cache:
        return _cache[url]
    try:
        req = urllib.request.Request(url, headers=UA)
        data = urllib.request.urlopen(req, timeout=timeout).read()
        _cache[url] = data
        return data
    except Exception as e:
        sys.stderr.write(f"  ! fetch fail {url[:80]}: {e}\n")
        _cache[url] = None
        return None

def wb_raw(original):
    """Wayback identity URL for original asset/page (original bytes)."""
    return f"{WB}{TS}id_/{original}"

def fetch_asset(original):
    """Assets: try exact id_, then nearest-capture resolver (raw bytes for
    images/css/js since Wayback only injects toolbar into HTML pages)."""
    d = fetch(f"{WB}{TS}id_/{original}")
    if d is not None:
        return d
    return fetch(f"{WB}{TS}/{original}")

def wb_nav(original):
    """Wayback navigational URL (with toolbar) for <a> links."""
    return f"{WB}{TS}/{original}"

def save_asset(original_abs):
    """Download an asset by original URL, store under assets/, return local rel path."""
    ext = os.path.splitext(urllib.parse.urlparse(original_abs).path)[1][:6]
    if not re.match(r'^\.[A-Za-z0-9]+$', ext):
        ext = ""
    name = hashlib.md5(original_abs.encode()).hexdigest()[:16] + ext
    dest = os.path.join(ASSETS_DIR, name)
    rel = "assets/" + name
    if os.path.exists(dest):
        return rel
    data = fetch_asset(original_abs)
    if data is None:
        return None
    with open(dest, "wb") as f:
        f.write(data)
    # If CSS, rewrite its url() refs too
    if ext.lower() == ".css":
        try:
            txt = data.decode("utf-8", "replace")
            def css_sub(m):
                u = m.group(1).strip('\'"')
                if u.startswith(("data:", "#")):
                    return m.group(0)
                ab = urllib.parse.urljoin(original_abs, u)
                r = save_asset(ab)
                return f"url({r})" if r else m.group(0)
            txt = re.sub(r'url\(([^)]+)\)', css_sub, txt)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(txt)
        except Exception:
            pass
    return rel

class Rewriter(HTMLParser):
    def __init__(self, base):
        super().__init__(convert_charrefs=False)
        self.base = base
        self.out = []
        self.frames = []   # (original_abs) frame docs to recurse
    def _abs(self, u):
        return urllib.parse.urljoin(self.base, u)
    def handle_starttag(self, tag, attrs):
        self._emit(tag, attrs, False)
    def handle_startendtag(self, tag, attrs):
        self._emit(tag, attrs, True)
    def _emit(self, tag, attrs, selfclose):
        attrs = dict(attrs)
        # navigation links -> wayback absolute
        if tag == "a" and attrs.get("href"):
            h = attrs["href"]
            if not h.startswith(("#", "javascript:", "mailto:")):
                attrs["href"] = wb_nav(self._abs(h))
        # framesets -> recurse, point to local snapshot file
        if tag in ("frame", "iframe") and attrs.get("src"):
            ab = self._abs(attrs["src"])
            fname = "frame_" + hashlib.md5(ab.encode()).hexdigest()[:12] + ".html"
            self.frames.append((ab, fname))
            attrs["src"] = fname
        # sub-resources -> download
        for at in ("src", "background", "data"):
            if tag in ("a",) or at not in attrs:
                continue
            if tag in ("frame", "iframe") and at == "src":
                continue
            v = attrs[at]
            if v.startswith(("data:", "#", "javascript:")):
                continue
            r = save_asset(self._abs(v))
            if r:
                attrs[at] = r
        if tag == "link" and attrs.get("href"):
            rel = (attrs.get("rel") or "").lower()
            if "stylesheet" in rel or attrs["href"].lower().split("?")[0].endswith((".css", ".ico", ".png", ".gif")):
                r = save_asset(self._abs(attrs["href"]))
                if r:
                    attrs["href"] = r
        # rebuild tag
        s = "<" + tag
        for k, val in attrs.items():
            if val is None:
                s += f" {k}"
            else:
                s += f' {k}="{val}"'
        s += "/>" if selfclose else ">"
        self.out.append(s)
    def handle_endtag(self, tag):
        self.out.append(f"</{tag}>")
    def handle_data(self, d):
        self.out.append(d)
    def handle_comment(self, d):
        self.out.append(f"<!--{d}-->")
    def handle_entityref(self, n):
        self.out.append(f"&{n};")
    def handle_charref(self, n):
        self.out.append(f"&#{n};")
    def handle_decl(self, d):
        self.out.append(f"<!{d}>")

def process_page(original_abs, outfile):
    data = fetch(wb_raw(original_abs))
    if data is None:
        sys.stderr.write(f"  ! page fetch failed: {original_abs}\n")
        return False
    html = data.decode("utf-8", "replace")
    # strip any wayback toolbar remnants just in case
    html = re.sub(r'<!--\s*BEGIN WAYBACK TOOLBAR INSERT\s*-->.*?<!--\s*END WAYBACK TOOLBAR INSERT\s*-->', '', html, flags=re.S|re.I)
    rw = Rewriter(original_abs)
    rw.feed(html)
    with open(os.path.join(OUT, outfile), "w", encoding="utf-8") as f:
        f.write("".join(rw.out))
    # recurse frames (one level)
    for ab, fname in rw.frames:
        if not os.path.exists(os.path.join(OUT, fname)):
            process_page(ab, fname)
    return True

ok = process_page(ROOT_URL, "index.html")
n_assets = len(os.listdir(ASSETS_DIR))
print(f"{'OK' if ok else 'FAIL'} {OUT}: index.html + {n_assets} assets")
