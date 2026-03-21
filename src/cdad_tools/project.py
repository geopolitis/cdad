from __future__ import annotations

from pathlib import Path


DEFAULT_DIRS = (
    "docs/architecture",
    "docs/decisions",
    "docs/specs",
    "agent/memory",
    "agent/packets",
    "agent/progress",
    "agent/verification",
    "agent/reports",
    "agent/integrations",
    "agent/benchmarks",
)


MEMORY_TEMPLATE = """# CDAD Project Memory

## Stable Rules
- Keep durable intent outside transient chat.
- Use task packets as the runtime unit of work.
- Every packet needs explicit verification.
- Escalate changes to dependencies, contracts, schemas, security boundaries, destructive operations, or widened scope.

## Environment Commands
- Add project-specific test, lint, build, and run commands here.
"""


def init_project(root: Path) -> list[Path]:
    from .config import write_default_config

    created: list[Path] = []
    for relative in DEFAULT_DIRS:
        path = root / relative
        path.mkdir(parents=True, exist_ok=True)
        created.append(path)
    memory = root / "agent/memory/project.md"
    if not memory.exists():
        memory.write_text(MEMORY_TEMPLATE, encoding="utf-8")
        created.append(memory)
    progress = root / "agent/progress/progress.md"
    if not progress.exists():
        progress.write_text("# CDAD Progress Log\n\n", encoding="utf-8")
        created.append(progress)
    config = root / "cdad.config.json"
    existed = config.exists()
    write_default_config(root)
    if not existed:
        created.append(config)
    return created


def packet_path(root: Path, task_id: str) -> Path:
    return root / "agent" / "packets" / f"{task_id}.json"


def packet_markdown_path(root: Path, task_id: str) -> Path:
    return root / "agent" / "packets" / f"{task_id}.md"


def evidence_path(root: Path, task_id: str, suffix: str) -> Path:
    return root / "agent" / "verification" / f"{task_id}-{suffix}"


def goal_path(root: Path, goal_id: str) -> Path:
    return root / "docs" / "specs" / f"{goal_id}.goal.json"


def goal_markdown_path(root: Path, goal_id: str) -> Path:
    return root / "docs" / "specs" / f"{goal_id}.goal.md"


def report_path(root: Path, name: str) -> Path:
    return root / "agent" / "reports" / name
