#!/bin/sh
# Fetch one versioned VizExplainer starter archive and check its SHA256
# before unpacking into an isolated directory.
# PLACEHOLDER_RELEASE_URL is not a working download. This script refuses it.
set -eu
here=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
url=$(tr -d '[:space:]' < "$here/RELEASE_URL")
version=$(tr -d '[:space:]' < "$here/VERSION")
case "$url" in
  *PLACEHOLDER*|"" )
    echo "viz-bootstrap: RELEASE_URL is PLACEHOLDER_RELEASE_URL." >&2
    echo "That is not a working download. No public file is being fetched." >&2
    exit 2
    ;;
esac
if [ -f "$here/ENGINE.sha256" ]; then sumfile=$here/ENGINE.sha256; else sumfile=$here/../ENGINE.sha256; fi
sum=$(awk 'NR==1 {print $1}' "$sumfile")
if [ -z "$sum" ]; then
  echo "viz-bootstrap: missing sha256" >&2
  exit 1
fi
dest="${VIZ_HOME:-$HOME/.local/share/viz-explainer-starter}/$version"
if [ -e "$dest" ]; then
  echo "viz-bootstrap: $dest already exists; refusing to overwrite" >&2
  exit 1
fi
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
archive="$tmp/starter.tar.gz"
curl -fsSL -- "$url" -o "$archive"
got=$(sha256sum "$archive" | awk '{print $1}')
if [ "$got" != "$sum" ]; then
  echo "viz-bootstrap: sha256 mismatch" >&2
  echo "  expected $sum" >&2
  echo "  got      $got" >&2
  exit 1
fi
mkdir -p "$(dirname "$dest")"
tar -xzf "$archive" -C "$(dirname "$dest")"
echo "unpacked $version into $dest"
echo "Next: node $dest/setup.mjs <new-empty-dir>"
echo "Read $dest/LICENSES/REMOTION-LICENSE.md before commercial use. Remotion is not MIT."
echo "This starter does not upload renders."
