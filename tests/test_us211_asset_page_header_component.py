"""
US-207.1: Asset Detail Page Header — Shared CSS Component
QA verification tests for the shared .asset-page-header component.
Tests structural correctness: class migration, --category-color values,
aria-hidden, and removal of old per-page header CSS.
"""

import os
import re
import pytest

TEMPLATES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "signaltrackers", "templates"
)
COMPONENT_CSS = os.path.join(
    os.path.dirname(__file__),
    "..",
    "signaltrackers",
    "static",
    "css",
    "components",
    "asset-page-header.css",
)
DESIGN_SYSTEM = os.path.join(
    os.path.dirname(__file__), "..", "docs", "design-system.md"
)

TEMPLATES = {
    "credit": "#dc3545",
    "equity": "#0d6efd",
    "rates": "#0d6efd",
    "dollar": "#0dcaf0",
    "crypto": "#ffc107",
    "safe_havens": "#198754",
}

OLD_HEADER_CLASSES = [
    "credit-header",
    "equity-header",
    "rates-header",
    "dollar-header",
    "crypto-header",
    "safe-havens-header",
]


def read_template(name):
    path = os.path.join(TEMPLATES_DIR, f"{name}.html")
    with open(path) as f:
        return f.read()


def read_component_css():
    with open(COMPONENT_CSS) as f:
        return f.read()


def read_design_system():
    with open(DESIGN_SYSTEM) as f:
        return f.read()


# ── Component CSS file ────────────────────────────────────────────────────────


class TestComponentCSSFile:
    def test_file_exists(self):
        assert os.path.exists(COMPONENT_CSS), "asset-page-header.css not found"

    def test_defines_asset_page_header(self):
        css = read_component_css()
        assert ".asset-page-header {" in css or ".asset-page-header{" in css

    def test_defines_title_modifier(self):
        css = read_component_css()
        assert ".asset-page-header__title" in css

    def test_defines_description_modifier(self):
        css = read_component_css()
        assert ".asset-page-header__description" in css

    def test_defines_updated_modifier(self):
        css = read_component_css()
        assert ".asset-page-header__updated" in css

    def test_documents_category_color_variable(self):
        # --category-color is applied via inline style on the icon in each template,
        # not directly in the CSS file. The CSS file documents this in its header comment.
        css = read_component_css()
        assert "--category-color" in css, (
            "asset-page-header.css should document --category-color usage"
        )


# ── Per-template structural checks ────────────────────────────────────────────


@pytest.mark.parametrize("tmpl_name,expected_color", TEMPLATES.items())
class TestTemplateClassMigration:
    def test_component_css_linked(self, tmpl_name, expected_color):
        html = read_template(tmpl_name)
        assert "asset-page-header.css" in html, (
            f"{tmpl_name}.html missing link to asset-page-header.css"
        )

    def test_category_color_defined_in_root(self, tmpl_name, expected_color):
        html = read_template(tmpl_name)
        assert "--category-color:" in html, (
            f"{tmpl_name}.html missing --category-color in :root"
        )

    def test_category_color_correct_hex(self, tmpl_name, expected_color):
        html = read_template(tmpl_name)
        pattern = rf"--category-color:\s*{re.escape(expected_color)}"
        assert re.search(pattern, html, re.IGNORECASE), (
            f"{tmpl_name}.html --category-color is not {expected_color}"
        )

    def test_uses_asset_page_header_class(self, tmpl_name, expected_color):
        html = read_template(tmpl_name)
        assert 'class="asset-page-header"' in html or "asset-page-header" in html, (
            f"{tmpl_name}.html missing .asset-page-header class"
        )

    def test_uses_title_modifier(self, tmpl_name, expected_color):
        html = read_template(tmpl_name)
        assert "asset-page-header__title" in html, (
            f"{tmpl_name}.html missing .asset-page-header__title"
        )

    def test_uses_description_modifier(self, tmpl_name, expected_color):
        html = read_template(tmpl_name)
        assert "asset-page-header__description" in html, (
            f"{tmpl_name}.html missing .asset-page-header__description"
        )

    def test_uses_updated_modifier(self, tmpl_name, expected_color):
        html = read_template(tmpl_name)
        assert "asset-page-header__updated" in html, (
            f"{tmpl_name}.html missing .asset-page-header__updated"
        )

    def test_old_header_class_removed(self, tmpl_name, expected_color):
        html = read_template(tmpl_name)
        for old_cls in OLD_HEADER_CLASSES:
            # Only the class matching this template's old name should be gone
            if tmpl_name.replace("_", "-") in old_cls or tmpl_name in old_cls:
                assert old_cls not in html, (
                    f"{tmpl_name}.html still contains old class '{old_cls}'"
                )

    def test_header_icon_uses_category_color_style(self, tmpl_name, expected_color):
        html = read_template(tmpl_name)
        # Header icon must use style="color: var(--category-color);" not Bootstrap text-* class
        # We look for the asset-page-header__title icon pattern
        title_block = re.search(
            r'class="asset-page-header__title"[^>]*>.*?</h1>',
            html,
            re.DOTALL,
        )
        assert title_block is not None, (
            f"{tmpl_name}.html missing asset-page-header__title h1 block"
        )
        title_html = title_block.group(0)
        assert "color: var(--category-color)" in title_html, (
            f"{tmpl_name}.html header icon missing 'color: var(--category-color)'"
        )

    def test_header_icon_has_aria_hidden(self, tmpl_name, expected_color):
        html = read_template(tmpl_name)
        title_block = re.search(
            r'class="asset-page-header__title"[^>]*>.*?</h1>',
            html,
            re.DOTALL,
        )
        assert title_block is not None
        title_html = title_block.group(0)
        assert 'aria-hidden="true"' in title_html, (
            f"{tmpl_name}.html header icon missing aria-hidden='true'"
        )

    def test_no_bootstrap_color_class_on_header_icon(self, tmpl_name, expected_color):
        html = read_template(tmpl_name)
        title_block = re.search(
            r'class="asset-page-header__title"[^>]*>.*?</h1>',
            html,
            re.DOTALL,
        )
        assert title_block is not None
        title_html = title_block.group(0)
        bootstrap_color_classes = [
            "text-danger",
            "text-primary",
            "text-success",
            "text-warning",
            "text-info",
            "text-secondary",
        ]
        for cls in bootstrap_color_classes:
            assert cls not in title_html, (
                f"{tmpl_name}.html header icon still uses Bootstrap class '{cls}'"
            )


# ── Design system documentation ───────────────────────────────────────────────


class TestDesignSystemDocumentation:
    def test_component_entry_present(self):
        ds = read_design_system()
        assert "asset-page-header" in ds, (
            "docs/design-system.md missing .asset-page-header component entry"
        )

    def test_category_color_documented(self):
        ds = read_design_system()
        assert "--category-color" in ds, (
            "docs/design-system.md missing --category-color documentation"
        )


# ── credit.html: --category-credit retained for non-header elements ───────────


class TestCategoryCreditRetained:
    def test_category_credit_still_defined(self):
        html = read_template("credit")
        assert "--category-credit:" in html, (
            "credit.html should retain --category-credit for non-header elements"
        )

    def test_category_credit_used_for_non_header(self):
        html = read_template("credit")
        # Should be used outside the header section (e.g. interpretation block border)
        uses = [m.start() for m in re.finditer(r"--category-credit", html)]
        assert len(uses) >= 2, (
            "credit.html --category-credit should be used in multiple places (not only defined)"
        )
