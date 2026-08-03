#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

DEST="$TMP_DIR/skills"
VICTIM="$TMP_DIR/victim"
SAFE_STALE="nature-removed-test"

mkdir -p "$DEST/$SAFE_STALE" "$VICTIM"
touch "$VICTIM/must-survive"
printf '%s\n' \
  '# test manifest' \
  '../victim' \
  "$SAFE_STALE" >"$DEST/.nature-skills-install.txt"

bash "$REPO_ROOT/scripts/update-codex-skills.sh" \
  --dest "$DEST" \
  --prune >"$TMP_DIR/stdout" 2>"$TMP_DIR/stderr"

if [ ! -f "$VICTIM/must-survive" ]; then
  echo "Unsafe manifest entry escaped the destination directory." >&2
  exit 1
fi

if [ -d "$DEST/$SAFE_STALE" ]; then
  echo "Safe stale managed directory was not pruned." >&2
  exit 1
fi

if ! grep -Fq "ignoring unsafe managed skill name" "$TMP_DIR/stderr"; then
  echo "Unsafe manifest entry was not reported." >&2
  exit 1
fi

echo "Skill prune safety passed."
