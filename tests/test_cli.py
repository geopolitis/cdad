from contextlib import redirect_stdout
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import io
import sys
import unittest

from cdad_tools.cli import main


class CliTests(unittest.TestCase):
    def test_init_and_doctor(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(main(["--root", str(root), "init"]), 0)
            self.assertTrue((root / "agent/packets").is_dir())
            self.assertEqual(main(["--root", str(root), "doctor"]), 0)

    def test_packet_new_validate_context_progress_and_trace(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src/auth/routes.ts"
            source.parent.mkdir(parents=True)
            source.write_text("export const route = true;\n", encoding="utf-8")

            self.assertEqual(main(["--root", str(root), "init"]), 0)
            self.assertEqual(
                main(
                    [
                        "--root",
                        str(root),
                        "packet",
                        "new",
                        "AUTH-ML-02",
                        "--objective",
                        "Implement backend endpoint",
                        "--why-now",
                        "Frontend needs link issuance",
                        "--context",
                        "src/auth/routes.ts",
                        "--constraint",
                        "Do not change admin auth.",
                        "--verify",
                        f"{sys.executable} -c \"print('ok')\"",
                    ]
                ),
                0,
            )
            self.assertTrue((root / "agent/packets/AUTH-ML-02.json").is_file())
            self.assertEqual(main(["--root", str(root), "validate", "--strict-paths"]), 0)
            self.assertEqual(main(["--root", str(root), "context", "AUTH-ML-02"]), 0)
            self.assertTrue((root / "agent/verification/AUTH-ML-02-context.md").is_file())
            self.assertEqual(main(["--root", str(root), "verify", "AUTH-ML-02"]), 0)
            self.assertTrue((root / "agent/verification/AUTH-ML-02-verification.md").is_file())
            packet = json.loads((root / "agent/packets/AUTH-ML-02.json").read_text(encoding="utf-8"))
            self.assertEqual(packet["status"], "Passed")
            self.assertEqual(packet["verification"][0]["evidence_path"], "agent/verification/AUTH-ML-02-verification.md")
            self.assertEqual(
                main(
                    [
                        "--root",
                        str(root),
                        "progress",
                        "add",
                        "AUTH-ML-02",
                        "--result",
                        "Passed",
                        "--verification",
                        "python command passed",
                        "--next",
                        "Create next packet",
                    ]
                ),
                0,
            )
            self.assertIn("AUTH-ML-02", (root / "agent/progress/progress.md").read_text(encoding="utf-8"))
            packet = json.loads((root / "agent/packets/AUTH-ML-02.json").read_text(encoding="utf-8"))
            self.assertIn("Create next packet", packet["progress_snapshot"])
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--root", str(root), "trace"]), 0)
            self.assertIn("AUTH-ML-02", output.getvalue())

    def test_goal_design_next_integration_verification_and_benchmark(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(main(["--root", str(root), "init"]), 0)
            self.assertEqual(
                main(
                    [
                        "--root",
                        str(root),
                        "goal",
                        "new",
                        "AUTH-ML",
                        "--objective",
                        "Add magic link auth",
                        "--scope-in",
                        "backend endpoint",
                        "--scope-out",
                        "social login",
                        "--constraint",
                        "reuse email provider",
                        "--risk",
                        "token leakage",
                        "--quality-bar",
                        "all tests pass",
                        "--verify",
                        f"{sys.executable} -c \"print('ok')\"",
                    ]
                ),
                0,
            )
            self.assertEqual(main(["--root", str(root), "goal", "validate", "--report"]), 0)
            self.assertTrue((root / "agent/reports/AUTH-ML-goal-validation.json").is_file())

            design = root / "docs/specs/auth-design.md"
            design.write_text(
                """# Auth Design

## Objective
Add magic link auth.

## Scope In
Backend request endpoint.

## Scope Out
Social login.

## Constraints
Reuse email provider.

## Risks
Token leakage.

## Verification
Run auth tests.

## Approval Boundaries
Approve schema, contract, dependency, and security changes.
""",
                encoding="utf-8",
            )
            self.assertEqual(main(["--root", str(root), "design", "validate", "docs/specs/auth-design.md", "--report"]), 0)
            self.assertTrue((root / "agent/reports/auth-design-design-validation.json").is_file())

            source = root / "src/auth/routes.ts"
            source.parent.mkdir(parents=True)
            source.write_text("export const route = true;\n", encoding="utf-8")
            self.assertEqual(
                main(
                    [
                        "--root",
                        str(root),
                        "packet",
                        "new",
                        "AUTH-ML-01",
                        "--goal-id",
                        "AUTH-ML",
                        "--objective",
                        "Implement backend endpoint",
                        "--why-now",
                        "Goal needs runtime path",
                        "--context",
                        "src/auth/routes.ts",
                        "--verify",
                        f"{sys.executable} -c \"print('ok')\"",
                        "--priority",
                        "1",
                        "--risk",
                        "5",
                    ]
                ),
                0,
            )
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["--root", str(root), "next", "--heuristic", "risk-first"]), 0)
            self.assertIn("AUTH-ML-01", output.getvalue())
            next_json = io.StringIO()
            with redirect_stdout(next_json):
                self.assertEqual(main(["--root", str(root), "next", "--heuristic", "risk-first", "--json"]), 0)
            self.assertEqual(json.loads(next_json.getvalue())["selected"]["task_id"], "AUTH-ML-01")
            self.assertEqual(main(["--root", str(root), "integration", "generate", "--all"]), 0)
            self.assertTrue((root / "agent/integrations/codex-cdad.md").is_file())
            self.assertTrue((root / ".claude/commands/cdad.md").is_file())
            (root / "package.json").write_text('{"scripts":{"test":"node --test","lint":"eslint ."}}\n', encoding="utf-8")
            (root / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")
            verification_output = io.StringIO()
            with redirect_stdout(verification_output):
                self.assertEqual(main(["--root", str(root), "verification"]), 0)
            self.assertIn("npm test", verification_output.getvalue())
            self.assertIn("npm run lint", verification_output.getvalue())
            self.assertIn("python3 -m unittest discover -s tests -v", verification_output.getvalue())
            bench = io.StringIO()
            with redirect_stdout(bench):
                self.assertEqual(main(["--root", str(root), "benchmark"]), 0)
            self.assertIn("cdad.benchmark_report.v1", bench.getvalue())

    def test_trace_json_coverage_packet_lifecycle_and_ci(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(main(["--root", str(root), "init"]), 0)
            self.assertTrue((root / "cdad.config.json").is_file())
            source = root / "src/auth/routes.ts"
            source.parent.mkdir(parents=True)
            source.write_text("export const route = true;\n", encoding="utf-8")
            self.assertEqual(
                main(
                    [
                        "--root",
                        str(root),
                        "goal",
                        "new",
                        "AUTH-ML",
                        "--objective",
                        "Add magic link auth",
                        "--scope-in",
                        "backend endpoint",
                        "--scope-out",
                        "social login",
                        "--constraint",
                        "reuse email provider",
                        "--risk",
                        "token leakage",
                        "--quality-bar",
                        "all tests pass",
                        "--verify",
                        f"{sys.executable} -c \"print('ok')\"",
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "--root",
                        str(root),
                        "packet",
                        "new",
                        "AUTH-ML-01",
                        "--objective",
                        "Implement backend endpoint",
                        "--why-now",
                        "Goal needs runtime path",
                        "--context",
                        "src/auth/routes.ts",
                        "--verify",
                        f"{sys.executable} -c \"print('ok')\"",
                    ]
                ),
                0,
            )
            ci_output = io.StringIO()
            with redirect_stdout(ci_output):
                self.assertEqual(main(["--root", str(root), "ci"]), 1)
            self.assertIn("not linked to a goal", ci_output.getvalue())
            self.assertEqual(main(["--root", str(root), "packet", "link-goal", "AUTH-ML-01", "AUTH-ML"]), 0)
            self.assertEqual(main(["--root", str(root), "packet", "status", "AUTH-ML-01", "--status", "Ready"]), 0)
            packet = json.loads((root / "agent/packets/AUTH-ML-01.json").read_text(encoding="utf-8"))
            self.assertEqual(packet["goal_id"], "AUTH-ML")
            self.assertEqual(packet["status"], "Ready")
            trace_json = io.StringIO()
            with redirect_stdout(trace_json):
                self.assertEqual(main(["--root", str(root), "trace", "--json"]), 0)
            self.assertEqual(json.loads(trace_json.getvalue())["packets"][0]["goal_id"], "AUTH-ML")
            self.assertEqual(main(["--root", str(root), "coverage", "--report"]), 0)
            coverage = json.loads((root / "agent/reports/goal-coverage.json").read_text(encoding="utf-8"))
            self.assertEqual(coverage["goals"][0]["linked_packet_count"], 1)
            self.assertTrue((root / "agent/reports/goal-coverage.json").is_file())
            self.assertEqual(main(["--root", str(root), "verify", "AUTH-ML-01"]), 0)
            self.assertEqual(
                main(
                    [
                        "--root",
                        str(root),
                        "progress",
                        "add",
                        "AUTH-ML-01",
                        "--result",
                        "Passed",
                        "--file",
                        "src/auth/routes.ts",
                        "--verification",
                        "ok",
                        "--next",
                        "done",
                    ]
                ),
                0,
            )
            trace_path = root / "agent/reports/trace.json"
            self.assertEqual(main(["--root", str(root), "trace", "--json", "--output", "agent/reports/trace.json"]), 0)
            trace = json.loads(trace_path.read_text(encoding="utf-8"))
            self.assertIn("src/auth/routes.ts", trace["packets"][0]["changed_files"])
            self.assertEqual(main(["--root", str(root), "ci"]), 0)


if __name__ == "__main__":
    unittest.main()
