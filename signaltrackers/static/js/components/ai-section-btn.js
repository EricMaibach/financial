/**
 * AI Section Buttons — Section-Level Entry Points
 * US-258.2: Ghost pill buttons in section headers that open the chatbot
 * pre-loaded with that section's context.
 *
 * Design decision: opening message is generated client-side instantly so the
 * chatbot panel feels responsive without waiting for an API round-trip.
 * Section context (sectionId) is also passed to the API so the backend
 * system prompt can reference it in follow-up replies.
 */

// Map section IDs to human-readable names and opening messages.
const AI_SECTION_CONTEXTS = {
    'macro-regime-section': {
        name: 'Macro Regime Score',
        opening: "You're looking at the **Macro Regime Score** — a composite signal that classifies the current market environment as Bull, Neutral, Bear, or Recession based on credit conditions, equity breadth, rate dynamics, and volatility. What would you like to explore about the current regime?",
    },
    'briefing-section': {
        name: 'AI Market Briefing',
        opening: "You're reading the **AI Market Briefing** — a daily narrative synthesis of macro conditions, key market moves, and regime implications generated from live economic data. What aspect of today's briefing would you like to dig into?",
    },
    'sector-tone-section': {
        name: 'Sector Management Tone',
        opening: "You're looking at **Sector Management Tone** — derived from FinBERT sentiment analysis of SEC EDGAR 8-K filings across major sectors. It shows how bullish or cautious corporate management teams sound across industries. What would you like to know?",
    },
    'market-conditions': {
        name: 'Market Conditions at a Glance',
        opening: "You're looking at **Market Conditions at a Glance** — six macro dimensions (Credit, Equities, Rates, Volatility, Dollar, Liquidity) each rated with a status badge and AI synthesis. What condition would you like to explore further?",
    },
    'movers-section': {
        name: "What's Moving Today",
        opening: "You're looking at **What's Moving Today** — the top movers across all 50+ tracked metrics, ranked by statistical significance relative to historical percentiles. What's driving the biggest moves right now?",
    },
    'signals-section': {
        name: 'Cross-Market Indicators',
        opening: "You're looking at **Cross-Market Indicators** — key signals like the Yield Curve, VIX term structure, and Gold/Credit divergence that cut across asset classes. What indicator would you like to understand better?",
    },
    'recession-panel-section': {
        name: 'Recession Probability',
        opening: "You're looking at the **Recession Probability** panel — a three-model ensemble (yield curve, credit spread, and leading indicators) that estimates the probability of a recession in the next 12 months. What aspect of this analysis would you like to explore?",
    },
    'trade-pulse-section': {
        name: 'Global Trade Pulse',
        opening: "You're looking at the **Global Trade Pulse** — US goods trade balance data from FRED showing import/export trends and regime-contextualized trade interpretation. What would you like to know about the trade data?",
    },
    'regime-implications': {
        name: 'Regime Implications',
        opening: "You're looking at **Regime Implications** — a structured view of how the current macro regime historically affects different asset classes (equities, fixed income, credit, commodities, real assets, safe havens). What asset class or implication would you like to explore?",
    },
    // Asset pages
    'asset-credit': {
        name: 'Credit Markets',
        opening: "You're on the **Credit Markets** page — tracking high-yield (HY) spreads, investment-grade (IG) spreads, and credit market stress indicators. Credit spreads are a key barometer of risk appetite and financial conditions. What would you like to understand about the current credit environment?",
    },
    'asset-equity': {
        name: 'Equity Markets',
        opening: "You're on the **Equity Markets** page — tracking market structure, sector rotation signals, and key breadth indicators. What aspect of current equity conditions would you like to explore?",
    },
    'asset-rates': {
        name: 'Rates & Fixed Income',
        opening: "You're on the **Rates & Fixed Income** page — tracking Treasury yields, yield curve shape, and inflation expectations. Rate dynamics are foundational to understanding macro conditions. What would you like to dig into?",
    },
    'asset-dollar': {
        name: 'US Dollar',
        opening: "You're on the **US Dollar** page — tracking the Dollar Index (DXY), major currency pairs, and global FX dynamics. Dollar strength affects commodity prices, international equities, and EM markets. What would you like to explore?",
    },
    'asset-crypto': {
        name: 'Crypto / Bitcoin',
        opening: "You're on the **Crypto & Bitcoin** page — tracking macro liquidity indicators and sentiment metrics that historically correlate with Bitcoin's price cycles. What would you like to know about the current macro backdrop for crypto?",
    },
    'asset-safe-havens': {
        name: 'Safe Havens',
        opening: "You're on the **Safe Havens** page — tracking gold, silver, and other defensive assets. Safe haven flows are an important signal of risk appetite and macro stress. What would you like to explore?",
    },
};

/**
 * Open the chatbot pre-loaded with section context.
 * @param {string} sectionId - Key from AI_SECTION_CONTEXTS
 */
function openChatbotWithSection(sectionId) {
    const ctx = AI_SECTION_CONTEXTS[sectionId];
    if (!ctx) {
        console.warn('ai-section-btn: unknown sectionId', sectionId);
        // Fall back to generic open
        if (window.chatbotWidget) window.chatbotWidget.expand();
        return;
    }

    const widget = window.chatbotWidget;
    if (!widget) {
        console.warn('ai-section-btn: chatbotWidget not available');
        return;
    }

    // If already expanded with an active conversation, just open normally —
    // don't clobber an in-progress session.
    if (widget.state === 'expanded') {
        // Graceful: scroll to bottom and focus input
        if (widget.input) widget.input.focus();
        return;
    }

    // Store the section context on the widget so fetchAIResponse can include it
    widget.activeSectionId = sectionId;
    widget.activeSectionName = ctx.name;

    // Open the panel
    widget.expand();

    // Inject the pre-loaded opening message as an AI message (client-side, instant)
    // Use a short delay to let the panel slide in before message appears
    setTimeout(() => {
        widget.addSectionOpeningMessage(ctx.opening);
    }, 150);
}

// Wire up all buttons on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.ai-section-btn[data-section-id]').forEach(btn => {
        btn.addEventListener('click', () => {
            openChatbotWithSection(btn.dataset.sectionId);
        });
    });
});
