"""Deterministic canonical-card parser (Book I / Bloc I.3).

Template-scoped parser for the known canonical card Markdown format:
an H1 title line, a front-matter block of `key: value` lines, and `## Section`
bodies (with `Beginner:/Operator:/Researcher:/Forbidden:` Ask-CEREBUS lines).

No LLM parsing, no prose inference, no arbitrary-path acceptance, no remote
fetch. A card that violates the template yields explicit parse results the
canonicalizer quarantines — it is never "AI repaired".
"""
from __future__ import annotations

from dataclasses import dataclass, field

_CARD_KIND_PREFIXES = ("MODEL CARD", "EVIDENCE CARD", "SETUP CARD")
_ASK_KEYS = ("Beginner:", "Operator:", "Researcher:", "Researcher Notes:", "Forbidden:")


@dataclass(frozen=True)
class ParsedCard:
    """Deterministic parse of one canonical card file."""

    path: str
    kind: str  # MODEL CARD | EVIDENCE CARD | SETUP CARD | UNKNOWN
    title: str
    fields: dict[str, str] = field(default_factory=dict)
    sections: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def section(self, name: str) -> tuple[str, ...]:
        return self.sections.get(name, ())

    def section_text(self, name: str) -> str:
        return "\n".join(self.section(name)).strip()

    def ask_line(self, key: str) -> str:
        """Extract a `Key:` line from the Ask CEREBUS section."""
        prefix = key.strip().rstrip(":") + ":"
        for line in self.section("Ask CEREBUS"):
            stripped = line.strip()
            if stripped.startswith(prefix):
                return stripped[len(prefix):].strip()
        return ""


def parse_card(path: str, text: str) -> ParsedCard:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    kind = "UNKNOWN"
    title = ""
    for line in lines:
        if line.startswith("# "):
            header = line[2:].strip()
            for prefix in _CARD_KIND_PREFIXES:
                if header.startswith(prefix):
                    kind = prefix
                    title = header[len(prefix):].lstrip(" —-:").strip()
                    break
            if kind == "UNKNOWN":
                title = header
            break

    fields: dict[str, str] = {}
    sections: dict[str, list[str]] = {}
    current_section: str | None = None
    front_matter_done = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            current_section = stripped[3:].strip()
            sections.setdefault(current_section, [])
            front_matter_done = True
            continue
        if current_section is not None:
            sections[current_section].append(line)
            continue
        if not stripped or stripped.startswith("#"):
            continue
        if not front_matter_done and ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            if key and " " not in key:
                fields[key] = value.strip()

    return ParsedCard(
        path=path,
        kind=kind,
        title=title,
        fields=fields,
        sections={name: tuple(body) for name, body in sections.items()},
    )


def split_csv(value: str) -> tuple[str, ...]:
    """Deterministic comma-split for market_scope-style fields."""
    return tuple(part.strip() for part in value.split(",") if part.strip())
