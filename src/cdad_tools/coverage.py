from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .schema import load_goal, load_packet


@dataclass(slots=True)
class CoverageFinding:
    severity: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"severity": self.severity, "code": self.code, "message": self.message}


def analyze_goal_coverage(root: Path) -> list[CoverageFinding]:
    findings: list[CoverageFinding] = []
    goals = [load_goal(path) for path in sorted((root / "docs/specs").glob("*.goal.json"))]
    packets = [load_packet(path) for path in sorted((root / "agent/packets").glob("*.json"))]
    goal_ids = {goal.goal_id for goal in goals}
    packets_by_goal: dict[str, list[str]] = {goal.goal_id: [] for goal in goals}
    for packet in packets:
        if not packet.goal_id:
            findings.append(CoverageFinding("error", "packet_missing_goal", f"Packet {packet.task_id} is not linked to a goal."))
            continue
        if packet.goal_id not in goal_ids:
            findings.append(CoverageFinding("error", "packet_unknown_goal", f"Packet {packet.task_id} links to missing goal {packet.goal_id}."))
            continue
        packets_by_goal.setdefault(packet.goal_id, []).append(packet.task_id)
    for goal in goals:
        linked = packets_by_goal.get(goal.goal_id, [])
        if not linked:
            findings.append(CoverageFinding("error", "goal_without_packets", f"Goal {goal.goal_id} has no linked packets."))
        if goal.scope_in and len(linked) < min(2, len(goal.scope_in)):
            findings.append(CoverageFinding("warning", "thin_goal_packet_coverage", f"Goal {goal.goal_id} has {len(linked)} packet(s) for {len(goal.scope_in)} scope-in item(s)."))
    return findings


def render_coverage_report(root: Path) -> str:
    findings = analyze_goal_coverage(root)
    goals = [load_goal(path) for path in sorted((root / "docs/specs").glob("*.goal.json"))]
    packets = [load_packet(path) for path in sorted((root / "agent/packets").glob("*.json"))]
    details = []
    for goal in goals:
        linked = [packet.task_id for packet in packets if packet.goal_id == goal.goal_id]
        details.append(
            {
                "goal_id": goal.goal_id,
                "scope_in_count": len(goal.scope_in),
                "linked_packets": linked,
                "linked_packet_count": len(linked),
            }
        )
    status = "failed" if any(f.severity == "error" for f in findings) else "passed"
    return json.dumps(
        {
            "schema": "cdad.goal_coverage_report.v1",
            "status": status,
            "goals": details,
            "findings": [finding.to_dict() for finding in findings],
        },
        indent=2,
    ) + "\n"
