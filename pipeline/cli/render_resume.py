"""CLI: render a one-page resume PDF from a verified tailored draft.

Refuses to render a draft that has not passed pipeline/cli/tailor_verify.py
- this is the same gate, re-run here, so a draft cannot reach a PDF without
also having been checked. Only profile/profile.yaml facts and the verified
draft's own claim text appear in the output; see pipeline/resume.py for how
they're arranged.

Writes two files under data/resumes/, both gitignored like the rest of
data/ (see docs/personal-data.md):
  - data/resumes/<dedupe_key>.pdf           - canonical, stable name
  - data/resumes/<First>_<Last>_Resume_<Company>.pdf - human-friendly copy,
    the one to actually attach to an application upload field

Usage:
    python3 -m pipeline.cli.render_resume <dedupe_key> [--draft PATH] [--matches-dir DIR] [--profile PATH] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from pipeline.profile import ProfileError, load_profile
from pipeline.resume import build_layout
from pipeline.resume_pdf import ResumeTooLongError, render_pdf
from pipeline.tailoring.schema import TailoredOutput
from pipeline.tailoring.verify import verify_output

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DRAFTS_DIR = REPO_ROOT / "data" / "drafts"
DEFAULT_MATCHES_DIR = REPO_ROOT / "data" / "matches"
DEFAULT_OUT_DIR = REPO_ROOT / "data" / "resumes"

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9_-]+")


def _safe_name_part(text: str) -> str:
    cleaned = _UNSAFE_FILENAME_CHARS.sub("_", text.strip())
    return cleaned.strip("_") or "Unknown"


def _find_company_for_dedupe_key(matches_dir: Path, dedupe_key: str) -> str | None:
    if not matches_dir.exists():
        return None
    for matches_file in sorted(matches_dir.glob("*.json")):
        with matches_file.open("r", encoding="utf-8") as f:
            try:
                entries = json.load(f)
            except json.JSONDecodeError:
                continue
        for entry in entries:
            if entry.get("dedupe_key") == dedupe_key:
                return entry.get("company")
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dedupe_key")
    parser.add_argument("--draft", type=Path, default=None)
    parser.add_argument("--matches-dir", type=Path, default=DEFAULT_MATCHES_DIR)
    parser.add_argument("--profile", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)

    draft_path = args.draft or (DEFAULT_DRAFTS_DIR / f"{args.dedupe_key}.json")
    if not draft_path.exists():
        print(f"error: draft not found at {draft_path}", file=sys.stderr)
        return 1

    try:
        profile = load_profile(args.profile)
    except ProfileError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    with draft_path.open("r", encoding="utf-8") as f:
        output = TailoredOutput.from_dict(json.load(f))

    result = verify_output(output, profile)
    if not result.is_valid:
        print(
            f"REFUSED: draft at {draft_path} has {len(result.violations)} unverified claim(s). "
            "Run pipeline.cli.tailor_verify and fix every violation before rendering a resume:",
            file=sys.stderr,
        )
        for violation in result.violations:
            print(f"  - \"{violation.claim.text}\" -> {violation.reason}", file=sys.stderr)
        return 1

    layout = build_layout(output, profile)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    canonical_path = args.out_dir / f"{args.dedupe_key}.pdf"
    name_parts = layout.candidate_name.split()
    first = _safe_name_part(name_parts[0]) if name_parts else "Unknown"
    last = _safe_name_part(name_parts[-1]) if len(name_parts) > 1 else "Resume"
    company = _find_company_for_dedupe_key(args.matches_dir, args.dedupe_key) or output.target_company
    friendly_name = f"{first}_{last}_Resume_{_safe_name_part(company)}.pdf"
    friendly_path = args.out_dir / friendly_name

    try:
        render_pdf(layout, canonical_path)
        render_pdf(layout, friendly_path)
    except ResumeTooLongError as exc:
        print(f"error: {exc}", file=sys.stderr)
        canonical_path.unlink(missing_ok=True)
        friendly_path.unlink(missing_ok=True)
        return 1

    print(f"OK: wrote {canonical_path}")
    print(f"OK: wrote {friendly_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
