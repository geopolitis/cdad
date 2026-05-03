from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re

from .schema import ValidationSeverity


SECTION_ALIASES = {
    "objective": ("objective", "goal", "purpose"),
    "scope_in": ("scope in", "in scope", "scope"),
    "scope_out": ("scope out", "out of scope", "non-goals", "non goals"),
    "constraints": ("constraints", "constraint"),
    "risks": ("risks", "risk"),
    "verification": ("verification", "acceptance", "tests", "checks"),
    "approval_boundaries": ("approval boundaries", "approval", "escalate", "escalation"),
}

SCOPE_OUT_TERMS = ("frontend", "social login", "migration", "mobile app", "redesign")


@dataclass(slots=True)
class ValidationFinding:
    severity: ValidationSeverity
    code: str
    message: str
    section: str

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "section": self.section,
        }


def extract_sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^(#{1,6})\s+(.+?)\s*$", text, flags=re.MULTILINE))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        title = match.group(2).strip().lower()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()
    return sections


def find_section(sections: dict[str, str], aliases: tuple[str, ...]) -> tuple[str, str] | None:
    for title, body in sections.items():
        normalized = re.sub(r"[^a-z0-9 ]+", "", title)
        if any(alias in normalized for alias in aliases):
            return title, body
    return None


def validate_design_text(text: str) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    sections = extract_sections(text)
    for canonical, aliases in SECTION_ALIASES.items():
        found = find_section(sections, aliases)
        if found is None:
            findings.append(
                ValidationFinding(
                    ValidationSeverity.ERROR,
                    f"missing_{canonical}",
                    f"Missing section for {canonical.replace('_', ' ')}.",
                    canonical,
                )
            )
            continue
        title, body = found
        if len(body) < 12 or "tbd" in body.lower():
            findings.append(
                ValidationFinding(
                    ValidationSeverity.WARNING,
                    f"thin_{canonical}",
                    f"Section '{title}' is empty, too thin, or still marked TBD.",
                    canonical,
                )
            )
    lower = text.lower()
    if "test" not in lower and "verify" not in lower and "scenario" not in lower:
        findings.append(
            ValidationFinding(
                ValidationSeverity.ERROR,
                "missing_verification_oracle",
                "Design does not appear to define a concrete verification oracle.",
                "verification",
            )
        )
    if not any(word in lower for word in ("dependency", "schema", "contract", "security", "destructive", "scope")):
        findings.append(
            ValidationFinding(
                ValidationSeverity.WARNING,
                "weak_approval_boundaries",
                "Approval boundaries do not mention common high-risk change classes.",
                "approval_boundaries",
            )
        )
    objective = find_section(sections, SECTION_ALIASES["objective"])
    scope_out = find_section(sections, SECTION_ALIASES["scope_out"])
    verification = find_section(sections, SECTION_ALIASES["verification"])
    risks = find_section(sections, SECTION_ALIASES["risks"])
    constraints = find_section(sections, SECTION_ALIASES["constraints"])
    approvals = find_section(sections, SECTION_ALIASES["approval_boundaries"])
    if objective and scope_out:
        objective_body = objective[1].lower()
        scope_out_body = scope_out[1].lower()
        for term in SCOPE_OUT_TERMS:
            if term in objective_body and term in scope_out_body:
                findings.append(
                    ValidationFinding(
                        ValidationSeverity.ERROR,
                        "objective_conflicts_with_scope_out",
                        f"Objective appears to include scope-out term '{term}'.",
                        "objective",
                    )
                )
    if risks and verification:
        risk_body = risks[1].lower()
        verification_body = verification[1].lower()
        if "security" in risk_body or "token" in risk_body:
            if not any(word in verification_body for word in ("security", "token", "expired", "replay", "auth")):
                findings.append(
                    ValidationFinding(
                        ValidationSeverity.WARNING,
                        "risk_not_reflected_in_verification",
                        "Security/token risk is not reflected in verification.",
                        "verification",
                    )
                )
    if constraints and approvals:
        constraint_body = constraints[1].lower()
        approval_body = approvals[1].lower()
        for term in ("schema", "dependency", "contract", "security"):
            if term in constraint_body and term not in approval_body:
                findings.append(
                    ValidationFinding(
                        ValidationSeverity.WARNING,
                        "constraint_missing_approval_boundary",
                        f"Constraint mentions {term}, but approval boundaries do not.",
                        "approval_boundaries",
                    )
                )
    return findings


def validate_design_file(path: Path) -> list[ValidationFinding]:
    return validate_design_text(path.read_text(encoding="utf-8", errors="replace"))


def render_validation_report(path: Path, findings: list[ValidationFinding]) -> str:
    status = "passed" if not any(f.severity == ValidationSeverity.ERROR for f in findings) else "failed"
    return json.dumps(
        {
            "schema": "cdad.design_validation_report.v1",
            "path": str(path),
            "status": status,
            "findings": [finding.to_dict() for finding in findings],
        },
        indent=2,
    ) + "\n"
