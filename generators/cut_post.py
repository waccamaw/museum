#!/usr/bin/env python3
"""Cut the post body from a blog snapshot, keep the shell/design.

Heuristic: a blog post body is long paragraphs; nav/header/footer chrome is
short. Remove <p>/<div> blocks whose visible text exceeds a threshold, drop a
single neutral placeholder where the first one was. Preserves head, styles,
header image, nav, footer. In-place, latin-1.
"""
import sys, re

PLACEHOLDER = ('<p style="font-style:italic;opacity:.8;padding:1em 0">'
               'This entry has been retired from the public archive. '
               'The page is preserved here as a snapshot of how the site '
               'looked at the time.</p>')
THRESHOLD = 140  # chars of visible text

def visible_len(block):
    txt = re.sub(r'<[^>]+>', '', block)
    txt = re.sub(r'&[a-z#0-9]+;', ' ', txt)
    return len(txt.strip())

for path in sys.argv[1:]:
    t = open(path, encoding="latin-1").read()
    # match <p ...>...</p> and <div ...>...</div> non-greedy (paragraph-level)
    placed = [False]
    def repl(m):
        block = m.group(0)
        if visible_len(block) >= THRESHOLD:
            if not placed[0]:
                placed[0] = True
                return PLACEHOLDER
            return ""
        return block
    # paragraphs first
    t2 = re.sub(r'<p\b[^>]*>.*?</p>', repl, t, flags=re.S | re.I)
    open(path, "w", encoding="latin-1").write(t2)
    print(f"cut {path}: placeholder_inserted={placed[0]}")
