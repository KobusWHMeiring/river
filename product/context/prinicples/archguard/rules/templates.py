"""Template rules for architecture guard."""
import re
from pathlib import Path

from ..rules import rule
from ..violation import Violation

TEMPLATE_DIR = Path("src/templates")
CDN_PATTERN = re.compile(r'(?:src|href)=["\'](?:https?://|//cdn)', re.IGNORECASE)


def _get_template_dir() -> Path:
    """Resolve template dir at call time so tests can chdir."""
    return TEMPLATE_DIR.resolve()


def _relpath(path: Path) -> str:
    """Return path relative to CWD, or just the path string."""
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


@rule("RU-007", severity="WARNING", category="template")
def check_cdn_in_templates():
    """Flag CDN references in HTML templates."""
    violations = []
    template_dir = _get_template_dir()
    if not template_dir.exists():
        return violations
    for html_file in template_dir.rglob("*.html"):
        try:
            content = html_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for lineno, line in enumerate(content.splitlines(), start=1):
            if CDN_PATTERN.search(line):
                violations.append(
                    Violation(
                        rule_id="RU-007",
                        severity="WARNING",
                        category="template",
                        file=_relpath(html_file),
                        line=lineno,
                        message="CDN reference detected in template — project must work offline (Total Isolation principle).",
                        snippet=line.strip()[:120],
                    )
                )
    return violations


@rule("RU-009", severity="WARNING", category="template")
def check_template_nesting():
    """Flag deeply nested {% if %} / {% for %} blocks."""
    violations = []
    template_dir = _get_template_dir()
    if not template_dir.exists():
        return violations
    TAG_PATTERN = re.compile(r"\{%-?\s*(if|for)\s.*?%\}")
    END_PATTERN = re.compile(r"\{%-?\s*end(if|for)\s.*?%\}")

    for html_file in template_dir.rglob("*.html"):
        try:
            content = html_file.read_text(encoding="utf-8")
        except Exception:
            continue
        depth = 0
        max_depth = 0
        max_depth_line = 0
        for lineno, line in enumerate(content.splitlines(), start=1):
            opens = len(TAG_PATTERN.findall(line))
            closes = len(END_PATTERN.findall(line))
            depth += opens - closes
            if depth > max_depth:
                max_depth = depth
                max_depth_line = lineno
        if max_depth > 2:
            violations.append(
                Violation(
                    rule_id="RU-009",
                    severity="WARNING",
                    category="template",
                    file=_relpath(html_file),
                    line=max_depth_line,
                    message=f"Template nesting depth {max_depth} exceeds limit of 2 — consider extracting a partial or include.",
                    snippet=None,
                )
            )
    return violations
