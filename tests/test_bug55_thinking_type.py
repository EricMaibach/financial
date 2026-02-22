"""
Tests for Bug #55 — Deprecated thinking.type parameter fix.

Verifies the static code fix without requiring live Anthropic API calls.
"""
import ast
import textwrap


AI_SUMMARY_PATH = "signaltrackers/ai_summary.py"


def _load_source():
    with open(AI_SUMMARY_PATH) as f:
        return f.read()


class TestThinkingTypeFixed:
    """Verify the deprecated thinking.type=enabled has been replaced."""

    def test_no_enabled_in_thinking_block(self):
        """'enabled' must not appear as thinking type anywhere in ai_summary.py."""
        source = _load_source()
        # Check for the exact deprecated pattern
        assert '"type": "enabled"' not in source, (
            "Deprecated thinking.type='enabled' still present in ai_summary.py"
        )
        assert "'type': 'enabled'" not in source, (
            "Deprecated thinking.type='enabled' still present in ai_summary.py"
        )

    def test_adaptive_type_present(self):
        """'adaptive' must be used as thinking type."""
        source = _load_source()
        assert '"type": "adaptive"' in source, (
            "thinking.type='adaptive' not found in ai_summary.py"
        )

    def test_exactly_one_thinking_call_site(self):
        """Confirm there is exactly one call site defining the thinking parameter block."""
        source = _load_source()
        import re
        # Match the thinking dict definition (not the del statement)
        definitions = re.findall(r'"thinking"\s*:\s*\{', source)
        assert len(definitions) == 1, (
            f"Expected exactly 1 thinking block definition, found {len(definitions)}"
        )

    def test_budget_tokens_preserved(self):
        """budget_tokens must still be passed alongside the type."""
        source = _load_source()
        # Find the thinking block and confirm budget_tokens is nearby
        thinking_idx = source.index('"thinking"')
        # Look for budget_tokens within the next 200 characters (the block)
        context = source[thinking_idx : thinking_idx + 200]
        assert "budget_tokens" in context, (
            "budget_tokens not found near the thinking block — may have been lost"
        )

    def test_budget_tokens_values_in_range(self):
        """All thinking budget values must be within Anthropic-recommended limits (1–32768)."""
        source = _load_source()
        # Parse effort_budgets dict values from source
        import re
        matches = re.findall(r"effort_budgets\s*=\s*\{([^}]+)\}", source, re.DOTALL)
        assert matches, "effort_budgets dict not found in ai_summary.py"
        budget_block = matches[0]
        values = re.findall(r":\s*(\d+)", budget_block)
        for raw_val in values:
            val = int(raw_val)
            assert 1 <= val <= 32768, (
                f"thinking budget value {val} is outside allowed range 1–32768"
            )
