#!/usr/bin/env bash
# Fails if any personal-data path is tracked by git.
# Personal paths are the real profile, real company list, and the data/ directory
# (runtime postings, tracker spreadsheet, generated resumes, referral drafts, credentials).
# See docs/personal-data.md for the contract this enforces.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"

PERSONAL_PATTERNS=(
  '^profile/profile\.yaml$'
  '^config/companies\.yaml$'
  '^data/'
  '(^|/)credentials\.json$'
  '(^|/)token\.json$'
  '(^|/)\.env$'
  '(^|/)\.env\.[^/]*$'
)

tracked_files="$(git -C "$REPO_ROOT" ls-files)"
violations=()

while IFS= read -r pattern; do
  [ -z "$pattern" ] && continue
  matches="$(printf '%s\n' "$tracked_files" | grep -E "$pattern" || true)"
  if [ -n "$matches" ]; then
    while IFS= read -r m; do
      violations+=("$m")
    done <<< "$matches"
  fi
done <<< "$(printf '%s\n' "${PERSONAL_PATTERNS[@]}")"

if [ "${#violations[@]}" -gt 0 ]; then
  echo "FAIL: personal-data path(s) are tracked by git:" >&2
  for v in "${violations[@]}"; do
    echo "  $v" >&2
  done
  echo "These paths must stay gitignored. See docs/personal-data.md." >&2
  exit 1
fi

echo "OK: no personal-data paths are tracked."
