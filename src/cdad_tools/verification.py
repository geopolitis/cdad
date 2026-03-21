from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess

from .schema import TaskPacket, VerificationKind


@dataclass(slots=True)
class VerificationRun:
    command: str
    kind: VerificationKind
    returncode: int
    stdout: str
    stderr: str


def runnable_commands(packet: TaskPacket) -> list[str]:
    return [item.command for item in packet.verification if item.command]


def classify_command(command: str) -> VerificationKind:
    lower = command.lower()
    if "lint" in lower or "ruff" in lower or "eslint" in lower:
        return VerificationKind.LINT
    if "typecheck" in lower or "tsc" in lower or "mypy" in lower:
        return VerificationKind.TYPECHECK
    if "build" in lower:
        return VerificationKind.BUILD
    if "e2e" in lower or "playwright" in lower or "cypress" in lower:
        return VerificationKind.E2E
    if "test" in lower or "unittest" in lower or "pytest" in lower or "vitest" in lower or "jest" in lower:
        return VerificationKind.UNIT
    return VerificationKind.MANUAL


def detect_verification_commands(root: Path) -> list[tuple[VerificationKind, str]]:
    commands: list[tuple[VerificationKind, str]] = []
    package_json = root / "package.json"
    if package_json.exists():
        try:
            scripts = json.loads(package_json.read_text(encoding="utf-8")).get("scripts", {})
        except json.JSONDecodeError:
            scripts = {}
        if "lint" in scripts:
            commands.append((VerificationKind.LINT, "npm run lint"))
        if "typecheck" in scripts:
            commands.append((VerificationKind.TYPECHECK, "npm run typecheck"))
        if "test" in scripts:
            commands.append((VerificationKind.UNIT, "npm test"))
        if "build" in scripts:
            commands.append((VerificationKind.BUILD, "npm run build"))
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="replace")
        if 'where = ["src"]' in content or "where = ['src']" in content:
            commands.append((VerificationKind.UNIT, "PYTHONPATH=src python3 -m unittest discover -s tests -v"))
        else:
            commands.append((VerificationKind.UNIT, "python3 -m unittest discover -s tests -v"))
    if (root / "go.mod").exists():
        commands.append((VerificationKind.UNIT, "go test ./..."))
    if (root / "Cargo.toml").exists():
        commands.append((VerificationKind.UNIT, "cargo test"))
    return commands


def run_packet_verification(root: Path, packet: TaskPacket, timeout: int = 600) -> tuple[list[VerificationRun], str]:
    runs: list[VerificationRun] = []
    for item in packet.verification:
        if not item.command:
            continue
        proc = subprocess.run(  # nosec B602
            item.command,
            cwd=root,
            shell=True,  # nosec B602
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        runs.append(VerificationRun(item.command, item.kind or classify_command(item.command), proc.returncode, proc.stdout, proc.stderr))
    return runs, render_verification_log(packet, runs)


def render_verification_log(packet: TaskPacket, runs: list[VerificationRun]) -> str:
    lines = [
        f"# Verification: {packet.task_id}",
        "",
        f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
        f"Objective: {packet.objective}",
        "",
    ]
    if not runs:
        lines.append("No runnable command verification entries were found.")
    for run in runs:
        lines.extend(
            [
                f"## `{run.command}`",
                f"Kind: {run.kind.value}",
                f"Return code: {run.returncode}",
                "",
                "### stdout",
                "```",
                run.stdout.rstrip(),
                "```",
                "",
                "### stderr",
                "```",
                run.stderr.rstrip(),
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"
