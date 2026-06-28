#!/usr/bin/env bash
# Waccamaw museum static content scan — the non-browser half of a quality pass.
# Surfaces (1) stale/off-domain links for nav-vs-historical triage, and
# (2) content that should be reviewed before publishing (profanity backstop +
# a reminder to check for sacred/restricted material). Reports only; never edits.
# Run from the repo root: bash qa/scan.sh
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
ROOTS="static content data layouts"

# Old/dead hosts the tribe's site has lived on. Live nav links to these should be
# rewritten to the current site; historical prose / Wayback URLs stay as artifacts.
OLD_HOSTS='waccamaw\.us|waccamawindians\.org|wixsite\.com|wix\.com|geocities|tripod|angelfire'

echo "############################################################"
echo "#  Off-domain / legacy-host links (rewrite LIVE/NAV only)   #"
echo "#  Leave historical prose, era labels, and Wayback archive  #"
echo "#  URLs (web.archive.org/.../http://...) untouched.         #"
echo "############################################################"
echo "--- candidate LIVE nav links (unescaped href/src to a legacy host) ---"
grep -rniE "(href|src)[[:space:]]*=[[:space:]]*\"https?://([a-z0-9]+\.)?($OLD_HOSTS)" $ROOTS 2>/dev/null \
  | grep -viE 'web\.archive\.org|/assets/|&lt;|&gt;|atom:link' \
  | sed -E 's/(.{140}).*/\1/' || echo "  (none)"
echo
echo "--- ALL other legacy-host mentions (historical — review, usually leave) ---"
grep -rniE "($OLD_HOSTS)" $ROOTS 2>/dev/null \
  | grep -viE 'web\.archive\.org|/assets/' \
  | sed -E 's/(.{120}).*/\1/' | sort | uniq -c | sort -rn | head -40 || true

echo
echo "############################################################"
echo "#  Content review before publishing                         #"
echo "#  1) Profanity backstop (Wayback toolbar cruft excluded)   #"
echo "#  2) MANUAL: confirm nothing sacred/restricted is served — #"
echo "#     ceremony, sacred sites, restricted member data, etc.  #"
echo "############################################################"
grep -rniE '\bnsfw\b|\bporn\b|\bsex\b|\bxxx\b|nigg|\bfag\b|retard' $ROOTS 2>/dev/null \
  | grep -viE '/assets/|var xxx|#xxx|to #xxxxxx' \
  | sed -E 's/(.{150}).*/\1/' || echo "  (no obvious profanity hits)"

echo
echo "Done. This scan only reports. Apply fixes per AGENTS.md (smallest change, MUSEUM-FIX flag)."
echo "Reminder: the public museum must not publish anything sacred or restricted — review in context."
