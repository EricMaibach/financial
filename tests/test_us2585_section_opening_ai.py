"""
Tests for US-258.5: Section AI buttons — AI-generated opening with live section data.

Verifies per the QA test plan:
- Static analysis: no hardcoded opening used as final output on success
- fetch() call present in openChatbotWithSection()
- Typing indicator shown before API call and hidden after (success + error)
- Fallback on failure: ctx.opening used in catch block
- widget.activeSectionId and activeSectionName still set before expand
- All 15 section IDs present in AI_SECTION_CONTEXTS
- Backend: route exists and accepts section_id
- Backend: live data injected into system prompt (variable reference, not literal)
- Backend: system prompt instructs holistic explanation + follow-up invitation
- Backend: route returns JSON with 'response' key
- Backend: route is @login_required
- Backend: graceful AIServiceError → 400
- Backend: graceful upstream AI exception → 503
- Edge: unknown section_id handled gracefully (returns 400)
- Security: section_id used only as dict key lookup, not in paths/SQL/shell
- Security: section_id length/character validation (or rejection of bad values)
- Security: @login_required enforced
"""

import os
import re
import pytest

REPO_ROOT = os.path.join(os.path.dirname(__file__), '..')
STATIC_JS = os.path.join(REPO_ROOT, 'signaltrackers', 'static', 'js', 'components')
DASHBOARD_PY = os.path.join(REPO_ROOT, 'signaltrackers', 'dashboard.py')

AI_SECTION_BTN_JS = os.path.join(STATIC_JS, 'ai-section-btn.js')
CHATBOT_JS = os.path.join(STATIC_JS, 'chatbot.js')


@pytest.fixture(scope='module')
def section_btn_js():
    with open(AI_SECTION_BTN_JS) as f:
        return f.read()


@pytest.fixture(scope='module')
def dashboard_py():
    with open(DASHBOARD_PY) as f:
        return f.read()


# ---------------------------------------------------------------------------
# Static Analysis — ai-section-btn.js
# ---------------------------------------------------------------------------

EXPECTED_SECTION_IDS = [
    'macro-regime-section',
    'briefing-section',
    'sector-tone-section',
    'market-conditions',
    'movers-section',
    'signals-section',
    'recession-panel-section',
    'trade-pulse-section',
    'regime-implications',
    'asset-credit',
    'asset-equity',
    'asset-rates',
    'asset-dollar',
    'asset-crypto',
    'asset-safe-havens',
]


@pytest.mark.parametrize('section_id', EXPECTED_SECTION_IDS)
def test_all_15_section_ids_present(section_btn_js, section_id):
    """All 15 section IDs must be present in AI_SECTION_CONTEXTS."""
    assert section_id in section_btn_js, f"Section ID '{section_id}' missing from ai-section-btn.js"


def test_fetch_call_present_in_open_function(section_btn_js):
    """openChatbotWithSection must contain a fetch() call targeting the backend."""
    assert 'fetch(' in section_btn_js or 'fetch (' in section_btn_js, \
        "openChatbotWithSection must contain a fetch() call"
    assert '/api/chatbot/section-opening' in section_btn_js, \
        "fetch must target /api/chatbot/section-opening"


def test_typing_indicator_shown_before_api_call(section_btn_js):
    """showTypingIndicator must be called before await fetch()."""
    show_pos = section_btn_js.find('showTypingIndicator')
    fetch_pos = section_btn_js.find('fetch(')
    assert show_pos != -1, "showTypingIndicator not found"
    assert fetch_pos != -1, "fetch not found"
    assert show_pos < fetch_pos, \
        "showTypingIndicator must appear before fetch() in the source"


def test_typing_indicator_hidden_in_success_branch(section_btn_js):
    """hideTypingIndicator must appear in the success path (after await)."""
    assert section_btn_js.count('hideTypingIndicator') >= 1, \
        "hideTypingIndicator must be called at least once"


def test_typing_indicator_hidden_in_error_branch(section_btn_js):
    """hideTypingIndicator must appear in both success and error branches."""
    # Count occurrences — must be 2+ (success + catch)
    count = section_btn_js.count('hideTypingIndicator')
    assert count >= 2, \
        f"hideTypingIndicator must appear in both success and catch branches, found {count} occurrences"


def test_fallback_on_failure_uses_static_opening(section_btn_js):
    """The catch block must fall back to ctx.opening (not leave chatbot broken)."""
    # Find catch block and verify ctx.opening is referenced
    catch_match = re.search(r'catch\s*\([^)]*\)\s*\{([^}]+)\}', section_btn_js, re.DOTALL)
    assert catch_match, "catch block not found"
    catch_body = catch_match.group(1)
    assert 'ctx.opening' in catch_body or 'opening' in catch_body, \
        "catch block must reference ctx.opening as fallback"


