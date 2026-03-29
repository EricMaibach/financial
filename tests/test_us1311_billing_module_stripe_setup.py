"""
US-13.1.1: Billing Module & Stripe SDK Setup

Tests for:
- Billing module exists as an architecturally distinct area
- Stripe Python SDK is installed and importable
- Stripe client initialises from environment variables
- Application starts when Stripe env vars are absent (graceful degradation)
- .env.example documents all required Stripe variables
- No hardcoded Stripe keys in the codebase
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
SIGNALTRACKERS_DIR = REPO_ROOT / "signaltrackers"
BILLING_DIR = SIGNALTRACKERS_DIR / "billing"

sys.path.insert(0, str(SIGNALTRACKERS_DIR))


# ===========================================================================
# Module Structure
# ===========================================================================

class TestBillingModuleStructure:
    """Billing module exists as an architecturally distinct area."""

    def test_billing_directory_exists(self):
        assert BILLING_DIR.is_dir(), "signaltrackers/billing/ directory must exist"

    def test_billing_init_exists(self):
        init_file = BILLING_DIR / "__init__.py"
        assert init_file.is_file(), "signaltrackers/billing/__init__.py must exist"

    def test_billing_module_importable(self):
        import billing
        assert hasattr(billing, "init_stripe")
        assert hasattr(billing, "is_stripe_configured")
        assert hasattr(billing, "get_publishable_key")
        assert hasattr(billing, "get_webhook_secret")
        assert hasattr(billing, "get_price_id")


# ===========================================================================
# Stripe SDK
# ===========================================================================

class TestStripeSdkInstalled:
    """Stripe Python SDK is installed and importable."""

    def test_stripe_importable(self):
        import stripe
        assert hasattr(stripe, "api_key")
        assert hasattr(stripe, "VERSION")


# ===========================================================================
# Stripe Client Initialisation
# ===========================================================================

class TestStripeClientInit:
    """Stripe client initialises from environment variables."""

    def test_init_stripe_with_key(self):
        import stripe
        from billing import init_stripe, is_stripe_configured

        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test_fake123"}):
            result = init_stripe()
            assert result is True
            assert is_stripe_configured() is True
            assert stripe.api_key == "sk_test_fake123"

    def test_init_stripe_without_key(self):
        from billing import init_stripe, is_stripe_configured

        env = os.environ.copy()
        env.pop("STRIPE_SECRET_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            result = init_stripe()
            assert result is False
            assert is_stripe_configured() is False

    def test_init_stripe_empty_key(self):
        from billing import init_stripe, is_stripe_configured

        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": ""}):
            result = init_stripe()
            assert result is False
            assert is_stripe_configured() is False

    def test_init_stripe_whitespace_key(self):
        from billing import init_stripe, is_stripe_configured

        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": "   "}):
            result = init_stripe()
            assert result is False
            assert is_stripe_configured() is False

    def test_no_hardcoded_keys(self):
        """No Stripe keys hardcoded anywhere in the codebase."""
        import re

        patterns = [
            r"sk_test_[A-Za-z0-9]{10,}",
            r"sk_live_[A-Za-z0-9]{10,}",
            r"pk_test_[A-Za-z0-9]{10,}",
            r"pk_live_[A-Za-z0-9]{10,}",
            r"whsec_[A-Za-z0-9]{10,}",
        ]

        violations = []
        for py_file in SIGNALTRACKERS_DIR.rglob("*.py"):
            content = py_file.read_text()
            for pattern in patterns:
                if re.search(pattern, content):
                    violations.append(f"{py_file.relative_to(REPO_ROOT)}: matches {pattern}")

        assert not violations, (
            "Hardcoded Stripe keys found:\n" + "\n".join(violations)
        )


# ===========================================================================
# Helper Functions
# ===========================================================================

class TestHelperFunctions:
    """Publishable key, webhook secret, and price ID helpers."""

    def test_get_publishable_key_set(self):
        from billing import get_publishable_key

        with patch.dict(os.environ, {"STRIPE_PUBLISHABLE_KEY": "pk_test_abc"}):
            assert get_publishable_key() == "pk_test_abc"

    def test_get_publishable_key_unset(self):
        from billing import get_publishable_key

        env = os.environ.copy()
        env.pop("STRIPE_PUBLISHABLE_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            assert get_publishable_key() is None

    def test_get_publishable_key_empty(self):
        from billing import get_publishable_key

        with patch.dict(os.environ, {"STRIPE_PUBLISHABLE_KEY": ""}):
            assert get_publishable_key() is None

    def test_get_webhook_secret_set(self):
        from billing import get_webhook_secret

        with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "whsec_test"}):
            assert get_webhook_secret() == "whsec_test"

    def test_get_webhook_secret_unset(self):
        from billing import get_webhook_secret

        env = os.environ.copy()
        env.pop("STRIPE_WEBHOOK_SECRET", None)
        with patch.dict(os.environ, env, clear=True):
            assert get_webhook_secret() is None

    def test_get_price_id_set(self):
        from billing import get_price_id

        with patch.dict(os.environ, {"STRIPE_PRICE_ID": "price_123"}):
            assert get_price_id() == "price_123"

    def test_get_price_id_unset(self):
        from billing import get_price_id

        env = os.environ.copy()
        env.pop("STRIPE_PRICE_ID", None)
        with patch.dict(os.environ, env, clear=True):
            assert get_price_id() is None


# ===========================================================================
# Graceful Degradation
# ===========================================================================

class TestGracefulDegradation:
    """App starts and works when Stripe env vars are absent."""

    def test_billing_import_without_env_vars(self):
        """Importing the billing module never raises, even without env vars."""
        env = os.environ.copy()
        for key in ("STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY",
                     "STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE_ID"):
            env.pop(key, None)

        with patch.dict(os.environ, env, clear=True):
            from billing import init_stripe, is_stripe_configured
            init_stripe()
            assert is_stripe_configured() is False

    def test_invalid_key_format_no_crash(self):
        """Malformed key doesn't crash at init time."""
        from billing import init_stripe, is_stripe_configured

        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": "not-a-real-key"}):
            result = init_stripe()
            # A non-empty string is accepted at init; validation happens on use
            assert result is True
            assert is_stripe_configured() is True


