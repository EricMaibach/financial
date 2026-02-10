# User Story 1.1.5: Brand Messaging and Navigation Update

**Epic:** Phase 1.1 - Homepage Overhaul
**Priority:** High
**Story Points:** 2
**Assigned To:** _Unassigned_

---

## User Story

**As a** SignalTrackers user,
**I want to** see consistent messaging that positions SignalTrackers as a comprehensive macro intelligence platform,
**So that** I understand the full breadth of coverage and don't perceive it as a single-thesis product.

---

## Background

Current messaging and navigation structure inadvertently emphasize the gold/credit divergence thesis. The tagline, page titles, and navigation hierarchy all contribute to the perception problem. This story updates all messaging touchpoints to reinforce our identity as a comprehensive platform.

---

## Acceptance Criteria

### AC1: Update Tagline
- [ ] Add new tagline to navbar: **"Comprehensive macro intelligence for individual investors"**
- [ ] Tagline appears below the logo or as navbar subtitle
- [ ] Tagline is visible on desktop and tablet, hidden on mobile (<768px)
- [ ] Typography: 14px, slightly muted color (#6c757d), regular weight

### AC2: Update Browser Title
- [ ] Change `<title>` tag from "Financial Markets Dashboard" to:
  - Homepage: **"SignalTrackers - Macro Intelligence Platform"**
- [ ] Update meta description to:
  - **"Daily macro intelligence briefings for individual investors. Track credit, equities, rates, safe havens, crypto, and currency markets in one dashboard."**

### AC3: Update Homepage Header
- [ ] Remove or replace: "Real-time tracking of credit markets, equities, safe havens, and economic indicators"
- [ ] New header subtitle: **"Your daily macro intelligence briefing"**
- [ ] Remove any hero text that emphasizes divergence or gold/credit specifically

### AC4: Navigation Restructure
Current navigation:
```
Dashboard | Equity Markets | Safe Havens | Crypto | Rates | Dollar | Divergence | Explorer | Portfolio
```

New navigation:
```
Dashboard | Markets ▼ | Signals | Explorer | Portfolio
             │
             └── Equities
                 Safe Havens
                 Crypto
                 Rates
                 Dollar
```

- [ ] Create "Markets" dropdown menu containing asset class pages
- [ ] Rename "Divergence" nav item to "Signals"
- [ ] Signals link points to `/divergence` (same page, renamed nav item)
- [ ] Keep "Explorer" and "Portfolio" as top-level items
- [ ] Dropdown uses Bootstrap 5 dropdown component

### AC5: Navigation Item Order
- [ ] Order reflects user priority:
  1. Dashboard (home)
  2. Markets (dropdown)
  3. Signals
  4. Explorer
  5. Portfolio (if authenticated)
- [ ] Authenticated user elements (Settings, Logout) remain in right-side dropdown

### AC6: Markets Dropdown Items
Dropdown menu items in order:
1. **Equities** → `/equity`
2. **Safe Havens** → `/safe-havens`
3. **Crypto** → `/crypto`
4. **Rates** → `/rates`
5. **Dollar** → `/dollar`

- [ ] Each item has consistent styling
- [ ] Active page is highlighted in dropdown when on that page
- [ ] Dropdown arrow indicates expandable menu

### AC7: Remove Divergence-Centric Messaging
Audit and update the following:
- [ ] Remove "gold vs. credit" language from hero sections
- [ ] Remove "Crisis Warning Score" prominent displays (move to Signals if needed)
- [ ] Remove "Gold-Implied Spread" as a primary headline metric
- [ ] Update any "track the divergence" copy to "track macro signals"

### AC8: Footer Update (Optional)
- [ ] Update footer text from "Financial Markets Dashboard | Data updated daily" to:
  - **"SignalTrackers | Macro Intelligence for Individual Investors | Data updated daily"**

### AC9: Mobile Navigation
- [ ] Hamburger menu expands to show full navigation
- [ ] Markets submenu expands inline (accordion style) on mobile
- [ ] Tagline hidden on mobile to save space
- [ ] All navigation items accessible within 2 taps

### AC10: Consistent Naming
Ensure consistent terminology across the site:

| Old Term | New Term |
|----------|----------|
| "Financial Markets Dashboard" | "SignalTrackers" |
| "Divergence" (nav) | "Signals" |
| "Divergence metric" | "Gold/Credit Divergence" (one of many signals) |
| "Crisis Score" | Remove or move to Signals section |

---

## Technical Notes

### Files to Modify

| File | Changes |
|------|---------|
| `signaltrackers/templates/base.html` | Navigation restructure, tagline, footer |
| `signaltrackers/templates/index.html` | Header text, title tag, meta description |
| `signaltrackers/static/css/dashboard.css` | Dropdown styles, tagline styles |

### HTML Changes - base.html Navigation

**Before:**
```html
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <a class="navbar-brand" href="/">SignalTrackers</a>
  <!-- Individual nav items -->
  <ul class="navbar-nav">
    <li class="nav-item"><a class="nav-link" href="/">Dashboard</a></li>
    <li class="nav-item"><a class="nav-link" href="/equity">Equity Markets</a></li>
    <li class="nav-item"><a class="nav-link" href="/safe-havens">Safe Havens</a></li>
    <li class="nav-item"><a class="nav-link" href="/crypto">Crypto</a></li>
    <li class="nav-item"><a class="nav-link" href="/rates">Rates</a></li>
    <li class="nav-item"><a class="nav-link" href="/dollar">Dollar</a></li>
    <li class="nav-item"><a class="nav-link" href="/divergence">Divergence</a></li>
    <li class="nav-item"><a class="nav-link" href="/explorer">Explorer</a></li>
  </ul>
</nav>
```

**After:**
```html
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <div class="container-fluid">
    <div class="navbar-brand-container">
      <a class="navbar-brand" href="/">SignalTrackers</a>
      <span class="navbar-tagline d-none d-md-inline">
        Comprehensive macro intelligence for individual investors
      </span>
    </div>

    <button class="navbar-toggler" type="button" data-bs-toggle="collapse"
            data-bs-target="#navbarNav">
      <span class="navbar-toggler-icon"></span>
    </button>

    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav me-auto">
        <li class="nav-item">
          <a class="nav-link" href="/">Dashboard</a>
        </li>

        <!-- Markets Dropdown -->
        <li class="nav-item dropdown">
          <a class="nav-link dropdown-toggle" href="#" role="button"
             data-bs-toggle="dropdown" aria-expanded="false">
            Markets
          </a>
          <ul class="dropdown-menu dropdown-menu-dark">
            <li><a class="dropdown-item" href="/equity">Equities</a></li>
            <li><a class="dropdown-item" href="/safe-havens">Safe Havens</a></li>
            <li><a class="dropdown-item" href="/crypto">Crypto</a></li>
            <li><a class="dropdown-item" href="/rates">Rates</a></li>
            <li><a class="dropdown-item" href="/dollar">Dollar</a></li>
          </ul>
        </li>

        <li class="nav-item">
          <a class="nav-link" href="/divergence">Signals</a>
        </li>

        <li class="nav-item">
          <a class="nav-link" href="/explorer">Explorer</a>
        </li>

        {% if current_user.is_authenticated %}
        <li class="nav-item">
          <a class="nav-link" href="/portfolio">Portfolio</a>
        </li>
        {% endif %}
      </ul>

      <!-- Right side navigation (user menu, etc.) -->
      <ul class="navbar-nav">
        <!-- Existing user menu -->
      </ul>
    </div>
  </div>
</nav>
```

### HTML Changes - index.html Head

```html
<head>
  <title>SignalTrackers - Macro Intelligence Platform</title>
  <meta name="description" content="Daily macro intelligence briefings for individual investors. Track credit, equities, rates, safe havens, crypto, and currency markets in one dashboard.">
  <!-- Other head elements -->
</head>
```

### CSS Additions

```css
/* Navbar Tagline */
.navbar-brand-container {
  display: flex;
  flex-direction: column;
}

.navbar-tagline {
  font-size: 0.75rem;
  color: #adb5bd;
  margin-top: -4px;
}

@media (min-width: 992px) {
  .navbar-brand-container {
    flex-direction: row;
    align-items: baseline;
    gap: 1rem;
  }

  .navbar-tagline {
    margin-top: 0;
  }
}

/* Dropdown Styling */
.dropdown-menu-dark {
  background-color: #343a40;
  border: 1px solid #495057;
}

.dropdown-menu-dark .dropdown-item {
  color: #dee2e6;
}

.dropdown-menu-dark .dropdown-item:hover,
.dropdown-menu-dark .dropdown-item:focus {
  background-color: #495057;
  color: #fff;
}

.dropdown-menu-dark .dropdown-item.active {
  background-color: #0d6efd;
}

/* Mobile accordion for Markets submenu */
@media (max-width: 991px) {
  .navbar-nav .dropdown-menu {
    background-color: transparent;
    border: none;
    padding-left: 1rem;
  }

  .navbar-nav .dropdown-menu .dropdown-item {
    color: rgba(255, 255, 255, 0.55);
    padding: 0.5rem 0;
  }

  .navbar-nav .dropdown-menu .dropdown-item:hover {
    color: rgba(255, 255, 255, 0.75);
    background-color: transparent;
  }
}
```

### JavaScript (if needed)

For mobile accordion behavior (optional enhancement):
```javascript
// Ensure dropdown works on mobile
document.querySelectorAll('.navbar-nav .dropdown').forEach(dropdown => {
  dropdown.addEventListener('show.bs.dropdown', function () {
    if (window.innerWidth < 992) {
      // Mobile: accordion behavior
    }
  });
});
```

---

## Copywriting Reference

### Approved Messaging

**Tagline:**
> Comprehensive macro intelligence for individual investors

**Homepage Subtitle:**
> Your daily macro intelligence briefing

**Meta Description:**
> Daily macro intelligence briefings for individual investors. Track credit, equities, rates, safe havens, crypto, and currency markets in one dashboard.

**Footer:**
> SignalTrackers | Macro Intelligence for Individual Investors | Data updated daily

### Messaging to Remove

- "Track the gold/credit divergence"
- "When gold and credit disagree..."
- "Crisis Warning Score"
- Any single-thesis language
- "Gold-implied spread" as a headline feature

---

## Definition of Done

- [ ] Tagline visible in navbar on desktop/tablet
- [ ] Browser title updated
- [ ] Meta description updated
- [ ] Navigation restructured with Markets dropdown
- [ ] "Divergence" renamed to "Signals" in nav
- [ ] All dropdown links work correctly
- [ ] Mobile navigation works with accordion-style Markets menu
- [ ] Divergence-centric messaging removed from homepage
- [ ] Footer updated
- [ ] Responsive design works on all breakpoints
- [ ] Code is reviewed and approved
- [ ] Manual testing on Chrome, Firefox, Safari
- [ ] No console errors
- [ ] Merged to main branch

---

## Dependencies

- Bootstrap 5 dropdown component (already in use)
- No backend changes required

---

## Notes for Developer

1. The navigation in `base.html` is used across all pages - test that changes don't break other pages
2. Ensure the active page highlighting still works with the new dropdown structure
3. The "Signals" link currently points to `/divergence` - this is intentional; Phase 2.1 will create a new unified Signals page
4. Search the codebase for any other instances of "divergence" or "gold vs credit" in user-facing text
5. Consider SEO implications of title/description changes - these are positive changes for discoverability
6. Test that the mobile hamburger menu still works correctly with the new structure
