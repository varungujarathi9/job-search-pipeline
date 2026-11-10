"""CLI: verify a tailored-output JSON file against profile.yaml.

Exits non-zero and prints every violation if any claim is untraceable. This
is the enforcement gate - the /jsp-tailor command must not present or save
an output this CLI rejects.

Usage:
    python -m pipeline.cli.tailor_verify path/to/output.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pipeline.profile import ProfileError, load_profile
from pipeline.tailoring.schema import TailoredOutput
from pipeline.tailoring.verify import verify_output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_json", type=Path)
    parser.add_argument("--profile", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        profile = load_profile(args.profile)
    except ProfileError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    with args.output_json.open("r", encoding="utf-8") as f:
        output = TailoredOutput.from_dict(json.load(f))

    result = verify_output(output, profile)
    if result.is_valid:
        print(f"OK: all {len(output.claims)} claims trace to the profile.")
        return 0

    print(f"BLOCKED: {len(result.violations)} of {len(output.claims)} claims failed verification:", file=sys.stderr)
    for violation in result.violations:
        print(f"  - \"{violation.claim.text}\" -> {violation.reason}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
