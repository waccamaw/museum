#!/usr/bin/env python3
"""Rewrite one domain/host to another across text files in a snapshot.

Usage: replace_domain.py <from> <to> <path> [<path> ...]
  e.g. replace_domain.py waccamaw.us waccamaw.org static/sites/waccamaw-2008

Only swaps in editable text files; reports binary assets (Flash, images) where
the old domain is baked into the bytes and cannot be rewritten. Case-insensitive
match; literal replacement of <from> with <to>.
"""
import sys, re, os

if len(sys.argv) < 4:
    sys.exit("usage: replace_domain.py <from> <to> <path> [<path> ...]")

FROM, TO, roots = sys.argv[1], sys.argv[2], sys.argv[3:]
TEXT_EXT = {".html", ".htm", ".js", ".css", ".inc", ".yaml", ".yml", ".txt", ".php", ".xml", ".json", ".md"}
from_b = FROM.encode()
from_re = re.compile(re.escape(FROM), re.I)
changed = 0
skipped_binary = []

for root in roots:
    for dp, _, files in os.walk(root):
        for fn in files:
            p = os.path.join(dp, fn)
            ext = os.path.splitext(fn)[1].lower()
            try:
                raw = open(p, "rb").read()
            except Exception:
                continue
            if not re.search(re.escape(from_b), raw, re.I):
                continue
            if ext not in TEXT_EXT:
                skipped_binary.append(p)
                continue
            t = raw.decode("utf-8", "replace")
            n = len(from_re.findall(t))
            t = from_re.sub(TO, t)
            open(p, "w", encoding="utf-8").write(t)
            if n:
                changed += 1

print(f"text files rewritten ({FROM} -> {TO}): {changed}")
if skipped_binary:
    print("BINARY (domain baked in, cannot edit):")
    for b in skipped_binary:
        print("  ", b)
