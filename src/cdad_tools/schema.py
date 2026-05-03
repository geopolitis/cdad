from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any
import json


class PacketStatus(StrEnum):
    DRAFT = "Draft"
    READY = "Ready"
    IN_PROGRESS = "InProgress"
    PASSED = "Passed"
    BLOCKED = "Blocked"
    NEEDS_APPROVAL = "NeedsApproval"
    AMBIGUOUS = "Ambiguous"


class VerificationKind(StrEnum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    VISUAL = "visual"
    SECURITY = "security"
    POLICY = "policy"
    EVIDENCE = "evidence"
    MANUAL = "manual"
    LINT = "lint"
    TYPECHECK = "typecheck"
    BUILD = "build"


class ValidationSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


APPROVAL_TRIGGERS = (
    "dependency",
    "external network",
    "schema",
    "contract",
    "security boundary",
    "destructive",
    "delete",
    "widen scope",
)


@dataclass(slots=True)
class Verification:
    kind: VerificationKind
    command: str = ""
    scenario: str = ""
    evidence_path: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Verification":
        return cls(
            kind=VerificationKind(data.get("kind", VerificationKind.MANUAL)),
            command=str(data.get("command", "")).strip(),
            scenario=str(data.get("scenario", "")).strip(),
            evidence_path=str(data.get("evidence_path", "")).strip(),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "kind": self.kind.value,
            "command": self.command,
            "scenario": self.scenario,
            "evidence_path": self.evidence_path,
        }


@dataclass(slots=True)
class TaskPacket:
    task_id: str
    objective: str
    why_now: str
    goal_id: str = ""
    relevant_context: list[str] = field(default_factory=list)
    interfaces_touched: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    verification: list[Verification] = field(default_factory=list)
    escalation_conditions: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    priority: int = 3
    risk: int = 3
    value: int = 3
    progress_snapshot: str = ""
    status: PacketStatus = PacketStatus.DRAFT
    owner: str = "lead-agent"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskPacket":
        return cls(
            task_id=str(data.get("task_id", "")).strip(),
            objective=str(data.get("objective", "")).strip(),
            why_now=str(data.get("why_now", "")).strip(),
            goal_id=str(data.get("goal_id", "")).strip(),
            relevant_context=[str(x).strip() for x in data.get("relevant_context", []) if str(x).strip()],
            interfaces_touched=[str(x).strip() for x in data.get("interfaces_touched", []) if str(x).strip()],
            constraints=[str(x).strip() for x in data.get("constraints", []) if str(x).strip()],
            verification=[Verification.from_dict(x) for x in data.get("verification", [])],
            escalation_conditions=[str(x).strip() for x in data.get("escalation_conditions", []) if str(x).strip()],
            references=[str(x).strip() for x in data.get("references", []) if str(x).strip()],
            depends_on=[str(x).strip() for x in data.get("depends_on", []) if str(x).strip()],
            priority=int(data.get("priority", 3)),
            risk=int(data.get("risk", 3)),
            value=int(data.get("value", 3)),
            progress_snapshot=str(data.get("progress_snapshot", "")).strip(),
            status=PacketStatus(data.get("status", PacketStatus.DRAFT)),
            owner=str(data.get("owner", "lead-agent")).strip() or "lead-agent",
            created_at=str(data.get("created_at", "")).strip() or datetime.now(timezone.utc).isoformat(),
            updated_at=str(data.get("updated_at", "")).strip() or datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "cdad.task_packet.v1",
            "task_id": self.task_id,
            "objective": self.objective,
            "why_now": self.why_now,
            "goal_id": self.goal_id,
            "relevant_context": self.relevant_context,
            "interfaces_touched": self.interfaces_touched,
            "constraints": self.constraints,
            "verification": [v.to_dict() for v in self.verification],
            "escalation_conditions": self.escalation_conditions,
            "references": self.references,
            "depends_on": self.depends_on,
            "priority": self.priority,
            "risk": self.risk,
            "value": self.value,
            "progress_snapshot": self.progress_snapshot,
            "status": self.status.value,
            "owner": self.owner,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def load_packet(path: Path) -> TaskPacket:
    with path.open("r", encoding="utf-8") as handle:
        return TaskPacket.from_dict(json.load(handle))


def save_packet(packet: TaskPacket, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    packet.updated_at = datetime.now(timezone.utc).isoformat()
    with path.open("w", encoding="utf-8") as handle:
        json.dump(packet.to_dict(), handle, indent=2)
        handle.write("\n")


@dataclass(slots=True)
class GoalRecord:
    goal_id: str
    objective: str
    scope_in: list[str] = field(default_factory=list)
    scope_out: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    verification: list[Verification] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    approval_boundaries: list[str] = field(default_factory=list)
    quality_bar: str = ""
    owner: str = "human-lead"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GoalRecord":
        return cls(
            goal_id=str(data.get("goal_id", "")).strip(),
            objective=str(data.get("objective", "")).strip(),
            scope_in=[str(x).strip() for x in data.get("scope_in", []) if str(x).strip()],
            scope_out=[str(x).strip() for x in data.get("scope_out", []) if str(x).strip()],
            constraints=[str(x).strip() for x in data.get("constraints", []) if str(x).strip()],
            verification=[Verification.from_dict(x) for x in data.get("verification", [])],
            risks=[str(x).strip() for x in data.get("risks", []) if str(x).strip()],
            approval_boundaries=[str(x).strip() for x in data.get("approval_boundaries", []) if str(x).strip()],
            quality_bar=str(data.get("quality_bar", "")).strip(),
            owner=str(data.get("owner", "human-lead")).strip() or "human-lead",
            created_at=str(data.get("created_at", "")).strip() or datetime.now(timezone.utc).isoformat(),
            updated_at=str(data.get("updated_at", "")).strip() or datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "cdad.goal_record.v1",
            "goal_id": self.goal_id,
            "objective": self.objective,
            "scope_in": self.scope_in,
            "scope_out": self.scope_out,
            "constraints": self.constraints,
            "verification": [v.to_dict() for v in self.verification],
            "risks": self.risks,
            "approval_boundaries": self.approval_boundaries,
            "quality_bar": self.quality_bar,
            "owner": self.owner,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def load_goal(path: Path) -> GoalRecord:
    with path.open("r", encoding="utf-8") as handle:
        return GoalRecord.from_dict(json.load(handle))


def save_goal(goal: GoalRecord, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    goal.updated_at = datetime.now(timezone.utc).isoformat()
    with path.open("w", encoding="utf-8") as handle:
        json.dump(goal.to_dict(), handle, indent=2)
        handle.write("\n")


def render_packet_markdown(packet: TaskPacket) -> str:
    def bullets(items: list[str], empty: str = "TBD") -> str:
        return "\n".join(f"- {item}" for item in items) if items else f"- {empty}"

    verification = []
    for item in packet.verification:
        detail = item.command or item.scenario or item.evidence_path or "TBD"
        verification.append(f"- [{item.kind.value}] {detail}")

    return f"""# Task Packet: {packet.task_id}

Status: {packet.status.value}
Owner: {packet.owner}
Goal: {packet.goal_id or "TBD"}

## Objective
{packet.objective or "TBD"}

## Why this step
{packet.why_now or "TBD"}

## Relevant context
{bullets(packet.relevant_context)}

## Interfaces / contracts touched
{bullets(packet.interfaces_touched)}

## Constraints
{bullets(packet.constraints)}

## Verification
{chr(10).join(verification) if verification else "- TBD"}

## Escalate if
{bullets(packet.escalation_conditions)}

## References
{bullets(packet.references)}

## Depends on
{bullets(packet.depends_on, "None")}

## Progress snapshot
{packet.progress_snapshot or "TBD"}
"""


def render_goal_markdown(goal: GoalRecord) -> str:
    def bullets(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items) if items else "- TBD"

    verification = []
    for item in goal.verification:
        detail = item.command or item.scenario or item.evidence_path or "TBD"
        verification.append(f"- [{item.kind.value}] {detail}")

    return f"""# Goal Record: {goal.goal_id}

Owner: {goal.owner}

## Objective
{goal.objective or "TBD"}

## Scope In
{bullets(goal.scope_in)}

## Scope Out
{bullets(goal.scope_out)}

## Constraints
{bullets(goal.constraints)}

## Quality Bar
{goal.quality_bar or "TBD"}

## Verification
{chr(10).join(verification) if verification else "- TBD"}

## Risks
{bullets(goal.risks)}

## Approval Boundaries
{bullets(goal.approval_boundaries)}
"""


def validate_packet(packet: TaskPacket, project_root: Path | None = None) -> list[str]:
    issues: list[str] = []
    if not packet.task_id:
        issues.append("task_id is required")
    if not packet.objective:
        issues.append("objective is required")
    if not packet.why_now:
        issues.append("why_now is required")
    if not packet.relevant_context:
        issues.append("at least one relevant_context entry is required")
    if not packet.constraints:
        issues.append("at least one constraint is required")
    if not packet.verification:
        issues.append("at least one verification entry is required")
    for index, verification in enumerate(packet.verification, start=1):
        if not (verification.command or verification.scenario or verification.evidence_path):
            issues.append(f"verification[{index}] needs command, scenario, or evidence_path")
    if not packet.escalation_conditions:
        issues.append("at least one escalation condition is required")
    if packet.priority < 1 or packet.priority > 5:
        issues.append("priority must be between 1 and 5")
    if packet.risk < 1 or packet.risk > 5:
        issues.append("risk must be between 1 and 5")
    if packet.value < 1 or packet.value > 5:
        issues.append("value must be between 1 and 5")
    if packet.status == PacketStatus.PASSED:
        if not any(v.evidence_path for v in packet.verification):
            issues.append("Passed packets should reference verification evidence")
    lowered = " ".join(packet.escalation_conditions).lower()
    missing = [trigger for trigger in APPROVAL_TRIGGERS if trigger not in lowered]
    if len(missing) == len(APPROVAL_TRIGGERS):
        issues.append("escalation_conditions should include at least one explicit approval boundary")
    if project_root is not None:
        for entry in packet.relevant_context:
            if "://" in entry or entry.startswith("#"):
                continue
            if not (project_root / entry).exists():
                issues.append(f"relevant_context path does not exist: {entry}")
    return issues


def validate_goal(goal: GoalRecord) -> list[str]:
    issues: list[str] = []
    if not goal.goal_id:
        issues.append("goal_id is required")
    if not goal.objective:
        issues.append("objective is required")
    if not goal.scope_in:
        issues.append("scope_in is required")
    if not goal.scope_out:
        issues.append("scope_out is required")
    if not goal.constraints:
        issues.append("constraints are required")
    if not goal.verification:
        issues.append("verification is required")
    for index, verification in enumerate(goal.verification, start=1):
        if not (verification.command or verification.scenario or verification.evidence_path):
            issues.append(f"verification[{index}] needs command, scenario, or evidence_path")
    if not goal.risks:
        issues.append("risks are required")
    if not goal.approval_boundaries:
        issues.append("approval_boundaries are required")
    if not goal.quality_bar:
        issues.append("quality_bar is required")
    lowered = " ".join(goal.approval_boundaries).lower()
    if not any(trigger in lowered for trigger in APPROVAL_TRIGGERS):
        issues.append("approval_boundaries should include at least one explicit approval trigger")
    return issues
