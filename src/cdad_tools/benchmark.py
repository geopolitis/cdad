from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import re

from .context import estimate_tokens
from .schema import PacketStatus, load_packet


@dataclass(slots=True)
class BenchmarkMetrics:
    packets_total: int
    packets_passed: int
    verification_pass_rate: float
    context_bundle_tokens: int
    verification_records: int
    progress_entries: int
    rework_mentions: int
    avg_time_to_verified_seconds: float

    def to_dict(self) -> dict[str, int | float]:
        return {
            "packets_total": self.packets_total,
            "packets_passed": self.packets_passed,
            "verification_pass_rate": self.verification_pass_rate,
            "context_bundle_tokens": self.context_bundle_tokens,
            "verification_records": self.verification_records,
            "progress_entries": self.progress_entries,
            "rework_mentions": self.rework_mentions,
            "avg_time_to_verified_seconds": self.avg_time_to_verified_seconds,
        }


def count_progress_entries(progress_text: str) -> int:
    return len(re.findall(r"^##\s+", progress_text, flags=re.MULTILINE))


def verification_timestamp(path: Path) -> datetime | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^Timestamp:\s+(.+?)\s*$", text, flags=re.MULTILINE)
    if not match:
        return None
    try:
        return datetime.fromisoformat(match.group(1))
    except ValueError:
        return None


def collect_benchmark_metrics(root: Path) -> BenchmarkMetrics:
    packet_paths = sorted((root / "agent/packets").glob("*.json"))
    packets = [load_packet(path) for path in packet_paths]
    passed = [packet for packet in packets if packet.status == PacketStatus.PASSED]
    verification_paths = sorted((root / "agent/verification").glob("*verification.md"))
    context_paths = sorted((root / "agent/verification").glob("*context.md"))
    context_tokens = 0
    for path in context_paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"^Estimated tokens:\s+(\d+)\s*$", text, flags=re.MULTILINE)
        context_tokens += int(match.group(1)) if match else estimate_tokens(text)
    progress_path = root / "agent/progress/progress.md"
    progress_text = progress_path.read_text(encoding="utf-8", errors="replace") if progress_path.exists() else ""
    total = len(packets)
    durations = []
    for packet in passed:
        try:
            start = datetime.fromisoformat(packet.created_at)
            evidence_times = [
                ts
                for item in packet.verification
                for ts in [verification_timestamp(root / item.evidence_path) if item.evidence_path else None]
                if ts is not None
            ]
            end = min(evidence_times) if evidence_times else datetime.fromisoformat(packet.updated_at)
            durations.append(max(0.0, (end - start).total_seconds()))
        except ValueError:
            continue
    return BenchmarkMetrics(
        packets_total=total,
        packets_passed=len(passed),
        verification_pass_rate=(len(passed) / total) if total else 0.0,
        context_bundle_tokens=context_tokens,
        verification_records=len(verification_paths),
        progress_entries=count_progress_entries(progress_text),
        rework_mentions=len(re.findall(r"\b(rework|reopen|regression|failed)\b", progress_text, flags=re.IGNORECASE)),
        avg_time_to_verified_seconds=(sum(durations) / len(durations)) if durations else 0.0,
    )


def render_benchmark_report(root: Path) -> str:
    metrics = collect_benchmark_metrics(root)
    return json.dumps(
        {
            "schema": "cdad.benchmark_report.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics.to_dict(),
        },
        indent=2,
    ) + "\n"
