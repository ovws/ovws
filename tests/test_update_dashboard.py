import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "update_dashboard.py"
SPEC = importlib.util.spec_from_file_location("update_dashboard", SCRIPT)
dashboard = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(dashboard)


def repo(name, language, pushed, *, fork=False, private=False):
    return {
        "name": name,
        "language": language,
        "pushed_at": pushed,
        "fork": fork,
        "private": private,
    }


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.repos = [
            repo("ovws", None, "2026-07-15T00:00:00Z"),
            repo("source-a", "TypeScript", "2026-07-14T00:00:00Z"),
            repo("source-b", "Go", "2026-05-01T00:00:00Z"),
            repo("old-source", "TypeScript", "2025-02-01T00:00:00Z"),
            repo("forked", "Python", "2026-07-13T00:00:00Z", fork=True),
            repo("private", "Rust", "2026-07-12T00:00:00Z", private=True),
        ]

    def test_filters_forks_and_private_repositories(self):
        names = [item["name"] for item in dashboard.source_repos(self.repos)]
        self.assertEqual(names, ["ovws", "source-a", "source-b", "old-source"])

    def test_stats_exclude_profile_repository(self):
        stats = dashboard.profile_stats("ovws", self.repos)
        self.assertEqual(stats["source_count"], 3)
        self.assertEqual(stats["language_count"], 2)
        self.assertEqual(stats["active_count"], 2)
        self.assertNotIn("forked", stats["source_names"])

    def test_readme_rejects_non_source_link(self):
        with tempfile.TemporaryDirectory() as directory:
            readme = Path(directory) / "README.md"
            readme.write_text("https://github.com/ovws/forked", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "forked"):
                dashboard.assert_readme_source_only(readme, "ovws", {"source-a"})

    def test_svg_mentions_filter_and_has_no_script(self):
        stats = dashboard.profile_stats("ovws", self.repos)
        svg = dashboard.render_dashboard("ovws", stats, "dark")
        self.assertIn("FORK FILTER: ON", svg)
        self.assertIn("source-a", svg)
        self.assertNotIn("forked", svg)
        self.assertNotIn("<script", svg)


if __name__ == "__main__":
    unittest.main()
