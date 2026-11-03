#!/bin/bash
# Render a diorama scene script with Blender and encode it as a ProRes clip for `shot: scene`.
#   render_scene.sh SCENE.py TIMES.json OUT.mov [FPS=23.976] [SAMPLES=32]
# FPS must be the plan's frame rate. Frames go to a temporary folder beside OUT and are removed after encoding.
set -euo pipefail
scene="$1"; times="$2"; out="$3"; fps="${4:-23.976}"; samples="${5:-32}"
blender="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
frames="$(dirname "$out")/.frames_$(basename "$out" .mov)"; rm -rf "$frames"; mkdir -p "$frames"
"$blender" -b --factory-startup --python-exit-code 1 -P "$scene" -- --times "$times" --out "$frames" --fps "$fps" --samples "$samples" \
  > "$frames.log" 2>&1 || { tail -20 "$frames.log"; exit 1; }
rate=$([ "$fps" = "23.976" ] && echo 24000/1001 || echo "$fps")
ffmpeg -v error -y -framerate "$rate" -i "$frames/f_%04d.png" -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le "$out"
n=$(ls "$frames" | wc -l | tr -d ' '); rm -rf "$frames"
echo "$out: $n frames at $fps fps ($(grep -c 'Saved' "$frames.log") rendered)"
