"""Audit .md writer for architecture guard."""
from datetime import datetime
from pathlib import Path

from .violation import Violation

OUTPUT_DIR = Path("docs/audits")


def write_audit(slug: str, violations: list[Violation], skipped: list[str]) -> Path:
    """Write violations to docs/audits/<slug>.md. Returns the output path."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{slug}.md"

    errors = [v for v in violations if v.severity == "ERROR"]
    warnings = [v for v in violations if v.severity == "WARNING"]

    if errors:
        verdict = f"❌ {len(errors)} ERRORS, {len(warnings)} WARNINGS — Phase not clean"
    elif warnings:
        verdict = f"⚠️ 0 ERRORS, {len(warnings)} WARNINGS — Review before proceeding"
    else:
        verdict = "✅ CLEAN"

    lines = [
        "# Architecture Guard Audit",
        "",
        f"**Phase:** {slug}",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "**Project:** Homtini — Project Mycelium",
        f"**Verdict:** {verdict}",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Tier | Count |",
        "|------|-------|",
        f"| Errors | {len(errors)} |",
        f"| Warnings | {len(warnings)} |",
        "",
    ]

    if errors:
        lines.append("## Errors")
        lines.append("")
        for v in sorted(errors, key=lambda x: x.rule_id):
            lines.append(f"### {v.rule_id}: {v.message}")
            lines.append(f"**File:** `{v.file}` (line {v.line})")
            if v.snippet:
                lines.append("```python")
                lines.append(v.snippet[:200])
                lines.append("```")
            lines.append("")

    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for v in sorted(warnings, key=lambda x: x.rule_id):
            lines.append(f"### {v.rule_id}: {v.message}")
            lines.append(f"**File:** `{v.file}` (line {v.line})")
            if v.snippet:
                lines.append("```")
                lines.append(v.snippet[:200])
                lines.append("```")
            lines.append("")

    lines.append("## Skipped Directories")
    lines.append("")
    for s in skipped:
        lines.append(f"- `{s}/`")
    lines.append("")
    lines.append("## Suppressions")
    lines.append("")
    lines.append("None.")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