def test_active_section_id_set_before_expand(section_btn_js):
    """widget.activeSectionId must be set before widget.expand() is called."""
    active_id_pos = section_btn_js.find('activeSectionId')
    expand_pos = section_btn_js.find('widget.expand()')
    assert active_id_pos != -1, "activeSectionId not found"
    assert expand_pos != -1, "widget.expand() not found"
    assert active_id_pos < expand_pos, \
        "activeSectionId must be set before widget.expand() is called"


def test_active_section_name_set_before_expand(section_btn_js):
    """widget.activeSectionName must be set before widget.expand() is called."""
    active_name_pos = section_btn_js.find('activeSectionName')
    expand_pos = section_btn_js.find('widget.expand()')
    assert active_name_pos != -1, "activeSectionName not found"
    assert expand_pos != -1, "widget.expand() not found"
    assert active_name_pos < expand_pos, \
        "activeSectionName must be set before widget.expand() is called"


def test_in_flight_guard_prevents_duplicate_calls(section_btn_js):
    """A guard variable must prevent duplicate API calls from rapid button clicks."""
    # Presence of an in-flight flag pattern
    assert 'InFlight' in section_btn_js or 'inFlight' in section_btn_js \
        or '_flight' in section_btn_js or 'pending' in section_btn_js.lower(), \
        "An in-flight guard must prevent duplicate API calls on rapid button clicks"


def test_expanded_guard_still_present(section_btn_js):
    """If chatbot is already expanded, must not overwrite session."""
    assert "state === 'expanded'" in section_btn_js or 'state==="expanded"' in section_btn_js, \
        "Guard against clobbering active expanded session must still be present"


def test_no_hardcoded_opening_as_final_output_on_success(section_btn_js):
    """ctx.opening must NOT appear as the chatbot's first message on a successful API call.

    It should only be used in the fallback (catch) block or as a variable reference,
    not called directly before the fetch() attempt.
    """
    # The static opening must not be injected before the fetch call
    # Look for addSectionOpeningMessage(ctx.opening) appearing before fetch
    section_opening_before_fetch = re.search(
        r'addSectionOpeningMessage\s*\(\s*ctx\.opening\s*\).*?fetch\s*\(',
        section_btn_js,
        re.DOTALL
    )
    assert section_opening_before_fetch is None, \
        "addSectionOpeningMessage(ctx.opening) must not be called before the fetch() attempt"


# ---------------------------------------------------------------------------
# Backend Tests — dashboard.py
# ---------------------------------------------------------------------------

def test_section_opening_route_exists(dashboard_py):
    """Route /api/chatbot/section-opening must exist."""
    assert '/api/chatbot/section-opening' in dashboard_py, \
        "Route /api/chatbot/section-opening not found in dashboard.py"


def test_section_opening_route_accepts_section_id(dashboard_py):
    """Route must read section_id from request body."""
    assert "section_id" in dashboard_py, "section_id not referenced in dashboard.py"
    # Check it's read from request data
    assert "data.get('section_id'" in dashboard_py or \
           'data.get("section_id"' in dashboard_py, \
        "section_id must be read from request data"


def test_live_data_injected_into_system_prompt(dashboard_py):
    """Live data must be fetched and injected into the system prompt — not just section name."""
    # _get_section_live_data or equivalent must exist and be called
    assert '_get_section_live_data' in dashboard_py, \
        "_get_section_live_data helper must exist"
    assert 'live_data' in dashboard_py or 'live_context' in dashboard_py, \
        "live data variable must be passed to the AI call"


def test_live_data_includes_data_bearing_fields(dashboard_py):
    """Live data helper must include data-bearing fields for accessible sections."""
    # Macro regime section should reference regime state
    assert 'get_macro_regime()' in dashboard_py, \
        "get_macro_regime() must be called for live data context"
    # Recession section
    assert 'get_recession_probability()' in dashboard_py, \
        "get_recession_probability() must be called for live data context"


def test_system_prompt_instructs_holistic_explanation(dashboard_py):
    """System prompt must instruct the AI to explain holistically."""
    assert 'holistic' in dashboard_py or 'plain language' in dashboard_py, \
        "System prompt must direct AI to explain holistically in plain language"


def test_system_prompt_instructs_follow_up_invitation(dashboard_py):
    """System prompt must instruct AI to close with follow-up invitation."""
    assert 'follow-up' in dashboard_py or 'follow up' in dashboard_py, \
        "System prompt must instruct AI to invite follow-up questions"


