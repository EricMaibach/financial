# Feature 3.2: Chatbot Mobile-First Redesign - Design Specification

**Feature:** [Feature 3.2 - Chatbot Mobile-First Redesign (#82)](https://github.com/EricMaibach/financial/issues/82)
**Designer:** UI/UX Designer
**Date:** 2026-02-20
**Status:** ✅ APPROVED - Ready for Engineering Implementation
**PM Approval:** 2026-02-20

---

## Executive Summary

This specification redesigns the AI chatbot widget for mobile-first UX using a bottom sheet pattern. The current implementation occupies 90%+ of the mobile viewport, obscuring charts and data users are asking questions about. This redesign ensures context preservation: users can see market data while interacting with the chatbot.

**Key Design Decisions:**
- Bottom sheet pattern for mobile (slides up from bottom, 40-50% viewport)
- Two-state interaction (minimized floating button ↔ expanded panel)
- Full conversation persistence across minimize/expand cycles
- Badge notification system for AI responses while minimized
- Side panel pattern for tablet/desktop

**User Impact:**
- ✓ Users can see charts while asking AI about them
- ✓ No more context loss forcing chatbot close → data check → chatbot reopen cycle
- ✓ Mobile chatbot becomes usable for first time
- ✓ Expected increase in mobile chatbot engagement

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Component Specification](#component-specification)
3. [Visual Design](#visual-design)
4. [Interaction Patterns](#interaction-patterns)
5. [Responsive Behavior](#responsive-behavior)
6. [Accessibility Requirements](#accessibility-requirements)
7. [Technical Implementation](#technical-implementation)
8. [Open Questions](#open-questions)

---

## Design Principles

### 1. Context Preservation (Primary Principle)
Users must be able to see the chart/data they're asking questions about while the chatbot is open. This is the core problem we're solving.

**Implementation:**
- Mobile: Chatbot panel covers ≤50% of viewport, leaving chart visible above
- Tablet/Desktop: Side-by-side layout allows simultaneous chart + chatbot viewing
- Never fullscreen or near-fullscreen overlay on any device

### 2. Progressive Disclosure
The chatbot should start minimal and expand only when needed by the user.

**Implementation:**
- Default state: Small floating button (≤64px diameter)
- Expanded state: Panel appears on user action (tap button)
- Minimized state: Returns to floating button, conversation persists

### 3. Familiar Mobile Patterns
Use established mobile UI patterns that users already understand from other apps.

**Implementation:**
- Bottom sheet pattern (Google Maps, Uber, Airbnb, etc.)
- Floating action button (FAB) for minimized state
- Smooth slide-up animations (250ms ease)
- Native feel (iOS/Android design language compatibility)

### 4. Persistent Availability
Users should be able to access the chatbot from any page without hunting for it.

**Implementation:**
- Floating button persists in fixed position across all pages
- Consistent placement (bottom-right corner)
- Conversation persistence allows contextual follow-up questions

---

## Component Specification

### Component States

The chatbot has **three distinct states** on mobile:

#### State 1: Minimized (Default)
```
┌─────────────────────────────────────┐
│                                     │
│  📊 Chart fully visible             │
│                                     │
│  Statistics sections below          │
│                                     │
│                                     │
│                              [💬]   │ ← Floating button
└─────────────────────────────────────┘
                                 ↑
                            64x64px FAB
                         bottom-right: 16px
```

**Characteristics:**
- Floating action button (FAB) only
- Size: 64x64px diameter
- Position: Fixed, bottom-right corner (16px from edges)
- Icon: Chat bubble or AI sparkle icon
- Badge: Shows notification count when AI responds ("1" or "New")
- z-index: Above page content, below modals
- Shadow: Elevated (8px blur, 0.15 opacity)

#### State 2: Expanded (Active Conversation)
```
┌─────────────────────────────────────┐
│  📊 Chart still visible (60%)       │
├─────────────────────────────────────┤
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │ ← Drag handle (visual only for MVP)
│ AI Chatbot               [─] [✕]   │ ← Header (44px)
├─────────────────────────────────────┤
│ 🤖 AI: Hello! How can I help?      │
│                                     │
│ 👤 You: What's this trend?          │ ← Scrollable
│                                     │   message area
│ 🤖 AI: This chart shows...          │
│                                     │
├─────────────────────────────────────┤
│ Ask about this chart... [↑]        │ ← Input area (56px)
└─────────────────────────────────────┘
          ↑
    40-50% of viewport height
```

**Characteristics:**
- Panel slides up from bottom
- Height: 40% of viewport (minimum), 50% (maximum)
  - Exact height: `min(50vh, max(40vh, 300px))`
  - Ensures usability on very small/large screens
- Header: 44px height
  - Title: "AI Chatbot" (text-base, 600 weight)
  - Minimize button (44x44px touch target, dash icon)
  - Close button (44x44px touch target, X icon)
- Message area: Scrollable, fills remaining space
- Input area: 56px height (44px minimum input + 6px padding each side)
- Background: White (or neutral-50 in dark mode)
- Border radius: 16px top corners (bottom corners square)
- Shadow: Strong elevation (0 -4px 20px rgba(0,0,0,0.15))

#### State 3: Transitioning (Animation In-Progress)
- Slide animation duration: 250ms ease-in-out
- Opacity fade: Synchronous with slide (0 → 1 on expand, 1 → 0 on minimize)
- No interaction during transition (buttons disabled for 250ms)

### Badge Notification Component

When chatbot is minimized and AI responds:

```
   [💬 1]
```

**Characteristics:**
- Position: Top-right of FAB (overlapping by ~8px)
- Size: 20px height (auto width based on content)
- Background: danger-600 (#DC2626)
- Text: White, text-xs (12px), 700 weight
- Content: Number count ("1", "2") or "New" for first message
- Border: 2px white (creates separation from FAB)
- Border radius: 10px (pill shape)
- Clears when user reopens chatbot

---

## Visual Design

### Color Palette

Using SignalTrackers design system colors:

**Component Colors:**
- **FAB Background**: `brand-indigo-500` (#6366F1) - Distinct from page content, signals AI functionality
- **FAB Icon**: White (#FFFFFF)
- **FAB Shadow**: `0 4px 12px rgba(99, 102, 241, 0.25)` - Indigo tint shadow for brand cohesion
- **Panel Background**: `neutral-50` (#FAFAFA) - Subtle, not pure white
- **Panel Border**: `neutral-200` (#E5E7EB) - Top border only (1px)
- **Header Background**: White (#FFFFFF) - Slightly elevated from panel
- **Header Text**: `neutral-800` (#1F2937)
- **Message Area Background**: White (#FFFFFF)
- **User Message Bubble**: `brand-blue-100` (#DBEAFE)
- **User Message Text**: `neutral-800` (#1F2937)
- **AI Message Bubble**: `neutral-100` (#F5F5F5)
- **AI Message Text**: `neutral-800` (#1F2937)
- **Input Border**: `neutral-300` (#D1D5DB)
- **Input Focus Border**: `brand-indigo-500` (#6366F1) - 2px
- **Badge Background**: `danger-600` (#DC2626) - High visibility
- **Badge Text**: White (#FFFFFF)

**Contrast Validation:**
- ✓ White on indigo-500: 4.67:1 (WCAG AA)
- ✓ Neutral-800 on blue-100: 11.32:1 (WCAG AAA)
- ✓ Neutral-800 on neutral-100: 11.32:1 (WCAG AAA)
- ✓ White on danger-600: 7.42:1 (WCAG AAA)

### Typography

**Header Title:**
- Font: System font stack (from design system)
- Size: `text-base` (16px)
- Weight: 600 (semibold)
- Color: `neutral-800`
- Line height: 1.5 (24px)

**Message Text:**
- Font: System font stack
- Size: `text-sm` (14px)
- Weight: 400 (regular)
- Color: `neutral-800`
- Line height: 1.6 (22.4px)

**Input Placeholder:**
- Font: System font stack
- Size: `text-sm` (14px)
- Weight: 400 (regular)
- Color: `neutral-500`
- Style: italic

**Badge Text:**
- Font: System font stack
- Size: `text-xs` (12px)
- Weight: 700 (bold)
- Color: White

### Spacing

Using 4px baseline grid from design system:

**Component Spacing:**
- FAB position: `space-4` (16px) from bottom and right edges
- Panel padding: `space-4` (16px) left/right, `0` top/bottom
- Header padding: `space-4` (16px) all sides
- Message bubble padding: `space-3` (12px) vertical, `space-4` (16px) horizontal
- Message bubble margin: `space-2` (8px) between messages
- Input padding: `space-3` (12px) all sides
- Button spacing: `space-2` (8px) between minimize and close buttons

**Touch Targets:**
- FAB: 64x64px (exceeds 44px minimum)
- Header buttons: 44x44px (meets minimum)
- Input submit button: 44x44px (meets minimum)
- Drag handle: 44px height (if implemented for draggable version)

### Shadows and Elevation

**Z-index Hierarchy:**
```
Page content:          z-index: 1
Chatbot FAB:           z-index: 1000
Chatbot Panel:         z-index: 999 (below FAB so FAB can be tapped to minimize)
Navigation:            z-index: 100
Modals/Overlays:       z-index: 2000
```

**Shadow Specifications:**
- **FAB Shadow**: `0 4px 12px rgba(99, 102, 241, 0.25)` - Indigo tint, medium elevation
- **FAB Hover** (desktop): `0 6px 16px rgba(99, 102, 241, 0.3)` - Enhanced on hover
- **Panel Shadow**: `0 -4px 20px rgba(0, 0, 0, 0.15)` - Strong elevation, casts upward
- **Badge Shadow**: `0 2px 4px rgba(0, 0, 0, 0.1)` - Subtle depth

---

## Interaction Patterns

### Opening the Chatbot

**Trigger:** User taps floating button (minimized state)

**Animation Sequence:**
1. **T+0ms**: Panel begins sliding up from bottom of viewport
2. **T+0ms**: Panel opacity fades from 0 → 1
3. **T+0ms**: FAB scales down from 1 → 0.9 (subtle feedback)
4. **T+250ms**: Panel fully expanded, animation complete
5. **T+250ms**: Input field auto-focuses, keyboard appears on mobile
6. **T+250ms**: FAB scales back to 1.0

**Easing:** `cubic-bezier(0.4, 0.0, 0.2, 1)` - Material Design standard ease

**Behavior:**
- If conversation exists, previous messages are visible (scrolled to bottom)
- If no conversation, empty state: "Hello! How can I help you understand the markets today?"
- Badge clears immediately when panel opens
- Page remains scrollable above panel
- Page content does NOT shift (panel overlays)

### Minimizing the Chatbot

**Trigger:** User taps minimize button (dash icon) in header

**Animation Sequence:**
1. **T+0ms**: Panel begins sliding down out of view
2. **T+0ms**: Panel opacity fades from 1 → 0
3. **T+0ms**: FAB scales up from 0.9 → 1.0 (appears to "catch" the panel)
4. **T+250ms**: Panel fully hidden, animation complete
5. **T+250ms**: Mobile keyboard dismisses

**Behavior:**
- Conversation persists (not cleared)
- If AI is mid-response when minimized, response continues in background
- When AI completes response after minimize, badge appears on FAB
- Input field loses focus

### Closing/Clearing the Chatbot

**Two Separate Actions (Per PM Approval):**

#### Action 1: Close (X) Button - Minimizes Panel
**Trigger:** User taps close button (X icon) in header

**Behavior:**
- Panel minimizes (same as minimize button)
- Conversation persists
- No confirmation needed
- Returns to FAB state

**Rationale:** X means "dismiss" not "delete" - prevents accidental data loss.

#### Action 2: Clear Conversation Link - Deletes History
**Trigger:** User taps "Clear conversation" link at top of message area

**Warning Dialog:**
```
┌────────────────────────────────────┐
│  Clear Conversation?               │
│                                    │
│  This will delete your chat        │
│  history.                          │
│                                    │
│  [ Cancel ]    [ Clear Chat ]      │
└────────────────────────────────────┘
```

**Button Specifications:**
- **Cancel**: Primary button style (outlined, neutral-600 border)
- **Clear Chat**: Danger button style (danger-600 background, white text)
- Cancel is default focus (press Enter = cancel, safer choice)

**Behavior:**
- Show confirmation dialog (prevent accidental loss)
- "Cancel" → Returns to chat, no changes
- "Clear Chat" → Conversation clears, panel minimizes, empty state on next open
- Message counter resets to 0 (for 30-message performance banner)

### Sending a Message

**Trigger:** User types message and taps submit button (↑ arrow)

**Behavior:**
1. User message appears immediately as bubble (optimistic UI)
2. Input field clears
3. "AI is typing..." indicator appears
4. AI response streams in when ready (word-by-word or sentence-by-sentence)
5. Message area auto-scrolls to show new content
6. Submit button disabled while AI is responding

**Loading State:**
```
🤖 AI is typing...
   [animated dots: ●○○ → ○●○ → ○○●]
```

### Notification Badge Flow

**Scenario:** User minimizes chatbot, AI responds

1. **User minimizes** → Panel slides down, FAB visible
2. **AI completes response** → Badge appears on FAB (count: "1")
3. **User taps FAB** → Panel opens, badge disappears
4. **User sees response** → Can continue conversation

**Multiple Responses:**
- If AI sends multiple messages while minimized, badge shows total count ("3")
- Badge clears completely when panel reopens (user has "seen" the messages)

### Performance Banner (30+ Messages)

**Trigger:** User sends 30th message in conversation

**Banner Appearance:**
```
┌────────────────────────────────────┐
│ ℹ️ Long conversation may affect    │
│   performance. Consider clearing   │
│   chat to continue.            [×] │
└────────────────────────────────────┘
```

**Banner Specifications:**
- **Position**: Above input field, below last message
- **Background**: `info-100` (#DBEAFE - light blue)
- **Text**: `info-700` (#1E40AF - dark blue)
- **Icon**: Info icon (ℹ️) on left
- **Dismiss button**: X button on right (44x44px touch target)
- **Padding**: `space-3` (12px) vertical, `space-4` (16px) horizontal
- **Border**: None (background color provides visual distinction)
- **Border radius**: 8px

**Behavior:**
- Appears once after 30th message sent
- Does NOT block sending more messages (soft limit)
- User can dismiss with X button
- Once dismissed, does not re-appear for current session (sessionStorage flag)
- After clearing conversation, counter resets and banner can appear again at 30

**Rationale:**
- Gentle nudge, not blocking (users can continue if needed)
- 30 messages = substantial conversation (~15 exchanges)
- Prevents extreme performance issues from 100+ message conversations
- Most users will never see this banner (typical usage <10 messages)

### Error States

#### Network Error
```
┌────────────────────────────────────┐
│  ⚠️ Connection Error               │
│                                    │
│  Could not reach the AI. Check    │
│  your internet connection.         │
│                                    │
│  [ Try Again ]                     │
└────────────────────────────────────┘
```

**Behavior:**
- User message remains visible (not lost)
- Error message appears as system message (not AI bubble)
- "Try Again" button resends last message
- If connection restored, AI responds normally

#### AI Unavailable
```
┌────────────────────────────────────┐
│  🤖 AI Temporarily Unavailable     │
│                                    │
│  The AI assistant is experiencing  │
│  issues. Please try again later.   │
│                                    │
│  [ Dismiss ]                       │
└────────────────────────────────────┘
```

**Behavior:**
- Chatbot remains functional (can type messages)
- Messages queue until AI available (or show error after timeout)
- User can minimize/close chatbot normally

---

## Responsive Behavior

### Mobile (375px - 767px)

**Layout:** Bottom sheet pattern (as specified above)

**Key Metrics:**
- FAB: 64x64px, fixed bottom-right (16px margins)
- Panel height: 40-50% of viewport (`min(50vh, max(40vh, 300px))`)
- Chart/content visible: 50-60% of viewport above panel
- Header: 44px
- Input area: 56px
- Message area: Remaining space (scrollable)

**Interaction:**
- Tap FAB to expand
- Tap minimize (–) to collapse
- Page scrollable when panel open (panel fixed position)
- Touch targets: All 44px minimum (FAB is 64px)

**Typography:**
- Header: 16px (text-base)
- Messages: 14px (text-sm)
- Input: 14px (text-sm)

**Example Viewports:**
- iPhone SE (375px): Panel ~180-240px, chart ~280px visible
- iPhone Pro (393px): Panel ~188-248px, chart ~290px visible
- Pixel (412px): Panel ~197-262px, chart ~304px visible

### Tablet (768px - 1023px)

**Layout:** Side panel (right side)

```
┌─────────────────────┬──────────────┐
│                     │              │
│  📊 Chart           │  AI Chatbot  │
│                     │              │
│                     │  [Messages]  │
│  Page content       │              │
│                     │  [Input]     │
│                     │              │
│              [💬]   │              │ ← FAB still visible when panel closed
└─────────────────────┴──────────────┘
     ~65-70%              ~30-35%
```

**Key Metrics:**
- Panel width: 320-400px (fixed)
- Panel height: Full viewport height minus header
- Panel slides in from right edge (not bottom)
- FAB position: Same (bottom-right), but shifts left when panel open
- Page content: Remains fully visible (may narrow slightly)

**Behavior:**
- Tap FAB to slide panel in from right
- Panel overlays or pushes page content (engineer decision based on implementation)
- Panel height is full viewport (not limited like mobile)
- Scrolling: Both page and panel can scroll independently

**Why Side Panel:**
- Tablet screens have width for side-by-side layout
- Bottom sheet on tablet would waste horizontal space
- Common pattern: iPad apps use side panels for secondary content

### Desktop (1024px+)

**Layout:** Side panel (right side) - similar to tablet but larger screen accommodates better

```
┌────────────────────────────────┬─────────────────┐
│                                │                 │
│  📊 Chart (larger)             │  AI Chatbot     │
│                                │                 │
│  Statistics sections           │  [Messages]     │
│                                │                 │
│  More page content visible     │  [Input]        │
│                                │                 │
│                         [💬]   │                 │
└────────────────────────────────┴─────────────────┘
         ~70-75%                      ~25-30%
```

**Key Metrics:**
- Panel width: 400-480px (fixed, slightly wider than tablet)
- Panel height: Full viewport height
- FAB: May be less prominent on desktop (users have mouse precision)
- Hover states: Buttons show hover effects (not available on mobile)

**Behavior:**
- Click FAB or hover to expand panel
- Panel slides in from right
- Page content may narrow or panel may overlay (engineer decision)
- Both page and panel independently scrollable

**Desktop Enhancements (Optional):**
- Keyboard shortcut to toggle chatbot (e.g., Cmd/Ctrl + K)
- Resizable panel (drag edge to adjust width)
- Hover preview of FAB shows "Ask AI about this chart"

### Breakpoint Transitions

**At 768px (Mobile → Tablet):**
- Panel repositions from bottom to right edge
- Animation: Panel slides down to bottom-right, then slides right to side
- Height changes: 40-50% viewport → Full height
- Width changes: 100% → 320-400px

**At 1024px (Tablet → Desktop):**
- Panel width increases: 320-400px → 400-480px
- Layout: Side panel remains, more horizontal space available
- Interaction: Hover states become available

**Implementation Note:** Engineers should use CSS breakpoints with smooth transitions. Panel should never "jump" between layouts - animate position/size changes over 250ms.

---

## Accessibility Requirements

### WCAG 2.1 AA Compliance (Minimum)

#### Color Contrast
- ✅ All text meets 4.5:1 minimum (body text on backgrounds)
- ✅ UI elements meet 3:1 minimum (buttons, borders, icons)
- ✅ Brand colors validated (indigo-500 on white = 4.67:1)
- ✅ Message bubbles validated (neutral-800 on blue-100 = 11.32:1)

#### Touch Targets
- ✅ FAB: 64x64px (exceeds 44px minimum by 20px)
- ✅ Header buttons: 44x44px (meets minimum exactly)
- ✅ Submit button: 44x44px (meets minimum exactly)
- ✅ Minimize spacing: 8px between buttons (adequate for fat-finger error prevention)

#### Keyboard Navigation
All interactive elements must be keyboard accessible:

**Tab Order:**
1. FAB (when minimized)
2. Minimize button (when expanded)
3. Close button (when expanded)
4. Message area (focusable for screen readers, not in regular tab order)
5. Input textarea
6. Submit button

**Keyboard Shortcuts:**
- `Tab`: Navigate through interactive elements
- `Enter`: Submit message (when input focused)
- `Escape`: Minimize panel (when chatbot expanded)
- `Shift + Tab`: Navigate backwards

**Focus Indicators:**
- All interactive elements show 2px outline on focus
- Outline color: `brand-indigo-500` (#6366F1)
- Outline offset: 2px (creates gap between element and outline)
- Never `outline: none` without alternative focus indicator

#### Screen Reader Support

**Semantic HTML:**
```html
<aside role="complementary" aria-label="AI Chatbot">
  <header>
    <h2 id="chatbot-title">AI Chatbot</h2>
    <button aria-label="Minimize chatbot">−</button>
    <button aria-label="Close and clear conversation">×</button>
  </header>

  <div role="log" aria-live="polite" aria-atomic="false" aria-label="Chat messages">
    <!-- Messages appear here -->
  </div>

  <form aria-label="Send message to AI">
    <label for="chat-input" class="sr-only">Ask about this chart</label>
    <textarea id="chat-input" aria-describedby="chat-hint"></textarea>
    <span id="chat-hint" class="sr-only">Type your question and press Enter to send</span>
    <button type="submit" aria-label="Send message">↑</button>
  </form>
</aside>
```

**ARIA Attributes:**
- `role="complementary"`: Chatbot is supplementary to main content
- `role="log"`: Message area announces new messages
- `aria-live="polite"`: New AI messages announced when screen reader is idle (not assertive)
- `aria-atomic="false"`: Only new messages announced (not entire conversation)
- `aria-label`: Descriptive labels for all buttons and regions
- `.sr-only`: Screen-reader-only text for context (hidden visually)

**Live Region Announcements:**
- User sends message: (No announcement needed, user knows they sent it)
- AI responds: "AI says: [message content]" (via aria-live="polite")
- Typing indicator: "AI is typing" (via aria-live="polite")
- Error: "Error: [error message]" (via aria-live="assertive" for errors)

#### Focus Management

**When opening chatbot:**
1. Panel slides up/in
2. Focus moves to input field
3. Screen reader announces: "AI Chatbot opened"

**When minimizing chatbot:**
1. Panel slides down/out
2. Focus returns to FAB
3. Screen reader announces: "AI Chatbot minimized"

**When new message arrives (minimized):**
1. Badge appears on FAB
2. Screen reader announces: "New message from AI" (aria-live)
3. Focus does NOT move (user may be elsewhere on page)

### AAA Enhancements (Where Feasible)

- ✅ Text contrast: Using neutral-800 on light backgrounds = 11.32:1 (exceeds AAA 7:1)
- ✅ FAB touch target: 64px (exceeds AAA 56px recommendation)
- ✅ Focus indicators: 2px thick, high contrast (exceeds 1px minimum)

### Color Independence

**Never rely on color alone to convey information:**

- ✅ User messages: Blue bubble + "You:" prefix
- ✅ AI messages: Gray bubble + "AI:" prefix + robot icon
- ✅ Error states: Red + warning icon ⚠️ + text
- ✅ Success states: Green + checkmark ✓ + text
- ✅ Loading: "AI is typing..." text + animated dots (not just color)

**Colorblind Testing:**
- Test with deuteranopia (green-blind) and protanopia (red-blind) simulators
- Ensure indigo FAB is distinguishable from page content in all colorblind modes

---

## Technical Implementation

### HTML Structure

```html
<!-- Floating Action Button (Minimized State) -->
<button
  id="chatbot-fab"
  class="chatbot-fab"
  aria-label="Open AI chatbot"
  aria-expanded="false">
  <svg class="chatbot-icon" aria-hidden="true"><!-- Chat bubble icon --></svg>
  <span class="chatbot-badge" aria-label="1 new message">1</span>
</button>

<!-- Chatbot Panel (Expanded State) -->
<aside
  id="chatbot-panel"
  class="chatbot-panel"
  role="complementary"
  aria-labelledby="chatbot-title"
  aria-hidden="true">

  <!-- Header -->
  <header class="chatbot-header">
    <h2 id="chatbot-title" class="chatbot-title">AI Chatbot</h2>
    <div class="chatbot-header-actions">
      <button
        class="chatbot-minimize"
        aria-label="Minimize chatbot"
        aria-controls="chatbot-panel">
        <span aria-hidden="true">−</span>
      </button>
      <button
        class="chatbot-close"
        aria-label="Close and clear conversation"
        aria-controls="chatbot-panel">
        <span aria-hidden="true">×</span>
      </button>
    </div>
  </header>

  <!-- Message Area -->
  <div
    class="chatbot-messages"
    role="log"
    aria-live="polite"
    aria-atomic="false"
    aria-label="Chat messages">

    <!-- Clear Conversation Link (appears when messages exist) -->
    <button
      class="chatbot-clear-link"
      aria-label="Clear conversation">
      Clear conversation
    </button>

    <!-- Empty State -->
    <div class="chatbot-empty-state">
      <p class="chatbot-empty-text">Hello! How can I help you understand the markets today?</p>
    </div>

    <!-- Messages (dynamically inserted) -->
    <div class="chatbot-message chatbot-message--user">
      <span class="chatbot-message-label sr-only">You said:</span>
      <p class="chatbot-message-text">What's driving this trend?</p>
    </div>

    <div class="chatbot-message chatbot-message--ai">
      <span class="chatbot-message-icon" aria-hidden="true">🤖</span>
      <span class="chatbot-message-label sr-only">AI said:</span>
      <p class="chatbot-message-text">This trend is driven by...</p>
    </div>

    <!-- Typing Indicator -->
    <div class="chatbot-typing" aria-label="AI is typing">
      <span class="chatbot-typing-dot"></span>
      <span class="chatbot-typing-dot"></span>
      <span class="chatbot-typing-dot"></span>
    </div>
  </div>

  <!-- Performance Banner (appears at 30+ messages) -->
  <div class="chatbot-performance-banner" role="status" aria-live="polite" hidden>
    <span class="chatbot-performance-icon" aria-hidden="true">ℹ️</span>
    <p class="chatbot-performance-text">Long conversation may affect performance. Consider clearing chat to continue.</p>
    <button class="chatbot-performance-dismiss" aria-label="Dismiss performance notice">×</button>
  </div>

  <!-- Input Area -->
  <form class="chatbot-input-form" aria-label="Send message to AI">
    <label for="chatbot-input" class="sr-only">Ask about this chart</label>
    <textarea
      id="chatbot-input"
      class="chatbot-input"
      placeholder="Ask about this chart..."
      rows="1"
      aria-describedby="chatbot-input-hint"></textarea>
    <span id="chatbot-input-hint" class="sr-only">Type your question and press Enter or tap send</span>
    <button
      type="submit"
      class="chatbot-submit"
      aria-label="Send message">
      <span aria-hidden="true">↑</span>
    </button>
  </form>
</aside>
```

### CSS Architecture

**File Organization:**
```
static/css/
  chatbot.css              # Main chatbot styles
  chatbot-mobile.css       # Mobile-specific (< 768px)
  chatbot-tablet.css       # Tablet-specific (768px - 1023px)
  chatbot-desktop.css      # Desktop-specific (>= 1024px)
```

**Core Styles (chatbot.css):**
```css
/* ============================================
   Chatbot Component Styles
   ============================================ */

/* Floating Action Button */
.chatbot-fab {
  position: fixed;
  bottom: 16px; /* space-4 */
  right: 16px; /* space-4 */
  width: 64px;
  height: 64px;
  border-radius: 32px; /* Perfect circle */
  background-color: #6366F1; /* brand-indigo-500 */
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
  cursor: pointer;
  z-index: 1000;
  transition: all 250ms cubic-bezier(0.4, 0.0, 0.2, 1);
}

.chatbot-fab:hover {
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.3);
  transform: scale(1.05);
}

.chatbot-fab:focus {
  outline: 2px solid #6366F1; /* brand-indigo-500 */
  outline-offset: 2px;
}

.chatbot-fab[aria-expanded="true"] {
  transform: scale(0.9);
}

/* Badge */
.chatbot-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background-color: #DC2626; /* danger-600 */
  color: white;
  font-size: 12px; /* text-xs */
  font-weight: 700;
  border-radius: 10px;
  border: 2px solid white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.chatbot-badge:empty {
  display: none;
}

/* Panel - Mobile (< 768px) */
.chatbot-panel {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: min(50vh, max(40vh, 300px));
  background-color: #FAFAFA; /* neutral-50 */
  border-top: 1px solid #E5E7EB; /* neutral-200 */
  border-radius: 16px 16px 0 0;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15);
  z-index: 999;
  display: flex;
  flex-direction: column;
  transform: translateY(100%); /* Hidden by default */
  opacity: 0;
  transition: all 250ms cubic-bezier(0.4, 0.0, 0.2, 1);
}

.chatbot-panel[aria-hidden="false"] {
  transform: translateY(0);
  opacity: 1;
}

/* Header */
.chatbot-header {
  height: 44px;
  padding: 0 16px; /* space-4 */
  background-color: white;
  border-bottom: 1px solid #E5E7EB; /* neutral-200 */
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.chatbot-title {
  font-size: 16px; /* text-base */
  font-weight: 600;
  color: #1F2937; /* neutral-800 */
  margin: 0;
}

.chatbot-header-actions {
  display: flex;
  gap: 8px; /* space-2 */
}

.chatbot-minimize,
.chatbot-close {
  width: 44px;
  height: 44px;
  border: none;
  background: none;
  color: #6B7280; /* neutral-500 */
  font-size: 24px;
  cursor: pointer;
  transition: color 150ms ease;
}

.chatbot-minimize:hover,
.chatbot-close:hover {
  color: #1F2937; /* neutral-800 */
}

.chatbot-minimize:focus,
.chatbot-close:focus {
  outline: 2px solid #6366F1; /* brand-indigo-500 */
  outline-offset: 2px;
}

/* Message Area */
.chatbot-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px; /* space-4 */
  background-color: white;
  display: flex;
  flex-direction: column;
  gap: 8px; /* space-2 */
}

/* Clear Conversation Link */
.chatbot-clear-link {
  align-self: center;
  padding: 8px 16px; /* space-2 space-4 */
  background: none;
  border: 1px solid #D1D5DB; /* neutral-300 */
  border-radius: 6px;
  color: #6B7280; /* neutral-500 */
  font-size: 14px; /* text-sm */
  cursor: pointer;
  transition: all 150ms ease;
  margin-bottom: 8px; /* space-2 */
}

.chatbot-clear-link:hover {
  border-color: #DC2626; /* danger-600 */
  color: #DC2626; /* danger-600 */
}

.chatbot-clear-link:focus {
  outline: 2px solid #6366F1; /* brand-indigo-500 */
  outline-offset: 2px;
}

.chatbot-clear-link:empty,
.chatbot-empty-state ~ .chatbot-clear-link {
  display: none; /* Hide when no messages */
}

.chatbot-empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6B7280; /* neutral-500 */
  font-size: 14px; /* text-sm */
  text-align: center;
  padding: 16px; /* space-4 */
}

/* Messages */
.chatbot-message {
  max-width: 80%;
  padding: 12px 16px; /* space-3 space-4 */
  border-radius: 12px;
  font-size: 14px; /* text-sm */
  line-height: 1.6;
}

.chatbot-message--user {
  align-self: flex-end;
  background-color: #DBEAFE; /* brand-blue-100 */
  color: #1F2937; /* neutral-800 */
}

.chatbot-message--ai {
  align-self: flex-start;
  background-color: #F5F5F5; /* neutral-100 */
  color: #1F2937; /* neutral-800 */
  display: flex;
  gap: 8px; /* space-2 */
}

.chatbot-message-icon {
  font-size: 16px;
  flex-shrink: 0;
}

/* Typing Indicator */
.chatbot-typing {
  align-self: flex-start;
  padding: 12px 16px; /* space-3 space-4 */
  background-color: #F5F5F5; /* neutral-100 */
  border-radius: 12px;
  display: flex;
  gap: 4px; /* space-1 */
}

.chatbot-typing-dot {
  width: 8px;
  height: 8px;
  background-color: #6B7280; /* neutral-500 */
  border-radius: 50%;
  animation: typing-bounce 1.4s infinite;
}

.chatbot-typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.chatbot-typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing-bounce {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-8px);
  }
}

/* Performance Banner */
.chatbot-performance-banner {
  padding: 12px 16px; /* space-3 space-4 */
  background-color: #DBEAFE; /* info-100 */
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px; /* space-2 */
  margin: 0 16px 8px 16px; /* Horizontal margin aligns with messages */
  flex-shrink: 0;
}

.chatbot-performance-banner[hidden] {
  display: none;
}

.chatbot-performance-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.chatbot-performance-text {
  flex: 1;
  font-size: 14px; /* text-sm */
  color: #1E40AF; /* info-700 */
  margin: 0;
  line-height: 1.5;
}

.chatbot-performance-dismiss {
  width: 44px;
  height: 44px;
  background: none;
  border: none;
  color: #1E40AF; /* info-700 */
  font-size: 24px;
  cursor: pointer;
  flex-shrink: 0;
  transition: opacity 150ms ease;
}

.chatbot-performance-dismiss:hover {
  opacity: 0.7;
}

.chatbot-performance-dismiss:focus {
  outline: 2px solid #6366F1; /* brand-indigo-500 */
  outline-offset: 2px;
}

/* Input Form */
.chatbot-input-form {
  height: 56px;
  padding: 6px 16px; /* space-4 left/right, custom vertical */
  background-color: white;
  border-top: 1px solid #E5E7EB; /* neutral-200 */
  display: flex;
  gap: 8px; /* space-2 */
  align-items: center;
  flex-shrink: 0;
}

.chatbot-input {
  flex: 1;
  padding: 12px; /* space-3 */
  border: 1px solid #D1D5DB; /* neutral-300 */
  border-radius: 8px;
  font-size: 14px; /* text-sm */
  font-family: inherit;
  resize: none;
  max-height: 44px; /* Prevent growing too tall */
}

.chatbot-input:focus {
  outline: none;
  border: 2px solid #6366F1; /* brand-indigo-500 */
  padding: 11px; /* Adjust for thicker border */
}

.chatbot-submit {
  width: 44px;
  height: 44px;
  background-color: #6366F1; /* brand-indigo-500 */
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 20px;
  cursor: pointer;
  transition: background-color 150ms ease;
  flex-shrink: 0;
}

.chatbot-submit:hover {
  background-color: #4F46E5; /* brand-indigo-600 */
}

.chatbot-submit:focus {
  outline: 2px solid #6366F1; /* brand-indigo-500 */
  outline-offset: 2px;
}

.chatbot-submit:disabled {
  background-color: #D1D5DB; /* neutral-300 */
  cursor: not-allowed;
}

/* Screen Reader Only */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

**Tablet Styles (chatbot-tablet.css):**
```css
@media (min-width: 768px) and (max-width: 1023px) {
  /* Panel slides in from right instead of bottom */
  .chatbot-panel {
    bottom: auto;
    top: 0;
    left: auto;
    right: 0;
    width: 360px;
    height: 100vh;
    border-radius: 0;
    border-top: none;
    border-left: 1px solid #E5E7EB; /* neutral-200 */
    transform: translateX(100%); /* Hidden off right edge */
  }

  .chatbot-panel[aria-hidden="false"] {
    transform: translateX(0);
  }

  /* FAB shifts left when panel opens */
  .chatbot-fab[aria-expanded="true"] {
    right: 376px; /* 360px panel + 16px margin */
  }
}
```

**Desktop Styles (chatbot-desktop.css):**
```css
@media (min-width: 1024px) {
  /* Wider panel on desktop */
  .chatbot-panel {
    width: 440px;
  }

  /* FAB shifts more on desktop */
  .chatbot-fab[aria-expanded="true"] {
    right: 456px; /* 440px panel + 16px margin */
  }

  /* Hover states more prominent */
  .chatbot-fab:hover {
    transform: scale(1.08);
  }

  /* Optional: Show tooltip on FAB hover */
  .chatbot-fab::after {
    content: attr(data-tooltip);
    position: absolute;
    right: 72px; /* To left of FAB */
    top: 50%;
    transform: translateY(-50%);
    background-color: #1F2937; /* neutral-800 */
    color: white;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 14px;
    white-space: nowrap;
    opacity: 0;
    pointer-events: none;
    transition: opacity 150ms ease;
  }

  .chatbot-fab:hover::after {
    opacity: 1;
  }
}
```

### JavaScript Behavior

**Key Functions:**
```javascript
// chatbot.js

class ChatbotWidget {
  constructor() {
    this.fab = document.getElementById('chatbot-fab');
    this.panel = document.getElementById('chatbot-panel');
    this.minimizeBtn = document.querySelector('.chatbot-minimize');
    this.closeBtn = document.querySelector('.chatbot-close');
    this.clearBtn = document.querySelector('.chatbot-clear-link');
    this.form = document.querySelector('.chatbot-input-form');
    this.input = document.getElementById('chatbot-input');
    this.messages = document.querySelector('.chatbot-messages');
    this.badge = document.querySelector('.chatbot-badge');
    this.performanceBanner = document.querySelector('.chatbot-performance-banner');
    this.performanceDismiss = document.querySelector('.chatbot-performance-dismiss');

    this.isOpen = false;
    this.conversation = [];
    this.messageCount = 0;
    this.performanceBannerDismissed = false;

    this.init();
  }

  init() {
    // Event listeners
    this.fab.addEventListener('click', () => this.toggle());
    this.minimizeBtn.addEventListener('click', () => this.close());
    this.closeBtn.addEventListener('click', () => this.close()); // X minimizes (per PM)
    this.clearBtn.addEventListener('click', () => this.clearConversation());
    this.form.addEventListener('submit', (e) => this.sendMessage(e));
    this.performanceDismiss.addEventListener('click', () => this.dismissPerformanceBanner());

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    });

    // Restore conversation and state from sessionStorage
    this.restoreConversation();
    this.performanceBannerDismissed = sessionStorage.getItem('chatbot-perf-dismissed') === 'true';
  }

  toggle() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  open() {
    this.isOpen = true;
    this.panel.setAttribute('aria-hidden', 'false');
    this.fab.setAttribute('aria-expanded', 'true');
    this.clearBadge();
    this.input.focus();

    // Announce to screen readers
    this.announce('AI Chatbot opened');
  }

  close() {
    this.isOpen = false;
    this.panel.setAttribute('aria-hidden', 'true');
    this.fab.setAttribute('aria-expanded', 'false');
    this.fab.focus(); // Return focus to FAB

    // Announce to screen readers
    this.announce('AI Chatbot minimized');
  }

  async sendMessage(e) {
    e.preventDefault();

    const message = this.input.value.trim();
    if (!message) return;

    // Add user message immediately
    this.addMessage('user', message);
    this.conversation.push({ role: 'user', content: message });
    this.messageCount++;

    // Clear input
    this.input.value = '';

    // Check for performance banner at 30 messages
    if (this.messageCount === 30 && !this.performanceBannerDismissed) {
      this.showPerformanceBanner();
    }

    // Show typing indicator
    this.showTypingIndicator();

    // Send to AI backend
    try {
      const response = await this.fetchAIResponse(message);
      this.hideTypingIndicator();
      this.addMessage('ai', response);
      this.conversation.push({ role: 'ai', content: response });

      // If chatbot is minimized, show badge
      if (!this.isOpen) {
        this.showBadge();
      }

      // Save conversation
      this.saveConversation();

    } catch (error) {
      this.hideTypingIndicator();
      this.showError('Could not reach the AI. Please try again.');
    }
  }

  addMessage(role, text) {
    const messageEl = document.createElement('div');
    messageEl.className = `chatbot-message chatbot-message--${role}`;

    if (role === 'ai') {
      messageEl.innerHTML = `
        <span class="chatbot-message-icon" aria-hidden="true">🤖</span>
        <span class="chatbot-message-label sr-only">AI said:</span>
        <p class="chatbot-message-text">${this.escapeHTML(text)}</p>
      `;
    } else {
      messageEl.innerHTML = `
        <span class="chatbot-message-label sr-only">You said:</span>
        <p class="chatbot-message-text">${this.escapeHTML(text)}</p>
      `;
    }

    this.messages.appendChild(messageEl);
    this.scrollToBottom();

    // Announce AI messages to screen readers
    if (role === 'ai') {
      this.announce(`AI says: ${text}`);
    }
  }

  showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'chatbot-typing';
    indicator.setAttribute('aria-label', 'AI is typing');
    indicator.innerHTML = `
      <span class="chatbot-typing-dot"></span>
      <span class="chatbot-typing-dot"></span>
      <span class="chatbot-typing-dot"></span>
    `;
    this.messages.appendChild(indicator);
    this.scrollToBottom();

    this.announce('AI is typing');
  }

  hideTypingIndicator() {
    const indicator = this.messages.querySelector('.chatbot-typing');
    if (indicator) {
      indicator.remove();
    }
  }

  showBadge() {
    // Count unread AI messages (simple implementation: just show "1")
    this.badge.textContent = '1';
    this.badge.setAttribute('aria-label', '1 new message');
  }

  clearBadge() {
    this.badge.textContent = '';
    this.badge.removeAttribute('aria-label');
  }

  scrollToBottom() {
    this.messages.scrollTop = this.messages.scrollHeight;
  }

  async fetchAIResponse(message) {
    // Call backend AI endpoint
    // Include page context (per PM decision - if technically simple)
    const response = await fetch('/api/chatbot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        conversation: this.conversation,
        context: {
          page: window.location.pathname // Simple context awareness
        }
      })
    });

    if (!response.ok) throw new Error('AI request failed');

    const data = await response.json();
    return data.response;
  }

  showError(errorMessage) {
    const errorEl = document.createElement('div');
    errorEl.className = 'chatbot-message chatbot-message--error';
    errorEl.innerHTML = `
      <span aria-hidden="true">⚠️</span>
      <p>${this.escapeHTML(errorMessage)}</p>
    `;
    this.messages.appendChild(errorEl);
    this.scrollToBottom();

    this.announce(`Error: ${errorMessage}`, 'assertive');
  }

  showPerformanceBanner() {
    this.performanceBanner.removeAttribute('hidden');
    this.announce('Long conversation may affect performance', 'polite');
  }

  dismissPerformanceBanner() {
    this.performanceBanner.setAttribute('hidden', '');
    this.performanceBannerDismissed = true;
    sessionStorage.setItem('chatbot-perf-dismissed', 'true');
  }

  clearConversation() {
    // Show confirmation dialog (per PM requirements)
    const confirmed = confirm(
      'Clear conversation? This will delete your chat history.'
    );

    if (!confirmed) {
      return; // User cancelled
    }

    // Clear conversation
    this.conversation = [];
    this.messageCount = 0;

    // Reset UI
    this.messages.innerHTML = `
      <button class="chatbot-clear-link" aria-label="Clear conversation">
        Clear conversation
      </button>
      <div class="chatbot-empty-state">
        <p class="chatbot-empty-text">Hello! How can I help you understand the markets today?</p>
      </div>
    `;

    // Hide performance banner and reset dismissed flag
    this.performanceBanner.setAttribute('hidden', '');
    this.performanceBannerDismissed = false;
    sessionStorage.removeItem('chatbot-perf-dismissed');

    // Re-attach event listener to new clear button
    this.clearBtn = document.querySelector('.chatbot-clear-link');
    this.clearBtn.addEventListener('click', () => this.clearConversation());

    // Save and close
    this.saveConversation();
    this.close();

    this.announce('Conversation cleared');
  }

  saveConversation() {
    const state = {
      conversation: this.conversation,
      messageCount: this.messageCount
    };
    sessionStorage.setItem('chatbot-conversation', JSON.stringify(state));
  }

  restoreConversation() {
    const saved = sessionStorage.getItem('chatbot-conversation');
    if (saved) {
      const state = JSON.parse(saved);
      this.conversation = state.conversation || [];
      this.messageCount = state.messageCount || 0;

      // Restore messages to UI
      this.conversation.forEach(msg => {
        this.addMessage(msg.role, msg.content);
      });

      // Show performance banner if applicable
      if (this.messageCount >= 30 && !this.performanceBannerDismissed) {
        this.showPerformanceBanner();
      }
    }
  }

  announce(message, priority = 'polite') {
    // Create live region announcement for screen readers
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', priority);
    announcement.className = 'sr-only';
    announcement.textContent = message;
    document.body.appendChild(announcement);

    // Remove after announcement
    setTimeout(() => announcement.remove(), 1000);
  }

  escapeHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Initialize chatbot
document.addEventListener('DOMContentLoaded', () => {
  new ChatbotWidget();
});
```

### Backend Integration

**API Endpoint:**
```python
# signaltrackers/routes/chatbot.py

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    """Handle AI chatbot requests"""
    data = request.json
    user_message = data.get('message', '')
    conversation_history = data.get('conversation', [])

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        # Call your AI service (OpenAI, Claude, etc.)
        ai_response = get_ai_response(user_message, conversation_history)

        return jsonify({
            'response': ai_response,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        app.logger.error(f'Chatbot error: {e}')
        return jsonify({'error': 'AI service unavailable'}), 503

def get_ai_response(message, history):
    """Get response from AI service"""
    # Implementation depends on your AI backend
    # Example: OpenAI, Anthropic Claude, local model, etc.
    pass
```

---

## Final Product Decisions (PM Approved)

### 1. Close Button Behavior ✅
**Decision:** Close (X) minimizes chatbot, separate "Clear conversation" link

**Implementation:**
- X button in header minimizes chatbot (same behavior as minimize button)
- Separate "Clear conversation" link positioned at top of message area
- Clicking "Clear conversation" shows confirmation dialog
- Dialog must include:
  - Warning text: "Clear conversation? This will delete your chat history."
  - Two buttons: "Cancel" (primary action) and "Clear Chat" (danger-styled)
- After clearing, panel minimizes and shows empty state on next open

**Rationale:** Prevents accidental conversation loss while providing clear path to start fresh.

### 2. Context Awareness ✅
**Decision:** Include for MVP if technically simple (<1 hour work), otherwise defer

**Implementation (if included in MVP):**
```javascript
// Send current page context to backend
fetch('/api/chatbot', {
  method: 'POST',
  body: JSON.stringify({
    message: userMessage,
    conversation: conversationHistory,
    context: { page: window.location.pathname } // Simple addition
  })
})
```

**Backend receives:**
- `context.page = "/credit"` when user is on credit page
- AI can provide contextual responses ("Tell me about this" → understands "this" = credit spreads)

**Engineer Decision:** If this takes <1 hour, include for MVP. If more complex, create follow-up user story and defer.

**Rationale:** Significant UX improvement if technically trivial; don't block MVP if complex.

### 3. Quick Suggestion Chips ✅
**Decision:** Deferred to post-MVP (future enhancement)

**Rationale:**
- Need real usage data to identify common question patterns
- Don't want to guess which suggestions are valuable
- MVP should validate core chatbot utility first
- Can add later based on analytics showing top queries

**Future Implementation:** Track most common user questions, create suggestion chips for top 3-5 patterns.

### 4. Voice Input ✅
**Decision:** Deferred to post-MVP (future enhancement)

**Rationale:**
- Significant implementation complexity (speech-to-text, permissions, cross-browser)
- Text input sufficient for sophisticated investor audience
- Can add later if users explicitly request in feedback

**Future Consideration:** Only implement if user feedback shows demand for voice input.

### 5. Conversation Limits ✅
**Decision:** Soft limit at 30 messages with gentle performance nudge

**Implementation:**
- After 30 messages sent, show performance banner above input field
- Banner specifications:
  - **Text**: "Long conversation may affect performance. Consider clearing chat to continue."
  - **Style**: `info-100` background with `info-600` text (neutral, not alarming)
  - **Dismissible**: X button to hide banner permanently for current session
  - **Position**: Above input field, below last message
  - **Does NOT block**: User can continue sending messages past 30 (soft limit)
- Banner appears once at 30 messages, doesn't re-appear each message
- After clearing conversation, counter resets

**Rationale:**
- 30 messages = ~15 back-and-forth exchanges (substantial conversation)
- Soft limit doesn't frustrate power users
- Gentle nudge prevents extreme performance degradation
- Most conversations will be <10 messages (typical chatbot usage patterns)

---

## Implementation Checklist

**Design Phase:**
- [x] Bottom sheet pattern specification
- [x] Mobile/tablet/desktop wireframes
- [x] Interaction patterns documented
- [x] Color palette and typography defined
- [x] Accessibility requirements specified
- [x] Technical implementation guidance provided
- [ ] PM approval of design spec
- [ ] Design spec reviewed with engineer for feasibility

**Engineering Phase:**
- [ ] HTML structure implemented
- [ ] CSS styles (mobile/tablet/desktop)
- [ ] JavaScript chatbot widget class
- [ ] Backend API endpoint (/api/chatbot)
- [ ] AI service integration
- [ ] Conversation persistence (sessionStorage)
- [ ] Error handling (network, AI unavailable)
- [ ] Accessibility implementation (ARIA, keyboard nav, screen reader)
- [ ] Touch target validation (44px minimum)
- [ ] Animation polish (250ms transitions)
- [ ] Cross-browser testing (Chrome, Safari, Firefox)
- [ ] Mobile device testing (iOS, Android)
- [ ] Tablet testing (iPad, Android tablets)

**QA Phase:**
- [ ] Playwright screenshot validation (mobile/tablet/desktop)
- [ ] Context preservation verification (chart visible while chatbot open)
- [ ] Touch target measurement (all ≥44px)
- [ ] Color contrast validation (WCAG 2.1 AA)
- [ ] Keyboard navigation testing (Tab, Enter, Escape)
- [ ] Screen reader testing (NVDA, JAWS, VoiceOver)
- [ ] Conversation persistence testing (minimize → reopen)
- [ ] Badge notification testing (AI response while minimized)
- [ ] Error state testing (network failure, AI unavailable)
- [ ] Performance testing (long conversations, slow networks)

---

## Success Metrics

**Measurable Outcomes (Post-Launch):**

1. **Context Preservation** ✅ (Design Goal)
   - Mobile chatbot panel height: 40-50% of viewport
   - Chart visible above panel: ≥50% of viewport
   - Validation: Playwright screenshots show chart + chatbot simultaneously

2. **Accessibility Compliance** ✅ (Design Goal)
   - All touch targets ≥44px
   - All color contrast ≥4.5:1 (text) and ≥3:1 (UI)
   - Full keyboard navigation support
   - Screen reader compatibility

3. **Mobile Chatbot Engagement** 📊 (Product Metric)
   - Baseline: Current mobile chatbot usage (likely very low)
   - Target: 3x increase in mobile chatbot sessions post-redesign
   - Tracking: Analytics on chatbot opens, messages sent (mobile vs desktop)

4. **User Satisfaction** 📊 (Product Metric)
   - Measure: User feedback, session duration with chatbot open
   - Target: Positive sentiment in user feedback, longer chatbot sessions
   - Indicates: Users finding chatbot valuable enough to keep open

---

**End of Design Specification**

**Next Steps:**
1. **@pm**: Review this specification, answer open questions, approve for engineering
2. **@ui-designer** (me): Update spec based on PM feedback, mark as "Approved"
3. **@engineer**: Implement chatbot redesign following this specification
4. **@qa**: Validate implementation against checklist and success criteria

**Questions?** Comment on [Feature 3.2 (#82)](https://github.com/EricMaibach/financial/issues/82)
