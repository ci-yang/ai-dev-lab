"""Deterministic verifier used only to exercise lab failure states."""

import argparse
import sys
from typing import Optional, Sequence


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit a clearly labeled pedagogical verifier result."
    )
    parser.add_argument("result", choices=("pass", "fail", "environment-error"))
    args = parser.parse_args(argv)
    if args.result == "pass":
        sys.stdout.write("PEDAGOGICAL_DEMO: verifier passed\n")
        return 0
    if args.result == "fail":
        sys.stderr.write("PEDAGOGICAL_DEMO: repeated acceptance failure\n")
        return 1
    sys.stderr.write("PEDAGOGICAL_DEMO: verifier environment error\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
