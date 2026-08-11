"""CSS/JS delegation rules — wraps existing checkers."""
import subprocess
from pathlib import Path

from ..rules import rule
from ..violation import Violation

PROJECT_ROOT = Path.cwd()


def _run_checker(script_name: str) -> list[Violation]:
    """Run an existing checker script and parse its output into violations."""
    script_path = PROJECT_ROOT / script_name
    if not script_path.exists():
        return [
            Violation(
                rule_id="CSS-JS-DELEGATE",
                severity="WARNING",
                category="css",
                file=str(script_name),
                line=0,
                message=f"Delegated checker {script_name} not found — skipping.",
                snippet=None,
            )
        ]
    try:
        result = subprocess.run(
            ["python", str(script_path)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
        )
    except subprocess.TimeoutExpired:
        return [
            Violation(
                rule_id="CSS-JS-DELEGATE",
                severity="WARNING",
                category="css",
                file=str(script_name),
                line=0,
                message=f"Delegated checker {script_name} timed out.",
                snippet=None,
            )
        ]
    except Exception as e:
        return [
            Violation(
                rule_id="CSS-JS-DELEGATE",
                severity="WARNING",
                category="css",
                file=str(script_name),
                line=0,
                message=f"Delegated checker {script_name} crashed: {e}",
                snippet=None,
            )
        ]

    violations = []
    for line in result.stdout.splitlines() + result.stderr.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("OK:") or line.startswith("All tokens"):
            continue
        if (
            "ERROR:" in line
            or "Warning:" in line
            or "Unclosed" in line
            or "Unexpected" in line
        ):
            violations.append(
                Violation(
                    rule_id=f"{script_name}",
                    severity="WARNING",
                    category="css" if "css" in script_name else "js",
                    file=str(script_name),
                    line=0,
                    message=line,
                    snippet=None,
                )
            )
    return violations


@rule("CSS-LAYOUT", severity="WARNING", category="css")
def check_css_layout():
    return _run_checker("check_layout_utilities.py")


@rule("CSS-CLASSES", severity="WARNING", category="css")
def check_css_classes():
    return _run_checker("check_css_classes.py")



