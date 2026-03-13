/**
 * AI Briefing Toolbar — Sentence-Level Drill-In (Desktop)
 * US-258.3: Floating selection toolbar with Copy + Ask AI for the AI briefing block.
 *
 * Design decisions:
 * - Toolbar is desktop-only (hidden on pointer:coarse via CSS).
 * - Listens for mouseup on the briefing narrative element specifically.
 * - Positions 8px above the selection midpoint; clamps left/right to stay in viewport.
 * - Disappears on: deselection, scroll, Escape key, click outside.
 * - Ask AI fires a real AI call via window.chatbotWidget.openWithTextDrillIn().
 */

(function () {
    'use strict';

    let toolbar = null;
    let currentSelectedText = '';
    let scrollListenerAttached = false;

    function init() {
        toolbar = document.getElementById('ai-briefing-toolbar');
        if (!toolbar) return;

        const briefingNarrative = document.getElementById('briefing-narrative');
        if (!briefingNarrative) return;

        // Listen for mouseup on the briefing narrative block
        briefingNarrative.addEventListener('mouseup', onMouseUp);

        // Global escape + deselect handling
        document.addEventListener('keydown', onKeyDown);
        document.addEventListener('mousedown', onMouseDown);

        // Copy button
        const copyBtn = toolbar.querySelector('.ai-briefing-toolbar__copy');
        if (copyBtn) {
            copyBtn.addEventListener('click', onCopyClick);
        }

        // Ask AI button
        const askAiBtn = toolbar.querySelector('.ai-briefing-toolbar__ask-ai');
        if (askAiBtn) {
            askAiBtn.addEventListener('click', onAskAiClick);
        }
    }

    function onMouseUp(e) {
        // Small delay to let the browser finalise the selection
        setTimeout(() => {
            const selection = window.getSelection();
            const selectedText = selection ? selection.toString().trim() : '';

            if (!selectedText) {
                hideToolbar();
                return;
            }

            // Confirm selection is within the briefing narrative block
            const briefingNarrative = document.getElementById('briefing-narrative');
            if (!briefingNarrative || !isSelectionWithin(selection, briefingNarrative)) {
                hideToolbar();
                return;
            }

            currentSelectedText = selectedText;
            positionAndShow(selection);
        }, 0);
    }

    function onKeyDown(e) {
        if (e.key === 'Escape') {
            hideToolbar();
        }
    }

    function onMouseDown(e) {
        // Hide toolbar if click is outside the toolbar itself
        if (toolbar && !toolbar.contains(e.target)) {
            // Don't hide immediately — let mouseup fire first so the toolbar
            // can still appear on a new selection. We hide on deselect instead.
            // But if click is outside briefing narrative AND toolbar, hide.
            const briefingNarrative = document.getElementById('briefing-narrative');
            if (!briefingNarrative || (!briefingNarrative.contains(e.target) && !toolbar.contains(e.target))) {
                hideToolbar();
            }
        }
    }

    function onScroll() {
        hideToolbar();
    }

    function onCopyClick() {
        if (!currentSelectedText) return;

        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(currentSelectedText).catch(() => {
                // Fallback: execCommand (deprecated but widely supported)
                legacyCopy(currentSelectedText);
            });
        } else {
            legacyCopy(currentSelectedText);
        }
        hideToolbar();
    }

    function legacyCopy(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
        } catch (_e) {
            // Copy failed silently — no uncaught exception
        }
        document.body.removeChild(textarea);
    }

    function onAskAiClick() {
        const selectedText = currentSelectedText;
        if (!selectedText) return;

        // Get full briefing text as context for the AI
        const briefingNarrative = document.getElementById('briefing-narrative');
        const briefingText = briefingNarrative ? briefingNarrative.innerText.trim() : '';

        hideToolbar();
        window.getSelection()?.removeAllRanges();

        const widget = window.chatbotWidget;
        if (!widget) {
            console.warn('ai-briefing-toolbar: chatbotWidget not available');
            return;
        }

        widget.openWithTextDrillIn(selectedText, briefingText);
    }

    /**
     * Position the toolbar 8px above the selection midpoint.
     * Clamps horizontally to stay within viewport.
     */
    function positionAndShow(selection) {
        if (!toolbar || !selection || selection.rangeCount === 0) return;

        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();

        if (!rect || rect.width === 0) return;

        const toolbarRect = toolbar.getBoundingClientRect();
        const toolbarW = toolbarRect.width || 180; // estimate if not visible yet
        const toolbarH = toolbarRect.height || 34;

        const midX = rect.left + rect.width / 2;
        const topY = rect.top - toolbarH - 8 + window.scrollY;

        // Clamp left edge: viewport margin of 8px
        const viewportW = window.innerWidth;
        let leftX = midX - toolbarW / 2;
        leftX = Math.max(8, Math.min(leftX, viewportW - toolbarW - 8));

        toolbar.style.left = leftX + 'px';
        toolbar.style.top = topY + 'px';
        toolbar.classList.add('is-visible');

        // Attach scroll listener once
        if (!scrollListenerAttached) {
            window.addEventListener('scroll', onScroll, { passive: true });
            scrollListenerAttached = true;
        }
    }

    function hideToolbar() {
        if (toolbar) {
            toolbar.classList.remove('is-visible');
        }
        currentSelectedText = '';

        if (scrollListenerAttached) {
            window.removeEventListener('scroll', onScroll);
            scrollListenerAttached = false;
        }
    }

    /**
     * Check if the selection is fully within a container element.
     */
    function isSelectionWithin(selection, container) {
        if (!selection || selection.rangeCount === 0) return false;
        const range = selection.getRangeAt(0);
        return container.contains(range.commonAncestorContainer);
    }

    document.addEventListener('DOMContentLoaded', init);
})();
