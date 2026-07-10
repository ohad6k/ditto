import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ditto_manifests", ROOT / "ditto.py")
ditto = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ditto)


class PluginSkillTest(unittest.TestCase):
    def read(self, name):
        return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")

    def test_exact_skill_names(self):
        expected = {"mine": "mine", "work": "work", "design": "design", "write": "write"}
        for folder, name in expected.items():
            fields = ditto.parse_frontmatter(self.read(folder))
            self.assertEqual(name, fields["name"])

    def test_routing_descriptions_are_mutually_bounded(self):
        mine = self.read("mine").lower()
        work = self.read("work").lower()
        design = self.read("design").lower()
        write = self.read("write").lower()
        self.assertIn("explicitly asks", mine)
        self.assertIn("do not use for design", work)
        self.assertIn("ui, ux, visual", design)
        self.assertIn("marketing, social, replies", write)
        self.assertNotIn("depth beats token efficiency", mine)

    def test_domain_loaders_use_only_profile_path_command(self):
        self.assertIn("plugin profile-path --domain work", self.read("work"))
        self.assertIn("plugin profile-path --domain design", self.read("design"))
        self.assertIn("plugin profile-path --domain write", self.read("write"))


if __name__ == "__main__":
    unittest.main()
