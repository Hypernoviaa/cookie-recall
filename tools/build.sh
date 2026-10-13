#!/usr/bin/env sh
# Builds dist/cookierecall.ankiaddon in the format AnkiWeb expects:
# the add-on's CONTENTS at the zip root, no __pycache__, no meta.json.
set -e
cd "$(dirname "$0")/.."
mkdir -p dist
find cookierecall -name __pycache__ -prune -exec rm -rf {} +
rm -f dist/cookierecall.ankiaddon
(cd cookierecall && zip -qr ../dist/cookierecall.ankiaddon . -x "meta.json" -x "*/__pycache__/*")
echo "built dist/cookierecall.ankiaddon ($(du -h dist/cookierecall.ankiaddon | cut -f1))"
