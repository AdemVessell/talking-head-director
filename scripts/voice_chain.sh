#!/usr/bin/env bash
# Voice cleanup + two-pass loudness normalisation.
# usage: voice_chain.sh IN OUT.wav [TARGET_LUFS=-14] [--mix]
#   IN may be audio or video. --mix skips the voice EQ/denoise (use it on a final
#   mix that already contains SFX/music) and only normalises + limits.
set -euo pipefail
in="$1"; out="$2"; I="${3:--14}"; mode="${4:-voice}"
[ "$I" = "--mix" ] && { I=-14; mode=--mix; }
if [ "$mode" = "--mix" ]; then
  pre="anull"
else
  # afftdn delays its output by 1200 samples at 48 kHz; trim it back out (and pad
  # the tail) so the cleaned voice stays frame-locked to the picture.
  pre="aresample=48000,highpass=f=80,afftdn=nr=10:nf=-42:tn=1,atrim=start_sample=1200,asetpts=PTS-STARTPTS,apad=pad_len=1200,deesser=i=0.35,equalizer=f=250:t=q:w=1.0:g=-3,equalizer=f=4000:t=q:w=1.2:g=2.5,equalizer=f=11000:t=h:w=0.7:g=2,acompressor=threshold=-21dB:ratio=3:attack=5:release=90:makeup=2"
fi
ln="loudnorm=I=${I}:TP=-1.5:LRA=8"
stats=$(ffmpeg -hide_banner -nostats -i "$in" -vn -af "${pre},${ln}:print_format=json" -f null - 2>&1 \
  | python3 -c 'import sys,re,json; t=sys.stdin.read(); j=json.loads(re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", t, re.S)[-1]); print(j["input_i"], j["input_tp"], j["input_lra"], j["input_thresh"], j["target_offset"])')
read -r mi mtp mlra mth off <<<"$stats"
ffmpeg -hide_banner -v error -y -i "$in" -vn \
  -af "${pre},${ln}:measured_I=${mi}:measured_TP=${mtp}:measured_LRA=${mlra}:measured_thresh=${mth}:offset=${off}:linear=true,aresample=48000,alimiter=limit=0.89:level=false:latency=true" \
  -c:a pcm_s24le "$out"
echo "in:  ${mi} LUFS, TP ${mtp} dBTP (after chain, before norm)"
ffmpeg -hide_banner -nostats -i "$out" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|Peak:)" | tail -2 | sed 's/^ */out: /'
