/**
 * StickyMetricSelector Component - JavaScript Behavior
 *
 * Detects when the sticky selector becomes "stuck" to the top of the viewport
 * and applies visual feedback (shadow). Uses IntersectionObserver for efficient
 * scroll detection.
 *
 * Dependencies: None (vanilla JavaScript)
 */

class StickyMetricSelector {
  constructor(element, options = {}) {
    this.element = element;
    this.dropdown = element.querySelector('.sticky-selector__dropdown');

    // Options
    this.options = {
      onMetricChange: options.onMetricChange || null, // Callback when metric changes
      threshold: 1, // IntersectionObserver threshold
    };

    // Validate required elements
    if (!this.dropdown) {
      console.error('StickyMetricSelector: Dropdown element not found');
      return;
    }

    this.init();
  }

  init() {
    // Set up IntersectionObserver to detect stuck state
    this.setupStickyObserver();

    // Set up metric change listener
    if (this.options.onMetricChange) {
      this.dropdown.addEventListener('change', (e) => {
        this.options.onMetricChange(e.target.value);
      });
    }
  }

  /**
   * Set up IntersectionObserver to detect when element becomes stuck
   */
  setupStickyObserver() {
    // Create a sentinel element just above the sticky element
    const sentinel = document.createElement('div');
    sentinel.style.position = 'absolute';
    sentinel.style.top = '0';
    sentinel.style.height = '1px';
    sentinel.style.width = '1px';
    sentinel.style.visibility = 'hidden';
    sentinel.setAttribute('data-sticky-sentinel', 'true');

    // Insert sentinel before the sticky element
    this.element.parentNode.insertBefore(sentinel, this.element);

    // Observe the sentinel
    const observer = new IntersectionObserver(
      ([entry]) => {
        // When sentinel is NOT intersecting, the sticky element is stuck
        const isStuck = !entry.isIntersecting;
        this.element.setAttribute('data-stuck', isStuck);
      },
      {
        threshold: [this.options.threshold],
        rootMargin: '-64px 0px 0px 0px', // Account for fixed nav height
      }
    );

    observer.observe(sentinel);

    // Store references for cleanup
    this.sentinel = sentinel;
    this.observer = observer;
  }

  /**
   * Get the currently selected metric value
   * @returns {string} The selected metric value
   */
  getSelectedMetric() {
    return this.dropdown.value;
  }

  /**
   * Set the selected metric
   * @param {string} metricValue - The metric value to select
   */
  setSelectedMetric(metricValue) {
    this.dropdown.value = metricValue;

    // Trigger change event if callback exists
    if (this.options.onMetricChange) {
      this.options.onMetricChange(metricValue);
    }
  }

  /**
   * Destroy the instance and clean up
   */
  destroy() {
    // Remove observer
    if (this.observer) {
      this.observer.disconnect();
    }

    // Remove sentinel
    if (this.sentinel && this.sentinel.parentNode) {
      this.sentinel.parentNode.removeChild(this.sentinel);
    }

    // Remove event listeners
    if (this.options.onMetricChange) {
      this.dropdown.removeEventListener('change', this.options.onMetricChange);
    }
  }
}

/**
 * Auto-initialize all sticky selectors on the page
 */
function initStickySelectors() {
  const selectors = document.querySelectorAll('.sticky-selector');

  selectors.forEach((selector) => {
    // Check if already initialized
    if (selector.dataset.initialized === 'true') {
      return;
    }

    // Get metric change callback from data attribute (function name)
    let onMetricChange = null;
    const callbackName = selector.dataset.onMetricChange;
    if (callbackName && typeof window[callbackName] === 'function') {
      onMetricChange = window[callbackName];
    }

    // Initialize
    new StickyMetricSelector(selector, {
      onMetricChange: onMetricChange,
    });

    // Mark as initialized
    selector.dataset.initialized = 'true';
  });
}

// Auto-initialize on DOMContentLoaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initStickySelectors);
} else {
  initStickySelectors();
}

// Export for manual initialization if needed
if (typeof module !== 'undefined' && module.exports) {
  module.exports = StickyMetricSelector;
}
