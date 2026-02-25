"""
Tests for Bug #55 and Bug #131 — thinking.type parameter history.

Bug #55 (Feb 21, 2026): Changed thinking.type from "enabled" to "adaptive" to fix a
deprecation warning.

Bug #131 (Feb 24, 2026): Reverted thinking.type from "adaptive" back to "enabled" because
the Anthropic API's "adaptive" type does NOT accept a budget_tokens field. The combination
caused a 400 error on every AI summary call, silently falling back to no thinking mode.

Current correct state: thinking.type="enabled" with budget_tokens.
See tests/test_bug131_thinking_type.py for the comprehensive test suite.
"""
import re


AI_SUMMARY_PATH = "signaltrackers/ai_summary.py"


def _load_source():
    with open(AI_SUMMARY_PATH) as f:
        return f.read()


class TestThinkingTypeCorrect:
    """Verify thinking.type is 'enabled' (reverted from Bug #131 fix)."""

    def test_enabled_in_thinking_block(self):
        """'enabled' must be used as thinking type (reverted from adaptive per Bug #131)."""
        source = _load_source()
        assert '"type": "enabled"' in source, (
            "thinking.type='enabled' not found in ai_summary.py — Bug #131 fix may be missing"
        )

    def test_no_adaptive_type(self):
        """'adaptive' must NOT appear as thinking type — adaptive rejects budget_tokens."""
        source = _load_source()
        assert '"type": "adaptive"' not in source, (
            "thinking.type='adaptive' still present in ai_summary.py — causes 400 error with budget_tokens"
        )
        assert "'type': 'adaptive'" not in source, (
            "thinking.type='adaptive' still present in ai_summary.py — causes 400 error with budget_tokens"
        )

    def test_exactly_one_thinking_call_site(self):
        """Confirm there is exactly one call site defining the thinking parameter block."""
        source = _load_source()
        definitions = re.findall(r'"thinking"\s*:\s*\{', source)
        assert len(definitions) == 1, (
            f"Expected exactly 1 thinking block definition, found {len(definitions)}"
        )

    def test_budget_tokens_preserved(self):
        """budget_tokens must still be passed alongside the type."""
        source = _load_source()
        thinking_idx = source.index('"thinking"')
        context = source[thinking_idx: thinking_idx + 200]
        assert "budget_tokens" in context, (
            "budget_tokens not found near the thinking block — may have been lost"
        )

    def test_budget_tokens_values_in_range(self):
        """All thinking budget values must be within Anthropic-recommended limits (1–32768)."""
        source = _load_source()
        matches = re.findall(r"effort_budgets\s*=\s*\{([^}]+)\}", source, re.DOTALL)
        assert matches, "effort_budgets dict not found in ai_summary.py"
        budget_block = matches[0]
        values = re.findall(r":\s*(\d+)", budget_block)
        for raw_val in values:
            val = int(raw_val)
            assert 1 <= val <= 32768, (
                f"thinking budget value {val} is outside allowed range 1–32768"
            )
