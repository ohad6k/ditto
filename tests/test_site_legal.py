import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class SiteLegalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {
            name: (SITE / name).read_text(encoding="utf-8")
            for name in ("privacy.html", "terms.html", "refunds.html")
        }

    def test_every_policy_has_consistent_identity_and_links(self):
        for html in self.pages.values():
            self.assertIn("Emulo", html)
            self.assertIn("Ohad Krispin", html)
            self.assertIn("Israel", html)
            self.assertIn("ohadkrispin@gmail.com", html)
            for href in ("/privacy.html", "/terms.html", "/refunds.html"):
                self.assertIn(f'href="{href}"', html)
            self.assertNotIn("registered company", html.lower())

    def test_privacy_describes_actual_minimized_data(self):
        html = self.pages["privacy.html"]
        for text in (
            "Google",
            "GitHub",
            "Cloudflare",
            "Polar",
            "Vercel",
            "browser session",
            "raw AI session logs",
        ):
            self.assertIn(text, html)
        self.assertIn("never receives the decryption key", html)

    def test_terms_separate_open_source_and_pro(self):
        html = self.pages["terms.html"]
        for text in (
            "MIT License",
            "Emulo Pro",
            "Merchant of Record",
            "automatic renewal",
            "Israel",
        ):
            self.assertIn(text, html)

    def test_refund_windows_are_exact(self):
        html = self.pages["refunds.html"]
        self.assertIn("14 days", html)
        self.assertIn("7 days", html)
        self.assertIn("does not automatically cancel", html)
        self.assertIn("mandatory consumer rights", html.lower())


if __name__ == "__main__":
    unittest.main()
