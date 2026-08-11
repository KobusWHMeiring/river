"""Architecture Guard — deterministic BUILD PRINCIPLES enforcement.

Usage: python -m scripts.archguard <phase-slug>
"""
import re
import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import rules to trigger @rule registration
from .rules import python_ast  # noqa: F401
from .rules import templates  # noqa: F401
from .rules import css_js  # noqa: F401
from .rules import discover
from .audit_writer import write_audit


def sanitize_slug(slug: str) -> str:
    """Reject slugs with path separators."""
    if re.search(r"[/\\]", slug):
        print(
            f"ERROR: Phase slug '{slug}' contains path separators. "
            f"Use a simple name like 'finance-dashboard-phase2'."
        )
        sys.exit(2)
    return slug.strip()


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.archguard <phase-slug>")
        sys.exit(2)

    slug = sanitize_slug(sys.argv[1])
    skipped = [
        "migrations",
        "tests",
        "management/commands",
        "venv",
        "node_modules",
        "__pycache__",
    ]

    print(f"[ArchGuard] Auditing phase '{slug}'...")

    all_violations = []
    rules = discover()

    for fn in rules:
        rule_id = getattr(fn, "rule_id", "unknown")
        severity = getattr(fn, "severity", "WARNING")
        print(f"  Running {rule_id} ({severity})...")
        try:
            result = fn()
            if result:
                all_violations.extend(result)
        except Exception as e:
            print(f"  WARN: {rule_id} crashed: {e}")

    output_path = write_audit(slug, all_violations, skipped)

    errors = sum(1 for v in all_violations if v.severity == "ERROR")
    warnings = sum(1 for v in all_violations if v.severity == "WARNING")

    print(f"\n[ArchGuard] Audit written to {output_path}")
    print(f"   Errors: {errors}, Warnings: {warnings}")

    if errors > 0:
        print(
            f"\n[FAIL] {errors} architectural error(s) detected. "
            f"Review {output_path} and fix before proceeding."
        )
        sys.exit(1)
    elif warnings > 0:
        print(f"\n[WARN] {warnings} warning(s). Review {output_path} before proceeding.")
        sys.exit(0)
    else:
        print("\n[PASS] Architecture guard passed — phase is clean.")
        sys.exit(0)


if __name__ == "__main__":
    main()
