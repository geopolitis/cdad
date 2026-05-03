from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json


DEFAULT_CONFIG = {
    "schema": "cdad.config.v1",
    "context_token_budget": 8000,
    "approval_triggers": [
        "dependency",
        "schema",
        "contract",
        "security",
        "destructive",
        "scope",
    ],
    "ci": {
        "min_verification_pass_rate": 0.0,
        "max_rework_mentions": 0,
        "require_goal_coverage": True,
        "require_design_reports": False,
    },
}


@dataclass(slots=True)
class CdadConfig:
    context_token_budget: int = 8000
    approval_triggers: list[str] = field(default_factory=lambda: list(DEFAULT_CONFIG["approval_triggers"]))
    min_verification_pass_rate: float = 0.0
    max_rework_mentions: int = 0
    require_goal_coverage: bool = True
    require_design_reports: bool = False


def config_path(root: Path) -> Path:
    return root / "cdad.config.json"


def write_default_config(root: Path) -> Path:
    path = config_path(root)
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n", encoding="utf-8")
    return path


def load_config(root: Path) -> CdadConfig:
    path = config_path(root)
    data: dict[str, Any] = DEFAULT_CONFIG
    if path.exists():
        loaded = json.loads(path.read_text(encoding="utf-8"))
        data = {**DEFAULT_CONFIG, **loaded}
        data["ci"] = {**DEFAULT_CONFIG["ci"], **loaded.get("ci", {})}
    ci = data.get("ci", {})
    return CdadConfig(
        context_token_budget=int(data.get("context_token_budget", 8000)),
        approval_triggers=[str(x) for x in data.get("approval_triggers", DEFAULT_CONFIG["approval_triggers"])],
        min_verification_pass_rate=float(ci.get("min_verification_pass_rate", 0.0)),
        max_rework_mentions=int(ci.get("max_rework_mentions", 0)),
        require_goal_coverage=bool(ci.get("require_goal_coverage", True)),
        require_design_reports=bool(ci.get("require_design_reports", False)),
    )
