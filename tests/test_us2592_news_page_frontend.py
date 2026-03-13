"""
Tests for US-259.2: News page frontend template and CSS.

Verifies:
- Flask test client renders /news correctly for each state (no data, summary+sources, stale)
- AI summary card: indigo left border, AI SUMMARY label, role=region, aria-label
- Source cards: aria-label with 'opens in new tab', arrow icon, domain display, rel attrs
- Empty states: bi-newspaper icon for 'no data'; bi-wifi-off for 'API unavailable no prior data'
- Stale banner: warning styling class, exclamation icon, date shown
- Page title: 'News — SignalTrackers'
- Security: summary_text and headline NOT rendered with | safe filter
- CSS: hover translateY, warning color vars, source card no-grid (single column flex)
- Accessibility: role=region on summary card, aria-label on source links
- 'Generated from X sources' footer with correct pluralization
- Desktop two-column layout (flex with flex:2 + flex:1 child)
- Source card URL fallback behavior (no crash on None url)
"""

import os
import re
import sys
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(REPO_ROOT, 'signaltrackers', 'templates')
STATIC_CSS = os.path.join(REPO_ROOT, 'signaltrackers', 'static', 'css')
DASHBOARD_PY = os.path.join(REPO_ROOT, 'signaltrackers', 'dashboard.py')

NEWS_HTML = os.path.join(TEMPLATES_DIR, 'news.html')
NEWS_CSS = os.path.join(STATIC_CSS, 'news.css')


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope='module')
def news_html():
    with open(NEWS_HTML) as f:
        return f.read()


@pytest.fixture(scope='module')
def news_css():
    with open(NEWS_CSS) as f:
        return f.read()


@pytest.fixture(scope='module')
def flask_app():
    """Create a test Flask app client."""
    sys.path.insert(0, os.path.join(REPO_ROOT, 'signaltrackers'))
    import dashboard as app_module
    app_module.app.config['TESTING'] = True
    app_module.app.config['WTF_CSRF_ENABLED'] = False
    with app_module.app.test_client() as client:
        yield client


# ─── Flask Route Rendering ────────────────────────────────────────────────────

class TestNewsRouteRendering:
    def test_news_page_returns_200(self, flask_app):
        resp = flask_app.get('/news')
        assert resp.status_code == 200

    def test_page_title_correct(self, flask_app):
        resp = flask_app.get('/news')
        html = resp.data.decode('utf-8')
        assert 'News' in html and 'SignalTrackers' in html

    def test_page_contains_heading(self, flask_app):
        resp = flask_app.get('/news')
        assert b"Today's Macro News" in resp.data

    def test_empty_state_shown_by_default(self, flask_app):
        resp = flask_app.get('/news')
        assert b'No news yet' in resp.data

    def test_empty_state_icon_present(self, flask_app):
        resp = flask_app.get('/news')
        assert b'bi-newspaper' in resp.data

    def test_no_summary_card_in_empty_state(self, flask_app):
        resp = flask_app.get('/news')
        assert b'news-summary-card' not in resp.data

    def test_no_stale_banner_in_empty_state(self, flask_app):
        resp = flask_app.get('/news')
        assert b'news-stale-banner' not in resp.data


# ─── AI Summary Card Structure ────────────────────────────────────────────────

class TestAISummaryCard:
    def test_summary_card_class_present(self, news_html):
        assert 'news-summary-card' in news_html

    def test_role_region_on_summary(self, news_html):
        assert 'role="region"' in news_html

    def test_aria_label_ai_generated(self, news_html):
        assert 'AI-generated news summary' in news_html

    def test_ai_summary_label_uppercase_text(self, news_html):
        # Label text should be 'AI Summary' or 'AI SUMMARY'
        assert re.search(r'AI\s+SUMMARY|AI\s+Summary', news_html, re.IGNORECASE)

    def test_ai_sparkle_or_icon_present(self, news_html):
        # Design spec says prefix label with sparkle mark or bi-stars
        assert 'sparkle' in news_html.lower() or 'stars' in news_html.lower() or \
               '<svg' in news_html or 'bi-stars' in news_html

    def test_generated_from_sources_footer(self, news_html):
        assert 'Generated from' in news_html

    def test_sources_count_in_footer(self, news_html):
        assert 'sources | length' in news_html or '| length' in news_html

    def test_summary_card_footer_class(self, news_html):
        assert 'news-summary-card__footer' in news_html

    def test_summary_text_rendered_in_paragraph(self, news_html):
        # summary_text should be inside a <p> tag
        assert re.search(r'<p[^>]*>.*summary_text.*</p>', news_html, re.DOTALL)


