#!/usr/bin/env bash
# Build the two public-candidate archives from distribution/candidates.
# Refuses private paths, bytecode, and a PRIVATE_DO_NOT_SHIP directory.
# Does not upload anything.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT

scan() {
  local tree="$1"
  if [ -d "$tree/PRIVATE_DO_NOT_SHIP" ] || [ -d "$tree/.git" ]; then
    echo "refuse: $tree contains PRIVATE_DO_NOT_SHIP or .git" >&2
    exit 1
  fi
  if find "$tree" -name '*.pyc' -o -name '__pycache__' -o -name 'sheet_real.jpg' | grep -q .; then
    echo "refuse: bytecode or real-presenter sheet in $tree" >&2
    exit 1
  fi
  if grep -R -n -E '/Users/|stevenson|NEWS_INBOX|FINAL VIDEOS|x-access-token|BEGIN OPENSSH|AKIA[0-9A-Z]{16}' "$tree" >/tmp/pack-scan.txt; then
    echo "refuse: private marker in $tree" >&2
    cat /tmp/pack-scan.txt >&2
    exit 1
  fi
}

pack_one() {
  local name="$1" dest="$2"
  local src="$here/candidates/$name"
  rm -rf "$stage/$name"
  mkdir -p "$stage"
  cp -a "$src" "$stage/$name"
  rm -rf "$stage/$name/.venv" "$stage/$name/node_modules" "$stage/$name/out"
  find "$stage/$name" -name '__pycache__' -type d -prune -exec rm -rf {} +
  find "$stage/$name" -name '*.pyc' -delete
  scan "$stage/$name"
  tar -C "$stage" -czf "$dest" "$name"
  sha256sum "$dest"
}

pack_one talking-head-director-0.1.0-rc1 "$here/candidates/talking-head-director-0.1.0-rc1.tar.gz" \
  | tee "$here/talking-head/ENGINE.sha256"
cp "$here/talking-head/ENGINE.sha256" "$here/talking-head/bootstrap/ENGINE.sha256"
pack_one viz-explainer-starter-v1 "$here/candidates/viz-explainer-starter-v1.tar.gz" \
  | tee "$here/viz-explainer/ENGINE.sha256"
cp "$here/viz-explainer/ENGINE.sha256" "$here/viz-explainer/bootstrap/ENGINE.sha256"
echo "archives written; no upload"
