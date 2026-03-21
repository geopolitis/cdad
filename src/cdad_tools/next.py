from __future__ import annotations

from pathlib import Path

from .schema import PacketStatus, TaskPacket, load_packet


OPEN_STATUSES = {PacketStatus.DRAFT, PacketStatus.READY, PacketStatus.AMBIGUOUS, PacketStatus.BLOCKED}


def load_packets(root: Path) -> list[TaskPacket]:
    return [load_packet(path) for path in sorted((root / "agent/packets").glob("*.json"))]


def completed_ids(packets: list[TaskPacket]) -> set[str]:
    return {packet.task_id for packet in packets if packet.status == PacketStatus.PASSED}


def is_unblocked(packet: TaskPacket, done: set[str]) -> bool:
    return all(dep in done for dep in packet.depends_on)


def next_packet(packets: list[TaskPacket], heuristic: str) -> TaskPacket | None:
    done = completed_ids(packets)
    candidates = [packet for packet in packets if packet.status in OPEN_STATUSES and is_unblocked(packet, done)]
    if not candidates:
        return None
    if heuristic == "risk-first":
        return sorted(candidates, key=lambda p: (-p.risk, p.priority, p.task_id))[0]
    if heuristic == "value-first":
        return sorted(candidates, key=lambda p: (-p.value, p.priority, p.task_id))[0]
    return sorted(candidates, key=lambda p: (len(p.depends_on), p.priority, -p.risk, p.task_id))[0]


def blocked_packets(packets: list[TaskPacket]) -> list[TaskPacket]:
    done = completed_ids(packets)
    return [packet for packet in packets if packet.status in OPEN_STATUSES and not is_unblocked(packet, done)]


def packet_rank_reason(packet: TaskPacket, heuristic: str) -> str:
    if heuristic == "risk-first":
        return f"risk={packet.risk}, priority={packet.priority}"
    if heuristic == "value-first":
        return f"value={packet.value}, priority={packet.priority}"
    return f"dependencies={len(packet.depends_on)}, priority={packet.priority}, risk={packet.risk}"


def packet_to_summary(packet: TaskPacket, heuristic: str) -> dict[str, object]:
    return {
        "task_id": packet.task_id,
        "goal_id": packet.goal_id or None,
        "status": packet.status.value,
        "priority": packet.priority,
        "risk": packet.risk,
        "value": packet.value,
        "depends_on": packet.depends_on,
        "rank_reason": packet_rank_reason(packet, heuristic),
    }
