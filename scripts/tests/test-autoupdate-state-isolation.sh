#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

mkdir -p "$TMP_DIR/bin" "$TMP_DIR/home" "$TMP_DIR/state"
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'case " $* " in' \
  '  *" rev-parse HEAD "*) printf "test-revision\\n" ;;' \
  'esac' \
  'exit 0' >"$TMP_DIR/bin/git"
chmod +x "$TMP_DIR/bin/git"

run_update() {
  HOME="$TMP_DIR/home" \
  XDG_STATE_HOME="$TMP_DIR/state" \
  PATH="$TMP_DIR/bin:$PATH" \
    bash "$REPO_ROOT/scripts/autoupdate-skills.sh" \
      --dest "$1" \
      --throttle 3600
}

run_update "$TMP_DIR/codex-skills"
run_update "$TMP_DIR/claude-skills"

stamp_count=$(find "$TMP_DIR/state/nature-skills" -name last-check -type f | wc -l | tr -d ' ')
if [ "$stamp_count" != "2" ]; then
  echo "Expected one independent throttle stamp per destination; found $stamp_count." >&2
  exit 1
fi

echo "Auto-update state isolation passed."
