# museum.waccamaw.org

A living digital archive of the **Waccamaw Indian People** — every recoverable
incarnation of waccamaw.org through the years, plus exhibits on the People, our
history, and the leadership of **Chief Hatcher**.

Built with [Hugo](https://gohugo.io), deployed to GitHub Pages, and modeled on the
museum.superterran.net project (same structure and concept, Waccamaw brand palette).

## Structure
- `content/` — exhibit pages (Markdown) — served publicly.
- `content/sites/` — locally hosted snapshots of past incarnations (as captured).
- `data/projects.yaml` — drives the homepage timeline of incarnations.
- `assets/css/main.css` — Waccamaw earth-tone palette (cream, brown, navy, blue).
- `assets/shots/` — incarnation screenshots used on cards.
- `layouts/` — Hugo templates (baseof, index, single).
- `archive/` — **private, never served by the build:**
  - `archive/web/` — raw mirrors of past site incarnations.
  - `archive/research/` — forensic notes on the collection effort.
  - `archive/corpus/` — the private research corpus on the Waccamaw Indian People
    and Chief Hatcher, gathered for study and future publication.

## Principle
The public site shows what the tribe shared with the world. The private archive
gathers the fuller record for the tribe's own study. Nothing sacred or restricted
is published.

## Deploy
Push to `main` → GitHub Actions builds with Hugo → GitHub Pages serves at
`museum.waccamaw.org` (set the `CNAME` / custom domain in repo Pages settings + DNS).
