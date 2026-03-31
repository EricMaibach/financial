"""
US-13.2.1: Invite Code on Registration

Tests for:
- Registration form includes invite code field when configured
- Registration fails with clear error for missing/invalid invite code
- Registration succeeds with correct invite code
- Invite code is configurable via environment variable
- Invalid invite code does not create a partial account
- No invite code field shown when INVITE_CODE is not configured
"""

import ast
import os
import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
SIGNALTRACKERS_DIR = REPO_ROOT / 'signaltrackers'

sys.path.insert(0, str(SIGNALTRACKERS_DIR))

DASHBOARD_FILE = SIGNALTRACKERS_DIR / 'dashboard.py'
CONFIG_FILE = SIGNALTRACKERS_DIR / 'config.py'
REGISTER_TEMPLATE = SIGNALTRACKERS_DIR / 'templates' / 'auth' / 'register.html'
ENV_EXAMPLE_FILE = REPO_ROOT / '.env.example'

DASHBOARD_SOURCE = DASHBOARD_FILE.read_text()
CONFIG_SOURCE = CONFIG_FILE.read_text()
REGISTER_HTML = REGISTER_TEMPLATE.read_text()
ENV_EXAMPLE_SOURCE = ENV_EXAMPLE_FILE.read_text()


# ---------------------------------------------------------------------------
# AC1: Registration form includes invite code field
# ---------------------------------------------------------------------------

class TestInviteCodeFormField:
    """Registration form shows an invite code field when INVITE_CODE is configured."""

    def test_invite_code_input_present_in_template(self):
        """Template contains an invite_code input field."""
        assert 'name="invite_code"' in REGISTER_HTML

    def test_invite_code_field_has_label(self):
        """Invite code field has a visible label."""
        assert 'for="invite_code"' in REGISTER_HTML
        assert 'Invite Code' in REGISTER_HTML

    def test_invite_code_field_conditionally_rendered(self):
        """Invite code field is wrapped in a config check (only shown when configured)."""
        assert 'config.INVITE_CODE' in REGISTER_HTML

    def test_invite_code_field_is_required_when_shown(self):
        """When the invite code field is visible, it has the required attribute."""
        # Extract the invite code input
        match = re.search(r'<input[^>]*name="invite_code"[^>]*>', REGISTER_HTML)
        assert match, "invite_code input not found"
        assert 'required' in match.group()

    def test_invite_code_field_appears_before_username(self):
        """Invite code field appears before the username field in the form."""
        invite_pos = REGISTER_HTML.index('name="invite_code"')
        username_pos = REGISTER_HTML.index('name="username"')
        assert invite_pos < username_pos

    def test_invite_code_has_helper_text(self):
        """Invite code field has helper text explaining invite-only access."""
        assert 'invite-only' in REGISTER_HTML.lower()


# ---------------------------------------------------------------------------
# AC2: Registration fails with clear error for invalid invite code
# ---------------------------------------------------------------------------

class TestInviteCodeValidation:
    """Registration route validates invite code and rejects invalid/missing codes."""

    def test_route_reads_invite_code_from_form(self):
        """Register route extracts invite_code from form data."""
        assert "request.form.get('invite_code'" in DASHBOARD_SOURCE

    def test_route_checks_app_config_invite_code(self):
        """Register route reads expected invite code from app config."""
        assert "app.config" in DASHBOARD_SOURCE
        assert "'INVITE_CODE'" in DASHBOARD_SOURCE

    def test_error_message_for_invalid_code(self):
        """Specific error message for invalid invite code is defined."""
        assert 'Registration is currently invite-only. Contact us for access.' in DASHBOARD_SOURCE

    def test_uses_constant_time_comparison(self):
        """Invite code comparison uses hmac.compare_digest to prevent timing attacks."""
        assert 'hmac.compare_digest' in DASHBOARD_SOURCE

    def test_hmac_imported(self):
        """hmac module is imported in dashboard.py."""
        assert 'import hmac' in DASHBOARD_SOURCE


# ---------------------------------------------------------------------------
# AC3: Registration succeeds with correct invite code
# ---------------------------------------------------------------------------

class TestInviteCodeSuccessPath:
    """Valid invite code allows registration to proceed normally."""

    def test_invite_code_check_before_other_validation(self):
        """Invite code validation happens before username/email/password checks."""
        tree = ast.parse(DASHBOARD_SOURCE)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'register':
                # Find the first error append that mentions invite-only
                source_lines = DASHBOARD_SOURCE.splitlines()
                func_start = node.lineno
                func_body = '\n'.join(source_lines[func_start:func_start + 80])
                invite_pos = func_body.find('invite-only')
                username_pos = func_body.find('Username is required')
                assert invite_pos < username_pos, \
                    "Invite code check should come before username validation"
                return
        pytest.fail("register function not found")

    def test_empty_invite_config_disables_gate(self):
        """When INVITE_CODE config is empty, the invite check is skipped."""
        # The code should check `if expected_code` before comparing
        assert re.search(
            r'if\s+expected_code\s+and',
            DASHBOARD_SOURCE
        ), "Invite code check should be conditional on expected_code being non-empty"


