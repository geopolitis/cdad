from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import re

from .context import estimate_tokens


def scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value)
    if not text:
        return '""'
    if any(ch in text for ch in "\n[]{}:,|"):
        return json.dumps(text, ensure_ascii=False)
    return text


def is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def same_keys_object_list(values: list[Any]) -> tuple[bool, list[str]]:
    if not values or not all(isinstance(item, dict) for item in values):
        return False, []
    keys = list(values[0].keys())
    return all(list(item.keys()) == keys and all(is_scalar(v) for v in item.values()) for item in values), keys


def to_toon_value(value: Any, indent: int = 0) -> list[str]:
    pad = "  " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, child in value.items():
            if is_scalar(child):
                lines.append(f"{pad}{key}: {scalar(child)}")
            else:
                lines.append(f"{pad}{key}:")
                lines.extend(to_toon_value(child, indent + 1))
        return lines
    if isinstance(value, list):
        compact, keys = same_keys_object_list(value)
        if compact:
            lines = [f"{pad}[{len(value)}]{{{','.join(keys)}}}:"]
            for item in value:
                lines.append(f"{pad}  " + "|".join(scalar(item[key]) for key in keys))
            return lines
        if all(is_scalar(item) for item in value):
            return [f"{pad}[{','.join(scalar(item) for item in value)}]"]
        lines = []
        for item in value:
            if is_scalar(item):
                lines.append(f"{pad}- {scalar(item)}")
            else:
                lines.append(f"{pad}-")
                lines.extend(to_toon_value(item, indent + 1))
        return lines
    return [f"{pad}{scalar(value)}"]


def json_to_toon(data: Any) -> str:
    return "\n".join(to_toon_value(data)).rstrip() + "\n"


def markdown_to_object(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {"type": "markdown", "sections": []}
    current: dict[str, Any] | None = None
    body: list[str] = []
    bullets: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            body.append(line.strip())
            continue
        heading = None if in_fence else re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            if current is not None:
                current["text"] = "\n".join(body).strip()
                current["bullets"] = "; ".join(bullets)
                root["sections"].append(current)
            current = {"level": len(heading.group(1)), "title": heading.group(2).strip()}
            body = []
            bullets = []
            continue
        bullet = None if in_fence else re.match(r"^\s*[-*]\s+(.+?)\s*$", line)
        if bullet:
            bullets.append(bullet.group(1).strip())
        elif line.strip():
            body.append(line.strip())
    if current is not None:
        current["text"] = "\n".join(body).strip()
        current["bullets"] = "; ".join(bullets)
        root["sections"].append(current)
    else:
        root["text"] = text.strip()
    return root


def markdown_to_toon(text: str) -> str:
    return json_to_toon(markdown_to_object(text))


def file_to_toon(path: Path, input_format: str = "auto") -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    fmt = input_format
    if fmt == "auto":
        fmt = "json" if path.suffix.lower() == ".json" else "md"
    if fmt == "json":
        return json_to_toon(json.loads(text))
    if fmt in {"md", "markdown"}:
        return markdown_to_toon(text)
    raise ValueError(f"unsupported TOON input format: {input_format}")


def toon_stats(original: str, toon: str) -> dict[str, int | float]:
    original_tokens = estimate_tokens(original)
    toon_tokens = estimate_tokens(toon)
    saved = original_tokens - toon_tokens
    return {
        "original_chars": len(original),
        "toon_chars": len(toon),
        "original_tokens_est": original_tokens,
        "toon_tokens_est": toon_tokens,
        "tokens_saved_est": saved,
        "token_reduction_pct_est": round((saved / original_tokens * 100), 2) if original_tokens else 0.0,
    }