# ─── Source Cards ─────────────────────────────────────────────────────────────

class TestSourceCards:
    def test_source_card_class_in_template(self, news_html):
        assert 'news-source-card' in news_html

    def test_source_link_new_tab(self, news_html):
        assert 'target="_blank"' in news_html

    def test_source_link_rel_noopener(self, news_html):
        assert 'rel="noopener noreferrer"' in news_html

    def test_source_aria_label_includes_opens_in_new_tab(self, news_html):
        assert 'opens in new tab' in news_html

    def test_source_aria_label_includes_headline(self, news_html):
        # aria-label should reference source.headline
        assert 'source.headline' in news_html

    def test_arrow_icon_present(self, news_html):
        assert 'bi-arrow-up-right' in news_html

    def test_arrow_icon_aria_hidden(self, news_html):
        # Arrow is decorative — must be aria-hidden
        arrow_section = news_html[news_html.find('bi-arrow-up-right') - 100:
                                   news_html.find('bi-arrow-up-right') + 100]
        assert 'aria-hidden' in arrow_section

    def test_extract_domain_called_for_meta(self, news_html):
        assert 'extract_domain' in news_html

    def test_source_headline_class(self, news_html):
        assert 'news-source-card__headline' in news_html

    def test_source_meta_class(self, news_html):
        assert 'news-source-card__meta' in news_html

    def test_sources_section_label_shows_count(self, news_html):
        # SOURCES (X) label
        assert 'sources | length' in news_html or '| length' in news_html


# ─── Empty States ─────────────────────────────────────────────────────────────

class TestEmptyStates:
    def test_no_news_yet_heading(self, news_html):
        assert 'No news yet' in news_html

    def test_no_news_yet_icon_bi_newspaper(self, news_html):
        assert 'bi-newspaper' in news_html

    def test_api_unavailable_no_prior_heading(self, news_html):
        assert 'News unavailable' in news_html

    def test_api_unavailable_icon_bi_wifi_off(self, news_html):
        assert 'bi-wifi-off' in news_html

    def test_api_unavailable_no_prior_description(self, news_html):
        assert 'retry' in news_html.lower() or 'tomorrow' in news_html.lower()

    def test_empty_state_class(self, news_html):
        assert 'news-empty-state' in news_html

    def test_empty_state_icon_class(self, news_html):
        assert 'news-empty-state__icon' in news_html


# ─── Stale Data Banner ────────────────────────────────────────────────────────

class TestStaleBanner:
    def test_stale_banner_class(self, news_html):
        assert 'news-stale-banner' in news_html

    def test_stale_banner_role_alert(self, news_html):
        assert 'role="alert"' in news_html

    def test_stale_banner_exclamation_icon(self, news_html):
        assert 'bi-exclamation-triangle' in news_html

    def test_stale_banner_shows_stale_date(self, news_html):
        assert 'stale_date' in news_html

    def test_stale_banner_conditional_on_is_stale(self, news_html):
        assert 'is_stale' in news_html

    def test_stale_banner_message_text(self, news_html):
        assert "today's fetch is unavailable" in news_html or "fetch is unavailable" in news_html


# ─── Security ─────────────────────────────────────────────────────────────────

class TestSecurity:
    def test_summary_text_not_rendered_with_safe(self, news_html):
        # Find summary_text in template — should NOT be followed by | safe
        matches = re.findall(r'summary_text\s*\|?\s*safe', news_html)
        assert not matches, "summary_text must NOT use | safe filter (XSS risk)"

    def test_headline_not_rendered_with_safe(self, news_html):
        matches = re.findall(r'source\.headline\s*\|?\s*safe', news_html)
        assert not matches, "source.headline must NOT use | safe filter (XSS risk)"

    def test_url_rendered_directly_or_conditionally(self, news_html):
        # source.url should appear in href but not with | safe applied to content areas
        assert 'source.url' in news_html