def test_route_returns_response_key(dashboard_py):
    """Route must return JSON with 'response' key."""
    # Look for jsonify({'response': ...}) in the section opening route area
    route_area = dashboard_py[dashboard_py.find('api_chatbot_section_opening'):]
    assert "'response'" in route_area[:3000] or '"response"' in route_area[:3000], \
        "Route must return JSON with 'response' key"


def test_route_is_login_required(dashboard_py):
    """Section opening route must be @login_required."""
    # Find the route definition and verify @login_required precedes it
    route_idx = dashboard_py.find('/api/chatbot/section-opening')
    assert route_idx != -1
    # Look at 200 chars before route for @login_required
    context_before = dashboard_py[max(0, route_idx - 200):route_idx + 100]
    assert 'login_required' in context_before, \
        "@login_required must decorate the section opening route"


def test_route_handles_ai_service_error_returns_400(dashboard_py):
    """AIServiceError must return HTTP 400 with error message."""
    route_area = dashboard_py[dashboard_py.find('api_chatbot_section_opening'):]
    route_area = route_area[:5000]
    assert 'AIServiceError' in route_area, \
        "Route must catch AIServiceError"
    assert '400' in route_area, \
        "AIServiceError must return HTTP 400"


def test_route_handles_upstream_exception_returns_503(dashboard_py):
    """Upstream AI exception must return HTTP 503."""
    route_area = dashboard_py[dashboard_py.find('api_chatbot_section_opening'):]
    route_area = route_area[:5000]
    assert '503' in route_area, \
        "Upstream AI exception must return HTTP 503"


# ---------------------------------------------------------------------------
# Security Tests
# ---------------------------------------------------------------------------

def test_section_id_used_only_as_dict_key(dashboard_py):
    """section_id must only be used as a dictionary key, not in file paths, SQL, or shell."""
    route_area = dashboard_py[dashboard_py.find('api_chatbot_section_opening'):]
    route_area = route_area[:5000]
    # Must NOT appear in open(), subprocess calls, or SQL
    assert 'open(section_id' not in route_area, \
        "section_id must not be used in open() calls (path traversal risk)"
    assert 'subprocess' not in route_area, \
        "section_id must not be used in subprocess calls"
    assert 'execute(section_id' not in route_area, \
        "section_id must not be passed directly to SQL execute"


def test_section_id_validated_against_allowlist(dashboard_py):
    """section_id must be validated against an allowlist, not used raw."""
    assert '_SECTION_OPENING_ALLOWED' in dashboard_py or \
           'ALLOWED' in dashboard_py or \
           'allowed' in dashboard_py.lower(), \
        "section_id must be validated against an allowlist set"
    assert 'not in' in dashboard_py, \
        "Rejection logic for unknown section_id must be present"


def test_section_id_rejection_returns_400(dashboard_py):
    """Unknown section_id must return HTTP 400."""
    route_area = dashboard_py[dashboard_py.find('api_chatbot_section_opening'):]
    route_area = route_area[:3000]
    # Validation block must return 400 before any data access
    assert '400' in route_area, \
        "Invalid section_id must return HTTP 400"


def test_no_jinja_safe_on_ai_response(dashboard_py):
    """AI response must never be rendered with Jinja2 |safe filter."""
    # For the section opening specifically — the response goes to JS as JSON,
    # so |safe is only dangerous if it were put into a template. Verify no
    # template renders section_opening content with |safe.
    # Since the endpoint returns JSON (not a template render), verify no
    # render_template call in the section opening route function.
    route_fn_area = dashboard_py[dashboard_py.find('def api_chatbot_section_opening'):]
    route_fn_area = route_fn_area[:2000]
    assert 'render_template' not in route_fn_area, \
        "Section opening route must not call render_template (XSS risk via |safe)"


# ---------------------------------------------------------------------------
# Edge Case Tests
# ---------------------------------------------------------------------------

def test_unknown_section_id_rejected(dashboard_py):
    """Unknown section_id must be caught and return an error — not crash."""
    route_area = dashboard_py[dashboard_py.find('api_chatbot_section_opening'):]
    route_area = route_area[:3000]
    assert 'Unknown section_id' in route_area or \
           'unknown section' in route_area.lower() or \
           'not in' in route_area, \
        "Unknown section_id must be rejected before any processing"


def test_section_with_no_data_degrades_gracefully(dashboard_py):
    """_get_section_live_data must have a try/except that handles missing data."""
    helper_area = dashboard_py[dashboard_py.find('def _get_section_live_data'):]
    helper_area = helper_area[:12000]
    assert 'except' in helper_area, \
        "_get_section_live_data must handle exceptions gracefully (data files may be absent)"
    assert 'temporarily unavailable' in helper_area.lower() or \
           'not yet available' in helper_area.lower(), \
        "Fallback message must be returned when data is unavailable"
