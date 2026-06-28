#!/usr/bin/env python3
"""Inject the Ruffle Flash-emulator polyfill into snapshot HTML files.

Ruffle's selfhosted script auto-detects <object>/<embed> Flash content and
replaces it with the WASM emulator, so old .swf files play again. We inject
into every HTML file (frames included) idempotently.
"""
import sys, os, re

RUFFLE = (
    '\n<!-- Ruffle: revive Flash (.swf) in-browser -->\n'
    '<script src="https://unpkg.com/@ruffle-rs/ruffle"></script>\n'
    '<script>window.RufflePlayer=window.RufflePlayer||{};'
    'window.RufflePlayer.config={"autoplay":"on","unmuteOverlay":"hidden",'
    '"warnOnUnsupportedContent":false,"contextMenu":false,"splashScreen":false};</script>\n'
)
MARKER = "@ruffle-rs/ruffle"

roots = sys.argv[1:]
count = 0
for root in roots:
    for dp, _, files in os.walk(root):
        for fn in files:
            if not fn.lower().endswith((".html", ".htm")):
                continue
            p = os.path.join(dp, fn)
            try:
                txt = open(p, encoding="latin-1").read()
            except Exception:
                continue
            if MARKER in txt:
                continue
            # insert before </head>, else after <body...>, else prepend
            m = re.search(r'</head>', txt, re.I)
            if m:
                txt = txt[:m.start()] + RUFFLE + txt[m.start():]
            else:
                mb = re.search(r'<body[^>]*>', txt, re.I)
                if mb:
                    txt = txt[:mb.end()] + RUFFLE + txt[mb.end():]
                else:
                    txt = RUFFLE + txt
            open(p, "w", encoding="latin-1").write(txt)
            count += 1
print(f"Ruffle injected into {count} HTML files")