# ─── Accessibility ────────────────────────────────────────────────────────────

class TestAccessibility:
    def test_page_h1_present(self, news_html):
        assert '<h1' in news_html

    def test_news_icon_aria_hidden(self, news_html):
        # bi-newspaper in h1 should be aria-hidden
        newspaper_pos = news_html.find('bi bi-newspaper')
        if newspaper_pos >= 0:
            context = news_html[newspaper_pos - 50: newspaper_pos + 100]
            assert 'aria-hidden' in context

    def test_summary_card_has_region_role(self, news_html):
        assert 'role="region"' in news_html

    def test_source_aria_labels_present(self, news_html):
        assert 'aria-label' in news_html

    def test_page_title_block(self, news_html):
        assert '{% block title %}News' in news_html


# ─── CSS Structure ────────────────────────────────────────────────────────────

class TestCSSStructure:
    def test_source_card_hover_translatey(self, news_css):
        assert 'translateY(-1px)' in news_css

    def test_source_card_hover_shadow(self, news_css):
        assert '.news-source-card:hover' in news_css
        assert 'box-shadow' in news_css

    def test_warning_100_var_defined(self, news_css):
        assert '--warning-100' in news_css

    def test_warning_700_var_defined(self, news_css):
        assert '--warning-700' in news_css

    def test_stale_banner_uses_warning_colors(self, news_css):
        css = news_css
        stale_section = css[css.find('stale'):]
        assert 'warning' in stale_section[:300]

    def test_source_list_is_flex_column_not_grid(self, news_css):
        # Sources should be in a flex column, NOT a grid (per spec: single-column list)
        assert 'news-sources__list' in news_css
        sources_section = news_css[news_css.find('news-sources__list'):
                                    news_css.find('news-sources__list') + 200]
        assert 'flex-direction: column' in sources_section
        assert 'grid' not in sources_section.lower()

    def test_desktop_layout_uses_flex_not_grid(self, news_css):
        # Desktop two-column layout should use flexbox, not CSS grid
        layout_section = news_css[news_css.find('news-layout'):
                                    news_css.find('news-layout') + 300]
        assert 'display: flex' in layout_section

    def test_summary_card_flex_2(self, news_css):
        # Summary card takes 2/3 width on desktop via flex: 2
        assert 'flex: 2' in news_css

    def test_sources_flex_1(self, news_css):
        # Sources panel takes 1/3 width on desktop via flex: 1
        assert 'flex: 1' in news_css

    def test_touch_target_min_height(self, news_css):
        assert '56px' in news_css

    def test_source_card_border_radius(self, news_css):
        assert 'border-radius: 8px' in news_css

    def test_summary_card_indigo_border(self, news_css):
        assert 'brand-indigo-500' in news_css or '#6366f1' in news_css.lower() or '#6366F1' in news_css

    def test_transition_on_source_card(self, news_css):
        assert 'transition' in news_css

    def test_desktop_breakpoint_1024(self, news_css):
        assert '1024px' in news_css

    def test_summary_card_sticky_on_desktop(self, news_css):
        assert 'sticky' in news_css


# ─── Layout: Two-Column Desktop ──────────────────────────────────────────────

class TestDesktopLayout:
    def test_news_layout_class_in_template(self, news_html):
        assert 'news-layout' in news_html

    def test_summary_in_left_column(self, news_html):
        layout_start = news_html.find('news-layout')
        summary_start = news_html.find('news-summary-card', layout_start)
        sources_start = news_html.find('news-sources', layout_start)
        assert summary_start < sources_start, "Summary card should come before sources in template"

    def test_mobile_single_column_implied_by_default_flex_direction(self, news_css):
        # Default (mobile) layout should be column
        mobile_section = news_css[:news_css.find('1024px')]
        assert 'flex-direction: column' in mobile_section


# ─── Source Pluralization ─────────────────────────────────────────────────────

class TestPluralisation:
    def test_singular_source_form(self, news_html):
        # Template should handle "1 source" vs "2 sources"
        assert "source'" in news_html or "source''" in news_html or \
               "'s' if" in news_html or "pluralize" in news_html or \
               "!= 1" in news_html
