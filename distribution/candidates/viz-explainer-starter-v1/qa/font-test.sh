#!/usr/bin/env bash
# Proves the font gate: (1) normal still renders; (2) with a font file hidden the render must FAIL, not fall back.
set -uo pipefail; cd "$(dirname "$0")/.."; mkdir -p out
npx remotion still src/index.ts Draft out/font-ok.png --frame=20 --gl=swangle --log=error || { echo "FONT TEST FAIL: normal still failed"; exit 1; }
mv public/fonts/IBMPlexMono.ttf public/fonts/IBMPlexMono.ttf.hidden
npx remotion still src/index.ts Draft out/font-missing.png --frame=20 --gl=swangle --log=error >out/font-missing.log 2>&1; rc=$?
mv public/fonts/IBMPlexMono.ttf.hidden public/fonts/IBMPlexMono.ttf
if [ $rc -ne 0 ] && grep -qi "font" out/font-missing.log; then echo "FONT TEST PASS (missing font cancels render, rc=$rc)"; else echo "FONT TEST FAIL rc=$rc"; exit 1; fi
