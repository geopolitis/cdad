from tempfile import TemporaryDirectory
from pathlib import Path
import unittest

from cdad_tools.context import collect_context, discover_related_context, estimate_tokens, render_context_bundle, source_terms
from cdad_tools.schema import TaskPacket


class ContextTests(unittest.TestCase):
    def test_estimate_tokens_is_stable_minimum(self) -> None:
        self.assertEqual(estimate_tokens(""), 1)
        self.assertEqual(estimate_tokens("abcd"), 1)
        self.assertEqual(estimate_tokens("abcde"), 2)

    def test_source_terms_extracts_symbols_and_imports(self) -> None:
        terms = source_terms("from src.auth.magic_link import request_magic_link\n\ndef request_magic_link(email): pass\n")

        self.assertIn("request-magic-link", terms)
        self.assertIn("src.auth.magic", " ".join(sorted(terms)))

    def test_collect_context_includes_referenced_text_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src/example.py"
            source.parent.mkdir()
            source.write_text("print('hello')\n", encoding="utf-8")
            packet = TaskPacket(
                task_id="T1",
                objective="Read file",
                why_now="Test",
                relevant_context=["src/example.py"],
            )

            items, warnings = collect_context(root, packet, token_budget=100)
            bundle = render_context_bundle(packet, items, warnings)

            self.assertEqual(warnings, [])
            self.assertEqual(items[0].path, "src/example.py")
            self.assertIn("print('hello')", bundle)

    def test_discover_related_context_finds_tests_and_docs(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            test_file = root / "tests/auth_magic_link_test.py"
            test_file.parent.mkdir()
            test_file.write_text("def test_magic_link(): pass\n", encoding="utf-8")
            spec_file = root / "docs/specs/auth.md"
            spec_file.parent.mkdir(parents=True)
            spec_file.write_text("magic link authentication spec\n", encoding="utf-8")
            packet = TaskPacket(task_id="AUTH-ML-02", objective="Implement magic link endpoint", why_now="Auth")

            discovered = discover_related_context(root, packet)

            self.assertIn("tests/auth_magic_link_test.py", discovered)

    def test_discover_related_context_skips_goal_markdown_when_json_is_explicit(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            goal_json = root / "docs/specs/AUTH.goal.json"
            goal_md = root / "docs/specs/AUTH.goal.md"
            goal_json.parent.mkdir(parents=True)
            goal_json.write_text('{"goal_id": "AUTH"}\n', encoding="utf-8")
            goal_md.write_text("# Goal Record: AUTH\n\nMagic link auth.\n", encoding="utf-8")
            packet = TaskPacket(
                task_id="AUTH-ML-01",
                objective="Implement magic link auth",
                why_now="Test",
                references=["docs/specs/AUTH.goal.json"],
            )

            discovered = discover_related_context(root, packet)

            self.assertNotIn("docs/specs/AUTH.goal.md", discovered)


if __name__ == "__main__":
    unittest.main()
