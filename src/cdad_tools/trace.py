from __future__ import annotations

from pathlib import Path
import json
import re

from .schema import load_packet


def progress_entries(progress: str, task_id: str) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    pattern = re.compile(rf"^##\s+([^\n]+)\s+{re.escape(task_id)}\n(.*?)(?=^##\s+|\Z)", re.MULTILINE | re.DOTALL)
    for match in pattern.finditer(progress):
        body = match.group(2)
        changed_files: list[str] = []
        result = ""
        verification = ""
        next_step = ""
        for line in body.splitlines():
            if line.startswith("- Files changed:"):
                value = line.split(":", 1)[1].strip()
                changed_files = [] if value == "None recorded" else [item.strip() for item in value.split(",") if item.strip()]
            elif line.startswith("- Result:"):
                result = line.split(":", 1)[1].strip()
            elif line.startswith("- Verification run:"):
                verification = line.split(":", 1)[1].strip()
            elif line.startswith("- Next recommended step:"):
                next_step = line.split(":", 1)[1].strip()
        entries.append(
            {
                "timestamp": match.group(1).strip(),
                "changed_files": changed_files,
                "verification": verification,
                "result": result,
                "next_step": next_step,
            }
        )
    return entries


def validation_reports(root: Path, task_id: str) -> list[str]:
    reports = sorted((root / "agent/reports").glob(f"{task_id}-*.json"))
    return [str(path.relative_to(root)) for path in reports]


def build_trace(root: Path) -> dict[str, object]:
    progress_path = root / "agent/progress/progress.md"
    progress = progress_path.read_text(encoding="utf-8", errors="replace") if progress_path.exists() else ""
    rows = []
    for path in sorted((root / "agent/packets").glob("*.json")):
        packet = load_packet(path)
        evidence = sorted((root / "agent/verification").glob(f"{packet.task_id}-*"))
        entries = progress_entries(progress, packet.task_id)
        rows.append(
            {
                "goal_id": packet.goal_id or None,
                "task_id": packet.task_id,
                "status": packet.status.value,
                "depends_on": packet.depends_on,
                "references": packet.references,
                "evidence": [str(item.relative_to(root)) for item in evidence],
                "validation_reports": validation_reports(root, packet.task_id),
                "progress_entries": entries,
                "changed_files": sorted({file for entry in entries for file in entry["changed_files"]}),
                "has_progress": bool(entries),
            }
        )
    return {"schema": "cdad.trace.v1", "packets": rows}


def render_trace_json(root: Path) -> str:
    return json.dumps(build_trace(root), indent=2) + "\n"


def render_trace_markdown(root: Path) -> str:
    trace = build_trace(root)
    rows = trace["packets"]
    if not rows:
        return "no packets found\n"
    lines = [
        "| Goal | Packet | Status | Depends On | References | Evidence | Progress |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        refs = ", ".join(row["references"]) if row["references"] else "None"
        deps = ", ".join(row["depends_on"]) if row["depends_on"] else "None"
        ev = ", ".join(row["evidence"]) if row["evidence"] else "None"
        progress = "yes" if row["has_progress"] else "no"
        lines.append(f"| {row['goal_id'] or 'None'} | {row['task_id']} | {row['status']} | {deps} | {refs} | {ev} | {progress} |")
    return "\n".join(lines) + "\n"
