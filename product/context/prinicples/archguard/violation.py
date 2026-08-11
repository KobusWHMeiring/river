from dataclasses import dataclass


@dataclass
class Violation:
    rule_id: str
    severity: str  # "ERROR" | "WARNING"
    category: str  # "python" | "template" | "css" | "js"
    file: str  # relative path from project root
    line: int  # 0 if file-level or unknown
    message: str
    snippet: str | None = None