# ===========================================================================
# .env.example Configuration
# ===========================================================================

class TestEnvExample:
    """.env.example documents all Stripe variables with comments."""

    @pytest.fixture(autouse=True)
    def _load_env_example(self):
        env_example = REPO_ROOT / ".env.example"
        assert env_example.is_file(), ".env.example must exist"
        self.content = env_example.read_text()

    @pytest.mark.parametrize("var", [
        "STRIPE_SECRET_KEY",
        "STRIPE_PUBLISHABLE_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "STRIPE_PRICE_ID",
    ])
    def test_variable_present(self, var):
        assert var in self.content, f"{var} must be in .env.example"

    def test_no_real_keys_in_env_example(self):
        """Placeholder values only — no actual Stripe keys."""
        import re
        for pattern in (r"sk_test_\w{10,}", r"sk_live_\w{10,}",
                        r"pk_test_\w{10,}", r"pk_live_\w{10,}",
                        r"whsec_\w{10,}"):
            assert not re.search(pattern, self.content), (
                f".env.example must not contain real keys matching {pattern}"
            )

    def test_variables_have_comments(self):
        """Each Stripe variable should have an explanatory comment nearby."""
        lines = self.content.splitlines()
        for var in ("STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY",
                     "STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE_ID"):
            # Find the line with the variable
            var_idx = next(
                (i for i, line in enumerate(lines) if var in line and not line.strip().startswith("#")),
                None,
            )
            assert var_idx is not None, f"{var} not found as a variable line"
            # Check that at least one comment line precedes it within 5 lines
            preceding = lines[max(0, var_idx - 5):var_idx]
            has_comment = any(line.strip().startswith("#") for line in preceding)
            assert has_comment, f"{var} should have an explanatory comment above it"


# ===========================================================================
# Security — .env not committed
# ===========================================================================

class TestSecurity:
    """Ensure .env is gitignored."""

    def test_env_in_gitignore(self):
        gitignore = REPO_ROOT / ".gitignore"
        assert gitignore.is_file()
        content = gitignore.read_text()
        assert ".env" in content, ".env must be listed in .gitignore"

    def test_env_file_not_tracked(self):
        """If a .env file exists, it should not be tracked by git."""
        import subprocess

        result = subprocess.run(
            ["git", "ls-files", ".env"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.stdout.strip() == "", ".env must not be tracked by git"
