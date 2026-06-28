import sys, re, os

for p in sys.argv[1:]:
    raw = open(p, "rb").read()
    # Diagnose: is it valid UTF-8?
    try:
        raw.decode("utf-8")
        enc = "utf-8"
    except UnicodeDecodeError:
        enc = "cp1252"
    text = raw.decode(enc, errors="replace")
    # If decoded as cp1252, smart quotes/dashes become proper unicode.
    # Ensure a charset meta (try <head>, then <html>, then prepend).
    if "charset" not in text.lower():
        if re.search(r"<head[^>]*>", text, re.I):
            text = re.sub(r"(<head[^>]*>)", r'\1\n<meta charset="utf-8">', text, count=1, flags=re.I)
        elif re.search(r"<html[^>]*>", text, re.I):
            text = re.sub(r"(<html[^>]*>)", r'\1\n<head><meta charset="utf-8"></head>', text, count=1, flags=re.I)
        else:
            text = '<meta charset="utf-8">\n' + text
    open(p, "w", encoding="utf-8").write(text)
    print(f"{p}: decoded_as={enc}, charset_added=True, bytes {len(raw)}->{len(text.encode('utf-8'))}")
