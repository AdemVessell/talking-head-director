#!/bin/sh
# Fetch one versioned VizExplainer starter archive and check its SHA256
# before unpacking into an isolated directory.
# While PUBLISHED is not "yes", the intended GitHub URL is not fetched.
set -eu
here=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
url=$(tr -d '[:space:]' < "$here/RELEASE_URL")
version=$(tr -d '[:space:]' < "$here/VERSION")
published=$(tr -d '[:space:]' < "$here/PUBLISHED")
if [ "$published" != "yes" ]; then
  echo "viz-bootstrap: the intended archive is not live." >&2
  echo "Intended URL (do not fetch; the repository is not confirmed):" >&2
  echo "  $url" >&2
  exit 2
fi
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
