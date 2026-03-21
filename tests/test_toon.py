import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cdad_tools.cli import main
from cdad_tools.toon import json_to_toon, markdown_to_toon, toon_stats


class ToonTests(unittest.TestCase):
    def test_json_to_toon_compacts_repeated_objects(self) -> None:
        rendered = json_to_toon({"items": [{"id": "A", "status": "Ready"}, {"id": "B", "status": "Passed"}]})

        self.assertIn("items:", rendered)
        self.assertIn("[2]{id,status}:", rendered)
        self.assertIn("A|Ready", rendered)

    def test_markdown_to_toon_preserves_sections_and_bullets(self) -> None:
        rendered = markdown_to_toon("# Goal\n\n## Scope In\n- backend\n- tests\n")

        self.assertIn("type: markdown", rendered)
        self.assertIn("[2]{level,title,text,bullets}:", rendered)
        self.assertIn("Scope In", rendered)
        self.assertIn("backend; tests", rendered)

    def test_toon_cli_writes_output_and_stats_are_smaller_for_repeated_json(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "packet.json"
            source.write_text(
                json.dumps({"items": [{"id": "A", "status": "Ready"}, {"id": "B", "status": "Passed"}]}),
                encoding="utf-8",
            )

            self.assertEqual(main(["--root", str(root), "toon", "packet.json", "--output", "packet.toon"]), 0)
            original = source.read_text(encoding="utf-8")
            toon = (root / "packet.toon").read_text(encoding="utf-8")
            stats = toon_stats(original, toon)

            self.assertTrue((root / "packet.toon").is_file())
            self.assertLess(stats["toon_tokens_est"], stats["original_tokens_est"])


if __name__ == "__main__":
    unittest.main()
