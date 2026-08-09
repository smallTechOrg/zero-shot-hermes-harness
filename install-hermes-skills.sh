#!/usr/bin/env bash
#
# install-hermes-skills.sh
# -----------------------------------------------------------------------------
# Install the zero-shot-hermes-harness skills into a LOCAL Hermes install so the
# harness stays OUT of your agent codebases. (See README "Install into a local
# Hermes" for usage + invocation.)
#
# What it does (idempotent — safe to re-run):
#   1. Copies harness/skills/{zero-shot-build,zero-shot-fix,zero-shot-sync}
#      into <HERMES_SKILLS_DIR>/  (each as its own skill directory).
#   2. Copies harness/{agents,patterns,rules,commands} ONCE into a shared
#      <HERMES_SKILLS_DIR>/zero-shot-harness-support/ directory — this is the
#      single debuggable/editable copy of every role, pattern, rule, and command
#      the skills reference.
#   3. Rewrites the skills' relative `harness/...` references to point at that
#      shared support dir (absolute path) so the skills are fully self-contained
#      and need no `harness/` dir at your project root at runtime.
#
# Usage:
#   ./install-hermes-skills.sh                 # use defaults
#   HERMES_SKILLS_DIR=/path/to/skills ./install-hermes-skills.sh
#   ./install-hermes-skills.sh --uninstall     # remove everything it installed
#   ./install-hermes-skills.sh --harness-root /path/to/harness/clone
#
# Env:
#   HERMES_SKILLS_DIR   Override the destination (default: ~/.hermes/skills).
#   HARNESS_ROOT        Override where the harness repo lives (default: the dir
#                       this script lives in).
# -----------------------------------------------------------------------------
set -euo pipefail

# --- resolve harness root (default: this script's directory) ----------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_ROOT="${HARNESS_ROOT:-$SCRIPT_DIR}"
SKILLS_DIR="${HERMES_SKILLS_DIR:-$HOME/.hermes/skills}"

SUPPORT_DIR="$SKILLS_DIR/zero-shot-harness-support"
SKILL_NAMES=(zero-shot-build zero-shot-fix zero-shot-sync)
SUPPORT_SUBDIRS=(agents patterns rules commands)

log()  { printf '\033[1;34m[install-skills]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[install-skills]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[install-skills]\033[0m %s\n' "$*"; }

# --- uninstall ---------------------------------------------------------------
if [[ "${1:-}" == "--uninstall" ]]; then
  log "Removing installed skills + support dir from $SKILLS_DIR"
  for s in "${SKILL_NAMES[@]}"; do
    if [[ -e "$SKILLS_DIR/$s" ]]; then
      rm -rf "$SKILLS_DIR/$s"
      ok "removed $SKILLS_DIR/$s"
    fi
  done
  if [[ -e "$SUPPORT_DIR" ]]; then
    rm -rf "$SUPPORT_DIR"
    ok "removed $SUPPORT_DIR"
  fi
  ok "Uninstall complete."
  exit 0
fi

if [[ "${1:-}" == "--harness-root" ]]; then
  HARNESS_ROOT="$2"
fi

# --- preconditions -----------------------------------------------------------
if [[ ! -d "$HARNESS_ROOT/harness/skills" ]]; then
  echo "ERROR: cannot find harness/skills under HARNESS_ROOT=$HARNESS_ROOT" >&2
  echo "       Run this script from the harness repo, or pass HARNESS_ROOT=/path/to/clone." >&2
  exit 1
fi

mkdir -p "$SKILLS_DIR"
# absolute, normalized support path for rewriting refs
SUPPORT_DIR_ABS="$(cd "$SKILLS_DIR" && pwd)/zero-shot-harness-support"

# --- 1. copy the three skills -----------------------------------------------
for s in "${SKILL_NAMES[@]}"; do
  src="$HARNESS_ROOT/harness/skills/$s"
  dst="$SKILLS_DIR/$s"
  if [[ ! -d "$src" ]]; then
    warn "skill dir not found, skipping: $src"
    continue
  fi
  rm -rf "$dst"
  cp -R "$src" "$dst"
  ok "installed skill: $dst"
done

# --- 2. copy shared support dir (single copy of all referenced files) -------
rm -rf "$SUPPORT_DIR"
mkdir -p "$SUPPORT_DIR"
for d in "${SUPPORT_SUBDIRS[@]}"; do
  src="$HARNESS_ROOT/harness/$d"
  if [[ -d "$src" ]]; then
    cp -R "$src" "$SUPPORT_DIR/$d"
    ok "copied support: $d -> $SUPPORT_DIR/$d"
  else
    warn "support dir not found (skipped): $src"
  fi
done

# --- 3. rewrite harness/... refs -> absolute support path --------------------
# Matches: harness/(agents|patterns|rules|commands)[/optional/path]
REF_RE='harness/(agents|patterns|rules|commands)(/[A-Za-z0-9_./-]*)?'
REPLACEMENT="$SUPPORT_DIR_ABS/\1\2"

rewrite_file() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  # only touch files that actually contain a harness/ ref
  if grep -Eq "$REF_RE" "$f"; then
    if command -v perl >/dev/null 2>&1; then
      perl -i -pe "s{$REF_RE}{$SUPPORT_DIR_ABS/\$1\$2}g" "$f"
    else
      # BSD/GNU sed fallback (no path metachars beyond /._- which sed handles)
      sed -i.bak -E "s|$REF_RE|$SUPPORT_DIR_ABS/\1\2|g" "$f" && rm -f "$f.bak"
    fi
    ok "rewrote refs: $f"
  fi
}

log "Rewriting harness/... references to: $SUPPORT_DIR_ABS"
for s in "${SKILL_NAMES[@]}"; do
  # rewrite SKILL.md and anything under references/
  find "$SKILLS_DIR/$s" \( -name 'SKILL.md' -o -path '*/references/*' \) -type f \
    | while read -r f; do rewrite_file "$f"; done
done

# --- done --------------------------------------------------------------------
ok "Skills installed to: $SKILLS_DIR"
log "Support (roles/patterns/rules/commands): $SUPPORT_DIR_ABS"
log "To remove: ./install-hermes-skills.sh --uninstall"
echo
echo "Skills are now Hermes-native and editable. To tweak behaviour, edit files in:"
echo "  $SKILLS_DIR/zero-shot-build/SKILL.md"
echo "  $SKILLS_DIR/zero-shot-fix/SKILL.md"
echo "  $SKILLS_DIR/zero-shot-sync/SKILL.md"
echo "  $SUPPORT_DIR_ABS/   (roles, patterns, rules, commands)"
