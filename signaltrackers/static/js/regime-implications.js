/* =============================================================
   Regime Implications Panel — Feature 6.1 / US-145.2
   Handles:
     - Mobile collapse toggle (progressive disclosure)
     - Tablet+ tab bar switching with Arrow key keyboard nav
     - Mobile regime switcher chip switching
   ============================================================= */

(function () {
    'use strict';

    /**
     * Switch the visible regime panel, update tab bar state,
     * update mobile subtitle, and update switcher chip visibility.
     *
     * @param {string} key  - Regime key: 'bull'|'neutral'|'bear'|'recession_watch'
     * @param {string} displayName - Human-readable name, e.g. "Bull Market"
     */
    function switchRegime(key, displayName) {
        // Hide all tabpanels
        document.querySelectorAll('[role="tabpanel"]').forEach(function (panel) {
            panel.setAttribute('hidden', '');
        });

        // Show the selected tabpanel
        var activePanel = document.getElementById('regime-panel-' + key);
        if (activePanel) {
            activePanel.removeAttribute('hidden');
        }

        // Update tab bar: aria-selected, tabindex
        document.querySelectorAll('.regime-tab').forEach(function (tab) {
            var tabKey = tab.id.replace('regime-tab-', '');
            var isActive = (tabKey === key);
            tab.setAttribute('aria-selected', String(isActive));
            tab.setAttribute('tabindex', isActive ? '0' : '-1');
        });

        // Update mobile subtitle
        var subtitle = document.getElementById('regime-implications-subtitle');
        if (subtitle) {
            subtitle.textContent = displayName + ' \u00b7 Historical patterns';
        }

        // Update mobile switcher chips: hide the now-active regime, show others
        document.querySelectorAll('.regime-switcher-chip').forEach(function (chip) {
            var chipKey = chip.getAttribute('data-regime');
            if (chipKey === key) {
                chip.classList.add('regime-switcher-chip--hidden');
            } else {
                chip.classList.remove('regime-switcher-chip--hidden');
            }
        });
    }

    function initRegimeImplications() {
        // ── Mobile collapse toggle ──────────────────────────────────────
        var toggle = document.getElementById('regime-implications-toggle');
        var content = document.getElementById('regime-implications-content');
        var toggleLabel = document.getElementById('regime-implications-toggle-label');

        if (toggle && content) {
            toggle.addEventListener('click', function () {
                var expanded = this.getAttribute('aria-expanded') === 'true';
                this.setAttribute('aria-expanded', String(!expanded));
                if (!expanded) {
                    content.classList.add('regime-implications-content--expanded');
                    if (toggleLabel) { toggleLabel.textContent = 'Hide'; }
                } else {
                    content.classList.remove('regime-implications-content--expanded');
                    if (toggleLabel) { toggleLabel.textContent = 'View Implications'; }
                }
            });
        }

        // ── Tablet+ tab bar: click and Arrow key navigation ─────────────
        var tabBar = document.querySelector('.regime-tab-bar');
        if (tabBar) {
            tabBar.addEventListener('click', function (e) {
                var tab = e.target.closest('[role="tab"]');
                if (!tab) { return; }
                var key = tab.id.replace('regime-tab-', '');
                var displayName = tab.getAttribute('data-display-name') || tab.textContent.replace('★ ', '').trim();
                switchRegime(key, displayName);
                tab.focus();
            });

            tabBar.addEventListener('keydown', function (e) {
                var tabs = Array.from(tabBar.querySelectorAll('[role="tab"]'));
                var activeTab = tabBar.querySelector('[aria-selected="true"]');
                var idx = tabs.indexOf(activeTab);

                if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
                    e.preventDefault();
                    var dir = (e.key === 'ArrowRight') ? 1 : -1;
                    var nextIdx = (idx + dir + tabs.length) % tabs.length;
                    var nextTab = tabs[nextIdx];
                    var key = nextTab.id.replace('regime-tab-', '');
                    var displayName = nextTab.getAttribute('data-display-name') || nextTab.textContent.replace('★ ', '').trim();
                    switchRegime(key, displayName);
                    nextTab.focus();
                } else if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    if (activeTab) { activeTab.click(); }
                }
            });
        }

        // ── Mobile switcher chips ────────────────────────────────────────
        var switcherContainer = document.getElementById('regime-switcher');
        if (switcherContainer) {
            switcherContainer.addEventListener('click', function (e) {
                var chip = e.target.closest('.regime-switcher-chip');
                if (!chip) { return; }
                var key = chip.getAttribute('data-regime');
                var displayName = chip.getAttribute('data-regime-name');
                switchRegime(key, displayName);
            });
        }
    }

    document.addEventListener('DOMContentLoaded', initRegimeImplications);
}());
