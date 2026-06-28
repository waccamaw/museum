#!/usr/bin/env python3
"""Sanitize snapshot HTML: a profanity backstop plus an (initially empty) list
of site-specific phrase rewrites. ASCII-safe substring matching so Win-1252
mojibake (curly quotes) doesn't break replacements. Operates in-place, latin-1.

For the Waccamaw archive this is rarely needed — the tribe's sites were
organizational, not personal — but it's kept in the toolkit. Add any
site-specific lines to PHRASE as you find them; the WORD backstop runs always.
"""
import sys, os, re

# Site-specific exact-line rewrites -> harmless, voice-preserving replacements.
# (empty by default — add entries as needed, e.g. ("old crude line", "tame line"))
PHRASE = [
]

# General backstop: whole-word, case-insensitive, mild swaps.
WORD = [
    (r"\bmother\s*f\w*cker\b", "menace"),
    (r"\bf\W?u\W?c\W?k(ing|ers?|ed|s)?\b", lambda m: {"ing":"freaking","er":"goofball","ers":"goofballs","ed":"messed","s":"heck"}.get(m.group(1) or "", "heck")),
    (r"\bshit(ty|s)?\b", lambda m: {"ty":"lousy","s":"stuff"}.get(m.group(1) or "", "stuff")),
    (r"\bbitch(es|ing)?\b", "deal"),
    (r"\bdamn(ed)?\b", lambda m: "darn" + (m.group(1) or "")),
    (r"\bbastards?\b", "guy"),
    (r"\bn[i1]gg\w*\b", "[redacted]"),
    (r"\bf[a4]g(got)?s?\b", "[redacted]"),
]

def scrub(text):
    for a, b in PHRASE:
        text = text.replace(a, b)
    for pat, rep in WORD:
        text = re.sub(pat, rep, text, flags=re.I)
    return text

def split_protect(html):
    # don't scrub inside <script> blocks (Ruffle config etc.)
    parts = re.split(r'(<script\b.*?</script>)', html, flags=re.S|re.I)
    for i in range(0, len(parts), 2):
        parts[i] = scrub(parts[i])
    return "".join(parts)

targets = []
for arg in sys.argv[1:]:
    if os.path.isdir(arg):
        for dp,_,fs in os.walk(arg):
            for fn in fs:
                if fn.lower().endswith((".html",".htm")): targets.append(os.path.join(dp,fn))
    else:
        targets.append(arg)

n=0
for p in targets:
    try:
        t=open(p,encoding="latin-1").read()
    except Exception: continue
    nt=split_protect(t)
    if nt!=t:
        open(p,"w",encoding="latin-1").write(nt); n+=1
print(f"scrubbed {n} files")
