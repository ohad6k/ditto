import re
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PUBLIC = [*SITE.glob("*.html"), SITE / "legal.css"]


class EmuloPublicSecurityTests(unittest.TestCase):
    def test_public_files_contain_no_secret_shapes_or_provider_ids(self):
        text = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC)
        for value in (
            "ce99808b-4e11-4cec-bc31-d9654d558e08",
            "b6535378-b1bd-40ee-bd37-96a03abec2f2",
        ):
            self.assertNotIn(value, text)
        self.assertNotRegex(
            text,
            re.compile(
                r"(?:polar_(?:oat|sk)|client_secret\s*[=:]|webhook_secret\s*[=:]|BEGIN PRIVATE KEY)",
                re.I,
            ),
        )

    def test_public_copy_does_not_claim_unavailable_paid_features(self):
        text = (SITE / "index.html").read_text(encoding="utf-8").lower()
        self.assertNotIn("encrypted sync is available", text)
        self.assertNotIn("payment successful", text)
        self.assertNotIn("private beta", text)

    def test_policy_pages_load_only_same_origin_assets(self):
        for name in ("privacy.html", "terms.html", "refunds.html"):
            text = (SITE / name).read_text(encoding="utf-8")
            self.assertNotRegex(text, re.compile(r"<(?:script|iframe)\b", re.I))
            self.assertNotRegex(text, re.compile(r'(?:src|href)="https?://', re.I))

    def test_google_credentials_and_tokens_do_not_cross_public_boundaries(self):
        public_text = "\n".join(
            path.read_text(encoding="utf-8") for path in PUBLIC
        )
        for marker in (
            "GOOGLE_CLIENT_SECRET",
            "id_token",
            "access_token",
            ".apps.googleusercontent.com",
        ):
            self.assertNotIn(marker, public_text)

        production = json.loads(
            (ROOT / "cloud" / "worker" / "wrangler.production.jsonc").read_text(
                encoding="utf-8"
            )
        )
        self.assertNotIn("GOOGLE_CLIENT_SECRET", production["vars"])

        google_auth = (
            ROOT / "cloud" / "worker" / "src" / "google-auth.ts"
        ).read_text(encoding="utf-8")
        self.assertNotRegex(
            google_auth,
            re.compile(r"console\.(?:log|warn|error)\([^\n]*(?:idToken|accessToken)", re.I),
        )
        migrations = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "cloud" / "worker" / "migrations").glob("*.sql")
        )
        self.assertNotRegex(migrations, re.compile(r"\b(?:id|access|refresh)_token\b", re.I))


if __name__ == "__main__":
    unittest.main()