# ---------------------------------------------------------------------------
# AC4: Invite code configurable via environment variable
# ---------------------------------------------------------------------------

class TestInviteCodeConfiguration:
    """INVITE_CODE is configurable via environment variable in app config."""

    def test_invite_code_in_config_class(self):
        """Config class defines INVITE_CODE from environment variable."""
        assert 'INVITE_CODE' in CONFIG_SOURCE

    def test_invite_code_reads_from_env(self):
        """INVITE_CODE is read from os.environ."""
        assert re.search(r"os\.environ\.get\(['\"]INVITE_CODE['\"]", CONFIG_SOURCE)

    def test_invite_code_defaults_to_empty(self):
        """INVITE_CODE defaults to empty string (open registration)."""
        match = re.search(
            r"INVITE_CODE\s*=\s*os\.environ\.get\(['\"]INVITE_CODE['\"],\s*['\"]['\"]",
            CONFIG_SOURCE
        )
        assert match, "INVITE_CODE should default to empty string"

    def test_env_example_documents_invite_code(self):
        """The .env.example file documents the INVITE_CODE variable."""
        assert 'INVITE_CODE' in ENV_EXAMPLE_SOURCE

    def test_env_example_invite_code_empty_default(self):
        """The .env.example has INVITE_CODE with empty value (open registration by default)."""
        assert 'INVITE_CODE=' in ENV_EXAMPLE_SOURCE


# ---------------------------------------------------------------------------
# AC5: Invalid invite code does not create a partial account
# ---------------------------------------------------------------------------

class TestNoPartialAccountCreation:
    """Invalid invite code must not create any database records."""

    def test_invite_check_before_user_creation(self):
        """Invite code validation errors are added before User() instantiation."""
        tree = ast.parse(DASHBOARD_SOURCE)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'register':
                source_lines = DASHBOARD_SOURCE.splitlines()
                func_start = node.lineno
                func_body = '\n'.join(source_lines[func_start:func_start + 100])
                invite_error_pos = func_body.find('invite-only')
                errors_check_pos = func_body.find('if errors:')
                user_creation_pos = func_body.find('User(username=')
                assert invite_error_pos < errors_check_pos < user_creation_pos, \
                    "Invite error should be added before error check, which is before User creation"
                return
        pytest.fail("register function not found")

    def test_errors_block_returns_before_db_commit(self):
        """When errors exist, the route returns before any db.session operations."""
        tree = ast.parse(DASHBOARD_SOURCE)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'register':
                source_lines = DASHBOARD_SOURCE.splitlines()
                func_start = node.lineno
                func_body = '\n'.join(source_lines[func_start:func_start + 100])
                errors_return_pos = func_body.find("return render_template('auth/register.html')")
                db_commit_pos = func_body.find('db.session.commit()')
                assert errors_return_pos < db_commit_pos, \
                    "Error return should happen before db commit"
                return
        pytest.fail("register function not found")


# ---------------------------------------------------------------------------
# Security: No information leakage
# ---------------------------------------------------------------------------

class TestSecurityNoInfoLeakage:
    """Invalid invite code error message does not reveal valid codes."""

    def test_error_message_is_generic(self):
        """Error message for invalid invite code does not contain the actual code."""
        # The error message should be a static string, not include the expected code
        error_msg = 'Registration is currently invite-only. Contact us for access.'
        assert error_msg in DASHBOARD_SOURCE
        # Verify the error append doesn't include expected_code variable
        lines = DASHBOARD_SOURCE.splitlines()
        for i, line in enumerate(lines):
            if error_msg in line:
                assert 'expected_code' not in line or 'expected_code)' not in line, \
                    "Error message should not include the expected code value"

    def test_invite_code_not_in_template_value(self):
        """Template does not expose the expected invite code in any attribute."""
        assert 'INVITE_CODE' not in REGISTER_HTML or \
            'config.INVITE_CODE' in REGISTER_HTML, \
            "Template should only reference INVITE_CODE as a boolean check, not expose its value"
        # Ensure the template only uses it in an {% if %} check, not as a value attribute
        for line in REGISTER_HTML.splitlines():
            if 'INVITE_CODE' in line:
                assert '{%' in line or '{#' in line, \
                    f"INVITE_CODE should only appear in template tags, not as output: {line.strip()}"
