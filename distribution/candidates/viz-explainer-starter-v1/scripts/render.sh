#!/usr/bin/env bash
# Usage: bash scripts/render.sh [Main|Draft]   -> out/<id>-master.mp4 + out/<id>-compat.mp4 (Baseline, <=720 wide)
# swangle = software WebGL (works on headless Linux w/o GPU). concurrency 1 keeps memory low (~2 GB boxes).
set -euo pipefail
ID="${1:-Draft}"; cd "$(dirname "$0")/.."; mkdir -p out
node scripts/make-sound.mjs
npx remotion render src/index.ts "$ID" "out/$ID-raw.mp4" --gl=swangle --concurrency=1 --muted --log=error
# fit audio: loudnorm then limiter, then measure FINAL encode; adjust gain until -14 LUFS ±1, TP <= -1 dBTP
G=0
for i in 1 2 3 4; do
 ffmpeg -v error -y -i "out/$ID-raw.mp4" -i out/sound.wav -map 0:v -map 1:a -c:v libx264 -profile:v high -level 4.0 -crf 17 -pix_fmt yuv420p \
  -af "loudnorm=I=-14:TP=-2:LRA=11,volume=${G}dB,alimiter=limit=0.8:level=false" -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "out/$ID-master.mp4"
 M=$(ffmpeg -nostats -i "out/$ID-master.mp4" -af ebur128=peak=true -f null - 2>&1 | awk '/Integrated/{f=1} f&&/I:/{i=$2} /True peak/{p=1} p&&/Peak:/{tp=$2} END{print i, tp}')
 I=${M% *}; TP=${M#* }; echo "pass $i gain=${G}dB I=$I LUFS TP=$TP dBTP"
 OK=$(awk -v i="$I" -v p="$TP" 'BEGIN{print (i>=-15&&i<=-13&&p<=-1)?1:0}'); [ "$OK" = 1 ] && break
 G=$(awk -v g="$G" -v i="$I" 'BEGIN{print g+(-14-i)}')
done
[ "$OK" = 1 ] || { echo "audio fit failed"; exit 1; }
W=$(ffprobe -v error -select_streams v -show_entries stream=width -of csv=p=0 "out/$ID-master.mp4")
VF="scale=$(( W>720 ? 720 : W )):-2"
ffmpeg -v error -y -i "out/$ID-master.mp4" -vf "$VF" -c:v libx264 -profile:v baseline -level 3.1 -crf 20 -pix_fmt yuv420p -c:a copy -movflags +faststart "out/$ID-compat.mp4"
rm -f "out/$ID-raw.mp4"; echo done
