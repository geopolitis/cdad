from __future__ import annotations

from pathlib import Path


SUPPORTED_AGENTS = ("codex", "claude-code", "cursor", "github-copilot")


TEMPLATE = """# CDAD Agent Command

Use CDAD artifacts as the operating boundary for this task.

1. Read `agent/memory/project.md`.
2. Read the selected packet under `agent/packets/`.
3. Run `cdad validate --strict-paths` before implementation.
4. Build a compact context bundle with `cdad context <TASK_ID>`.
5. Implement only the packet objective.
6. Run `cdad verify <TASK_ID>`.
7. Append progress with `cdad progress add <TASK_ID> ...`.
8. Escalate dependency, schema, contract, security, destructive, or scope-widening changes.

Do not treat this command as a giant prompt. The packet is the runtime source.
"""


def template_for(agent: str) -> str:
    return f"""---
agent: {agent}
schema: cdad.integration_template.v1
---

{TEMPLATE}"""


def integration_target(root: Path, agent: str) -> Path:
    if agent == "codex":
        return root / "agent/integrations/codex-cdad.md"
    if agent == "claude-code":
        return root / ".claude/commands/cdad.md"
    if agent == "cursor":
        return root / ".cursor/commands/cdad.md"
    if agent == "github-copilot":
        return root / ".github/prompts/cdad.prompt.md"
    raise ValueError(f"unsupported agent: {agent}")


def generate_integration(root: Path, agent: str, force: bool = False) -> Path:
    if agent not in SUPPORTED_AGENTS:
        raise ValueError(f"unsupported agent: {agent}")
    target = integration_target(root, agent)
    if target.exists() and not force:
        raise FileExistsError(str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(template_for(agent), encoding="utf-8")
    return target


def generate_all_integrations(root: Path, force: bool = False) -> list[Path]:
    return [generate_integration(root, agent, force) for agent in SUPPORTED_AGENTS]
