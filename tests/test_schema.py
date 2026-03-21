from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cdad_tools.schema import (
    GoalRecord,
    PacketStatus,
    TaskPacket,
    Verification,
    VerificationKind,
    validate_goal,
    validate_packet,
)


class SchemaTests(unittest.TestCase):
    def test_valid_packet_has_no_schema_issues_without_path_checks(self) -> None:
        packet = TaskPacket(
            task_id="AUTH-ML-02",
            objective="Implement endpoint",
            why_now="Frontend needs it",
            relevant_context=["src/auth/routes.ts"],
            constraints=["Stay inside auth route scope."],
            verification=[Verification(VerificationKind.UNIT, command="python -m unittest")],
            escalation_conditions=[
                "Escalate dependency, schema, contract, security boundary, destructive, or scope-widening changes."
            ],
        )

        self.assertEqual(validate_packet(packet), [])

    def test_missing_required_packet_fields_are_reported(self) -> None:
        packet = TaskPacket(task_id="", objective="", why_now="")

        issues = validate_packet(packet)

        self.assertIn("task_id is required", issues)
        self.assertIn("objective is required", issues)
        self.assertIn("at least one verification entry is required", issues)

    def test_passed_packet_requires_evidence_reference(self) -> None:
        packet = TaskPacket(
            task_id="AUTH-ML-02",
            objective="Implement endpoint",
            why_now="Frontend needs it",
            relevant_context=["src/auth/routes.ts"],
            constraints=["Stay inside auth route scope."],
            verification=[Verification(VerificationKind.UNIT, command="python -m unittest")],
            escalation_conditions=["Escalate dependency changes."],
            status=PacketStatus.PASSED,
        )

        self.assertIn("Passed packets should reference verification evidence", validate_packet(packet))

    def test_strict_path_validation_reports_missing_context(self) -> None:
        with TemporaryDirectory() as tmp:
            packet = TaskPacket(
                task_id="AUTH-ML-02",
                objective="Implement endpoint",
                why_now="Frontend needs it",
                relevant_context=["src/auth/routes.ts"],
                constraints=["Stay inside auth route scope."],
                verification=[Verification(VerificationKind.UNIT, command="python -m unittest")],
                escalation_conditions=["Escalate dependency changes."],
            )

            self.assertIn("relevant_context path does not exist: src/auth/routes.ts", validate_packet(packet, Path(tmp)))

    def test_valid_goal_has_no_issues(self) -> None:
        goal = GoalRecord(
            goal_id="AUTH-ML",
            objective="Add magic link login",
            scope_in=["backend endpoint"],
            scope_out=["social login"],
            constraints=["reuse email provider"],
            verification=[Verification(VerificationKind.UNIT, command="npm test")],
            risks=["token leakage"],
            approval_boundaries=["Approve schema and security boundary changes."],
            quality_bar="All tests pass and expired links are rejected.",
        )

        self.assertEqual(validate_goal(goal), [])

    def test_goal_requires_scope_and_quality_bar(self) -> None:
        issues = validate_goal(GoalRecord(goal_id="G1", objective="Do work"))

        self.assertIn("scope_in is required", issues)
        self.assertIn("quality_bar is required", issues)


if __name__ == "__main__":
    unittest.main()
