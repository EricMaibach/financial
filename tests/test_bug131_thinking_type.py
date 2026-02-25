"""
Tests for Bug #131 — Thinking mode broken after Bug #55 fix.

Root cause: Bug #55 (Feb 21, 2026) changed thinking.type from "enabled" to "adaptive"
to address a deprecation warning. However, the Anthropic API's "adaptive" type does NOT
accept a budget_tokens field — it causes a 400 error on every call. The fallback silently
retried without thinking mode, degrading all AI summary quality.

Fix: Revert thinking.type from "adaptive" back to "enabled". The "enabled" type correctly
accepts budget_tokens. The deprecation warning for "enabled" was a false alarm.

File: signaltrackers/ai_summary.py, line ~279
Branch: fix/bug-131-thinking-mode

Acceptance criteria from QA test plan:
  AC-1: "type": "enabled" appears in the thinking block
  AC-2: "type": "adaptive" does NOT appear anywhere in ai_summary.py
  AC-3: budget_tokens is still present in the same thinking block
  AC-4: Only one thinking block definition exists
  AC-5: All effort_budgets values are within Anthropic-documented range (1–32768)
  AC-6: test_bug55_thinking_type.py updated (done — see that file)
  AC-7: All previously passing tests still pass (no regressions)
"""
import re


AI_SUMMARY_PATH = "signaltrackers/ai_summary.py"


def _load_source():
    with open(AI_SUMMARY_PATH) as f:
        return f.read()


class TestBug131ThinkingModeFix:
    """Comprehensive verification of the Bug #131 fix."""

    def test_ac1_enabled_type_present(self):
        """AC-1: 'type': 'enabled' must appear in the thinking block."""
        source = _load_source()
        assert '"type": "enabled"' in source, (
            'AC-1 FAIL: thinking.type="enabled" not found in ai_summary.py. '
            'Bug #131 fix is missing — "enabled" type is required for budget_tokens to work.'
        )

    def test_ac2_no_adaptive_type(self):
        """AC-2: 'type': 'adaptive' must NOT appear anywhere in ai_summary.py."""
        source = _load_source()
        assert '"type": "adaptive"' not in source, (
            'AC-2 FAIL: thinking.type="adaptive" still present. '
            'Adaptive type rejects budget_tokens (causes 400 error on every AI call).'
        )
        assert "'type': 'adaptive'" not in source, (
            "AC-2 FAIL: thinking.type='adaptive' (single-quoted) still present in ai_summary.py."
        )

    def test_ac3_budget_tokens_in_thinking_block(self):
        """AC-3: budget_tokens must be present in the same thinking block as the type."""
        source = _load_source()
        # Find the thinking block definition (not the del statement)
        match = re.search(r'"thinking"\s*:\s*\{([^}]+)\}', source)
        assert match is not None, (
            "AC-3 FAIL: Could not find the thinking block definition in ai_summary.py"
        )
        block_content = match.group(1)
        assert "budget_tokens" in block_content, (
            "AC-3 FAIL: budget_tokens not found inside the thinking block. "
            "It must be passed alongside type='enabled' for extended thinking to work."
        )

    def test_ac4_exactly_one_thinking_block(self):
        """AC-4: Exactly one thinking block definition must exist."""
        source = _load_source()
        definitions = re.findall(r'"thinking"\s*:\s*\{', source)
        assert len(definitions) == 1, (
            f"AC-4 FAIL: Expected exactly 1 thinking block definition, found {len(definitions)}. "
            "Multiple definitions could indicate a copy/paste error."
        )

    def test_ac5_effort_budgets_in_valid_range(self):
        """AC-5: All effort_budgets values must be in Anthropic-documented range (1–32768)."""
        source = _load_source()
        matches = re.findall(r"effort_budgets\s*=\s*\{([^}]+)\}", source, re.DOTALL)
        assert matches, "AC-5 FAIL: effort_budgets dict not found in ai_summary.py"
        budget_block = matches[0]
        values = re.findall(r":\s*(\d+)", budget_block)
        assert values, "AC-5 FAIL: No numeric values found in effort_budgets dict"
        for raw_val in values:
            val = int(raw_val)
            assert 1 <= val <= 32768, (
                f"AC-5 FAIL: thinking budget value {val} is outside valid range 1–32768. "
                "Anthropic rejects budget_tokens values outside this range."
            )

    def test_thinking_block_structure_complete(self):
        """Both required fields (type and budget_tokens) must appear in the thinking block."""
        source = _load_source()
        match = re.search(r'"thinking"\s*:\s*\{([^}]+)\}', source)
        assert match is not None, "Could not locate thinking block definition"
        block = match.group(1)
        assert '"type"' in block or "'type'" in block, (
            "The 'type' key is missing from the thinking block"
        )
        assert "budget_tokens" in block, (
            "The 'budget_tokens' key is missing from the thinking block"
        )

    def test_fallback_del_statement_still_present(self):
        """The fallback that deletes thinking on error must still be present."""
        source = _load_source()
        assert 'del api_params["thinking"]' in source, (
            "The thinking-mode fallback (del api_params['thinking']) was removed. "
            "It must be preserved to handle any future API errors gracefully."
        )

    def test_thinking_budget_variable_used(self):
        """budget_tokens must reference thinking_budget variable (not a hardcoded literal)."""
        source = _load_source()
        match = re.search(r'"thinking"\s*:\s*\{([^}]+)\}', source)
        assert match is not None, "Could not locate thinking block definition"
        block = match.group(1)
        assert "thinking_budget" in block, (
            "budget_tokens should reference the 'thinking_budget' variable, not a hardcoded literal. "
            "This ensures the effort level setting is respected."
        )
