# AGENTS.md — museum.waccamaw.org

Guidance for anyone (human or agent) working on this repo.

## What this is

A living archive of the **Waccamaw Indian People** — the tribe's website through
the years, alongside exhibits on the People, the tribe's history, and the
leadership of **Chief Hatcher**. A GitHub Action builds Hugo and deploys **only**
the compiled output. Site incarnation previews live in `static/sites/<slug>/` and
are wired into the timeline via `data/projects.yaml`.

This repo is **public**. The fuller research record — logos, governing-body
photos, meeting material, tribe-vault documents — lives in the separate **private**
[`waccamaw/museum-archive`](https://github.com/waccamaw/museum-archive) repo and is
never part of this build (see `.gitignore`, which excludes `archive/`).

### Sources for recovered sites
1. The **Internet Archive / Wayback Machine** — the primary source for old
   waccamaw.org incarnations. Use `generators/wayback_snap.py`.
2. Doug's **2012 server backup** on the NAS (`ssh closet`, reachable from the dev
   box) at `/mnt/storage/backups/doug-archive/Projects/superterran.com-9-10-2012.tar.gz`
   — contains the XOOPS and WordPress incarnations of waccamaw.org and waccamaw.us
   (`supa/www/waccamaw/`, `supa/www/waccamawus/`) and their custom themes
   (`waccamawdotorg`, `waccamaw`). Prefer original backup bytes over Wayback where
   both exist; Wayback is lossy (missing CSS/images).

## The cleanup policy (READ THIS)

These artifacts are historical. **Preserve the essence.** We are restoring and
lightly repairing, not rebuilding or modernizing.

When something needs fixing, make the **smallest possible change** that delivers
a specific quality-of-life or functional fix — and **always comment and flag it**
so the original intent stays legible and our edits are obvious.

**Flag convention:** wrap or precede every change with a `MUSEUM-FIX` marker:

```html
<!-- MUSEUM-FIX: stretch banner to fill the viewport (was fixed-size) -->
<div id="banner" style="background-size: cover">
```

### Do
- Stretch/scale a background or banner that no longer fills the screen.
- Hide or gate a broken/always-on element behind its intended trigger.
- Remove a dead embed (missing `.swf`, external counter) that renders an error
  box or a 404.
- Repair an asset path or restore a missing image from the NAS backup.
- Fix encoding mojibake (Win-1252 → UTF-8) and broken-by-time glitches.

### Don't
- Rewrite content, restyle the design, or "modernize" the look.
- Replace the original voice/aesthetic with something cleaner.
- Make large or sweeping edits when a one-line fix will do.
- Touch anything that already works.

## Cultural policy (READ THIS TOO)

This is a tribe's record, published with care.

- **Never publish anything sacred or restricted** — ceremony details, sacred
  sites, or anything members have asked to keep within the community.
- **Never publish restricted member data** — rolls, contact info, or governing-body
  material that belongs in the private `museum-archive`, not here.
- When unsure whether something belongs in public, leave it in `museum-archive`
  and ask. Err toward the community's wishes over completeness.

## Tooling

- `generators/wayback_snap.py <out_dir> <timestamp> <url>` — snapshot a Wayback
  capture into a self-contained static site under `static/sites/<slug>/`.
- `generators/replace_domain.py <from> <to> <path>` — rewrite a legacy host to the
  current one across text files.
- `generators/reencode.py`, `fix_fffd.py` — fix Win-1252 mojibake / U+FFFD.
- `generators/inject_ruffle.py <path>` — revive Flash (.swf) via Ruffle.
- `generators/sanitize_scrub.py <path>` — profanity backstop (rarely needed here).
- `generators/cut_post.py` — retire a post body while preserving the page design.
- `qa/scan.sh` — static content scan (legacy-host links + content review).
- `qa/crawl.mjs [baseURL]` — headless-chromium crawl: broken assets, JS errors,
  full-page screenshots. `cd qa && npm i` once, then
  `node crawl.mjs http://127.0.0.1:1313`.

## Practical notes (dev box quirks)
- Work on `ssh -p 2222 me@10.0.0.226` (bazzite dev box).
- SSH is flaky on big uploads (exit 255 / TLS "bad record MAC") — retry.
- Inline Python over SSH breaks on nested quotes — write scripts to files and `scp` them.
- Commit + push in small increments; the deploy is fast.
- Always cache-bust preview URLs (`?fresh=N`); browsers negative-cache image 404s.
