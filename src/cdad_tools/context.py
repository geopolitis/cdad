from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .schema import TaskPacket


TEXT_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".md",
    ".mjs",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".sql",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}


@dataclass(slots=True)
class ContextItem:
    path: str
    content: str
    estimated_tokens: int
    score: int = 0


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES


def packet_terms(packet: TaskPacket) -> set[str]:
    text = " ".join(
        [
            packet.task_id,
            packet.objective,
            packet.why_now,
            " ".join(packet.constraints),
            " ".join(packet.interfaces_touched),
        ]
    ).lower()
    return {term for term in re.findall(r"[a-z0-9_/-]{3,}", text) if term not in {"the", "and", "for", "with"}}


def searchable_roots(root: Path) -> list[Path]:
    return [path for path in [root / "src", root / "tests", root / "docs/decisions", root / "docs/architecture", root / "docs/specs"] if path.exists()]


def source_terms(text: str) -> set[str]:
    terms = set(re.findall(r"\b(?:class|def|function|const|let|var|type|interface)\s+([A-Za-z_][A-Za-z0-9_]*)", text))
    terms.update(re.findall(r"\b(?:from|import)\s+([A-Za-z_][A-Za-z0-9_./]*)", text))
    return {term.lower().replace("_", "-") for term in terms if len(term) >= 3}


def explicit_context_terms(root: Path, packet: TaskPacket) -> set[str]:
    terms: set[str] = set()
    for entry in packet.relevant_context:
        path = root / entry
        if path.is_file() and is_text_file(path):
            try:
                terms.update(source_terms(path.read_text(encoding="utf-8", errors="replace")[:8000]))
            except OSError:
                continue
    return terms


def score_file(path: Path, terms: set[str], symbol_terms: set[str] | None = None, git_paths: set[str] | None = None) -> int:
    haystack = str(path).lower()
    score = sum(3 for term in terms if term in haystack)
    symbols = symbol_terms or set()
    score += sum(2 for term in symbols if term in haystack.replace("_", "-"))
    if path.parts and "tests" in path.parts:
        score += 2
    if "decision" in haystack or "architecture" in haystack or "spec" in haystack:
        score += 1
    if git_paths and str(path) in git_paths:
        score += 2
    return score


def git_changed_paths(root: Path) -> set[str]:
    git_dir = root / ".git"
    if not git_dir.exists():
        return set()
    try:
        import subprocess

        proc = subprocess.run(["git", "status", "--short"], cwd=root, text=True, capture_output=True, timeout=2)
    except Exception:
        return set()
    paths = set()
    for line in proc.stdout.splitlines():
        if len(line) > 3:
            paths.add(line[3:].strip())
    return paths


def discover_related_context(root: Path, packet: TaskPacket, limit: int = 8) -> list[str]:
    terms = packet_terms(packet)
    symbols = explicit_context_terms(root, packet)
    git_paths = git_changed_paths(root)
    explicit = set(packet.relevant_context + packet.references)
    scored: list[tuple[int, str]] = []
    for base in searchable_roots(root):
        for path in base.rglob("*"):
            if not path.is_file() or not is_text_file(path):
                continue
            relative = str(path.relative_to(root))
            if relative in explicit:
                continue
            if relative.endswith(".goal.md") and relative.replace(".goal.md", ".goal.json") in explicit:
                continue
            if relative.endswith(".goal.json") and relative.replace(".goal.json", ".goal.md") in explicit:
                continue
            score = score_file(path, terms, symbols, git_paths)
            if score <= 0:
                try:
                    sample = path.read_text(encoding="utf-8", errors="replace")[:4000].lower()
                except OSError:
                    continue
                score = sum(1 for term in terms if term in sample) + sum(1 for term in symbols if term in sample.replace("_", "-"))
            if score > 0:
                scored.append((score, relative))
    return [relative for _, relative in sorted(scored, key=lambda item: (-item[0], item[1]))[:limit]]


def collect_context(
    root: Path, packet: TaskPacket, token_budget: int, include_discovered: bool = True
) -> tuple[list[ContextItem], list[str]]:
    items: list[ContextItem] = []
    warnings: list[str] = []
    used = 0
    discovered = discover_related_context(root, packet) if include_discovered else []
    candidates = list(dict.fromkeys(packet.relevant_context + packet.references + discovered))
    for entry in candidates:
        if "://" in entry or entry.startswith("#"):
            warnings.append(f"Skipped non-local reference: {entry}")
            continue
        path = root / entry
        paths = []
        if path.is_file():
            paths = [path]
        elif path.is_dir():
            paths = [p for p in sorted(path.rglob("*")) if p.is_file() and is_text_file(p)]
        else:
            warnings.append(f"Missing context path: {entry}")
            continue
        for candidate in paths:
            if not is_text_file(candidate):
                warnings.append(f"Skipped non-text file: {candidate.relative_to(root)}")
                continue
            content = candidate.read_text(encoding="utf-8", errors="replace")
            cost = estimate_tokens(content)
            score = (
                100
                if str(candidate.relative_to(root)) in packet.relevant_context
                else score_file(candidate, packet_terms(packet), explicit_context_terms(root, packet), git_changed_paths(root))
            )
            if used + cost > token_budget and items:
                warnings.append(f"Budget exhausted before: {candidate.relative_to(root)}")
                continue
            items.append(ContextItem(str(candidate.relative_to(root)), content, cost, score))
            used += cost
    return items, warnings


def render_context_bundle(packet: TaskPacket, items: list[ContextItem], warnings: list[str]) -> str:
    total = sum(item.estimated_tokens for item in items)
    sections = [
        f"# CDAD Context Bundle: {packet.task_id}",
        "",
        f"Objective: {packet.objective}",
        f"Estimated tokens: {total}",
        "",
        "## Included Files",
    ]
    sections.extend(f"- {item.path} ({item.estimated_tokens} tokens est., score {item.score})" for item in items)
    if warnings:
        sections.extend(["", "## Warnings", *[f"- {warning}" for warning in warnings]])
    for item in items:
        sections.extend(
            [
                "",
                f"## {item.path}",
                "```",
                item.content.rstrip(),
                "```",
            ]
        )
    return "\n".join(sections).rstrip() + "\n"
