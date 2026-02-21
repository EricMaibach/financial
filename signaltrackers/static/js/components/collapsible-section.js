/**
 * CollapsibleSection Component - JavaScript Behavior
 *
 * Provides progressive disclosure functionality with:
 * - Click/tap toggle
 * - Keyboard support (Space/Enter)
 * - Smooth animations (250ms expand, 200ms collapse)
 * - ARIA attributes for screen readers
 * - Optional localStorage state persistence
 *
 * Dependencies: None (vanilla JavaScript)
 */

class CollapsibleSection {
  constructor(element, options = {}) {
    this.element = element;
    this.header = element.querySelector('.collapsible-section__header');
    this.content = element.querySelector('.collapsible-section__content');
    this.icon = element.querySelector('.collapsible-section__icon');

    // Options
    this.options = {
      persistState: options.persistState || false,
      sectionId: options.sectionId || null,
      expandDuration: 250, // ms
      collapseDuration: 200, // ms
    };

    // Validate required elements
    if (!this.header || !this.content) {
      console.error('CollapsibleSection: Missing required elements (header or content)');
      return;
    }

    this.init();
  }

  init() {
    // Set initial state
    const isExpanded = this.header.getAttribute('aria-expanded') === 'true';

    // Restore saved state if persistence enabled
    if (this.options.persistState && this.options.sectionId) {
      const savedState = localStorage.getItem(`collapsible-${this.options.sectionId}`);
      if (savedState !== null) {
        const shouldExpand = savedState === 'true';
        this.setExpanded(shouldExpand, false); // No animation on init
      }
    }

    // Event listeners
    this.header.addEventListener('click', () => this.toggle());
    this.header.addEventListener('keydown', (e) => this.handleKeydown(e));
  }

  /**
   * Toggle expanded/collapsed state
   */
  toggle() {
    const isExpanded = this.header.getAttribute('aria-expanded') === 'true';
    this.setExpanded(!isExpanded);
  }

  /**
   * Set expanded state
   * @param {boolean} expand - True to expand, false to collapse
   * @param {boolean} animate - Whether to animate the transition (default: true)
   */
  setExpanded(expand, animate = true) {
    // Update ARIA attribute
    this.header.setAttribute('aria-expanded', expand);

    if (expand) {
      this.expand(animate);
    } else {
      this.collapse(animate);
    }

    // Save state if persistence enabled
    if (this.options.persistState && this.options.sectionId) {
      localStorage.setItem(`collapsible-${this.options.sectionId}`, expand);
    }
  }

  /**
   * Expand the section with smooth animation
   */
  expand(animate = true) {
    // Remove hidden attribute
    this.content.hidden = false;

    if (animate) {
      // Get the natural height of the content
      const contentHeight = this.content.scrollHeight;

      // Set max-height to 0 initially
      this.content.style.maxHeight = '0px';
      this.content.style.transition = `max-height ${this.options.expandDuration}ms ease-out`;

      // Force a reflow to ensure the transition works
      this.content.offsetHeight;

      // Animate to natural height
      this.content.style.maxHeight = contentHeight + 'px';

      // Remove max-height after animation completes
      setTimeout(() => {
        this.content.style.maxHeight = '';
        this.content.style.transition = '';
      }, this.options.expandDuration);
    }
  }

  /**
   * Collapse the section with smooth animation
   */
  collapse(animate = true) {
    if (animate) {
      // Get current height
      const contentHeight = this.content.scrollHeight;

      // Set explicit height
      this.content.style.maxHeight = contentHeight + 'px';
      this.content.style.transition = `max-height ${this.options.collapseDuration}ms ease-in`;

      // Force a reflow
      this.content.offsetHeight;

      // Animate to 0
      this.content.style.maxHeight = '0px';

      // Hide after animation completes
      setTimeout(() => {
        this.content.hidden = true;
        this.content.style.maxHeight = '';
        this.content.style.transition = '';
      }, this.options.collapseDuration);
    } else {
      this.content.hidden = true;
    }
  }

  /**
   * Handle keyboard navigation
   * @param {KeyboardEvent} e - The keyboard event
   */
  handleKeydown(e) {
    // Space or Enter key toggles the section
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault(); // Prevent page scroll on Space
      this.toggle();
    }
  }

  /**
   * Destroy the instance and remove event listeners
   */
  destroy() {
    this.header.removeEventListener('click', this.toggle);
    this.header.removeEventListener('keydown', this.handleKeydown);
  }
}

/**
 * Auto-initialize all collapsible sections on the page
 */
function initCollapsibleSections() {
  const sections = document.querySelectorAll('.collapsible-section');

  sections.forEach((section) => {
    // Check if already initialized
    if (section.dataset.initialized === 'true') {
      return;
    }

    // Get section ID from data attribute (for state persistence)
    const sectionId = section.dataset.sectionId;
    const persistState = section.dataset.persistState === 'true';

    // Initialize
    new CollapsibleSection(section, {
      sectionId: sectionId,
      persistState: persistState,
    });

    // Mark as initialized
    section.dataset.initialized = 'true';
  });
}

// Auto-initialize on DOMContentLoaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initCollapsibleSections);
} else {
  initCollapsibleSections();
}

// Export for manual initialization if needed
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CollapsibleSection;
}
