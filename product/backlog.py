"""Regenerate product/backlog.md from the product backlog directories.

The directories are the single source of truth for backlog state:
    product/ready/       — approved, ready to build
    product/refinement/  — in design / needs a decision
    product/Done/        — shipped
    product/designs/     — mockups & analysis artifacts

This script reads those directories and emits a human-readable index
(backlog.md) plus any drift flags it can detect mechanically. It never
moves files — that is the maintaining-the-backlog skill's job.

Run:  python product/backlog.py
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRODUCT_DIR = PROJECT_ROOT / "product"
OUTPUT_FILE = PRODUCT_DIR / "backlog.md"

STATUS_DIRS = [
    ("Ready", PRODUCT_DIR / "ready"),
    ("Refinement", PRODUCT_DIR / "refinement"),
    ("Done", PRODUCT_DIR / "Done"),
    ("Designs", PRODUCT_DIR / "designs"),
]

STATUS_DESC = {
    "Ready": "approved, ready to build",
    "Refinement": "in design / needs a decision",
    "Done": "shipped",
    "Designs": "mockups & analysis artifacts",
}

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

_BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".ico", ".bmp"}


def extract_title(path: Path) -> str:
    """Best-effort one-line summary for a backlog item."""
    if path.suffix.lower() in _BINARY_SUFFIXES:
        return f"({path.suffix[1:].lower()} asset)"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "(unreadable)"

    if path.suffix.lower() == ".html":
        m = _TITLE_RE.search(text)
        return re.sub(r"\s+", " ", m.group(1)).strip() if m else "(html, no <title>)"

    # First markdown H1 heading.
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("# ") and not s.startswith("## "):
            return s[2:].strip()
    # Fallback: first non-empty, non-heading, non-blockquote line.
    for line in text.splitlines():
        s = line.strip()
        if s and not s.startswith(("#", ">")):
            return s[:100]
    return "(untitled)"


def list_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(
        p for p in directory.iterdir()
        if p.is_file() and not p.name.startswith(".")
    )


def detect_drift(status_dirs):
    """Return drift flags a script can catch without inspecting code."""
    flags = []
    by_basename = {}
    for status, directory, files in status_dirs:
        for f in files:
            by_basename.setdefault(f.name.lower(), []).append((status, directory, f))

    # HTML artifacts living outside designs/.
    for status, directory, files in status_dirs:
        if status == "Designs":
            continue
        for f in files:
            if f.suffix.lower() == ".html":
                flags.append(
                    f"- `product/{directory.name}/{f.name}` looks like a design "
                    f"artifact — consider moving it to `product/designs/`"
                )

    # Same filename in more than one status directory.
    for name, occurrences in sorted(by_basename.items()):
        if len({s for s, _, _ in occurrences}) > 1:
            locs = ", ".join(f"{directory.name}/{f.name}" for _, directory, f in occurrences)
            flags.append(
                f"- `{name}` appears in multiple places ({locs}) — resolve the duplicate"
            )

    return flags


def main() -> None:
    status_dirs = [
        (status, directory, list_files(directory))
        for status, directory in STATUS_DIRS
    ]

    lines = [
        "# River Product Backlog",
        "",
        "> **Auto-generated** — do not edit by hand. The directories are the "
        "source of truth.",
        "> Regenerate with: `python product/backlog.py`",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    for status, directory, files in status_dirs:
        lines.append(f"## {status} — {STATUS_DESC[status]} ({len(files)})")
        lines.append("")
        if not files:
            lines.append("_None._")
            lines.append("")
            continue
        lines.append("| File | Summary |")
        lines.append("|------|---------|")
        for f in files:
            title = extract_title(f).replace("|", "\\|")
            lines.append(f"| `{f.name}` | {title} |")
        lines.append("")

    lines.append("## Drift Flags")
    lines.append("")
    flags = detect_drift(status_dirs)
    if not flags:
        lines.append("_None detected._")
    else:
        lines.extend(flags)
    lines.append("")

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Backlog index '{OUTPUT_FILE.relative_to(PROJECT_ROOT)}' generated "
        f"({len(flags)} drift flag(s))."
    )


if __name__ == "__main__":
    main()
