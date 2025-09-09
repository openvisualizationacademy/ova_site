export default class Accessibility {
  constructor(app) {
    this.app = app;
    this.reducedMotion = false;
    this.queries = {};

    this.setup();
  }

  setup() {
    // Reduced Motion
    this.queries.reducedMotion = window.matchMedia(`(prefers-reduced-motion: reduce)`);
    this.reducedMotion = this.queries.reducedMotion.matches;
    this.queries.reducedMotion.addEventListener("change", (event) => (this.reducedMotion = event.matches));

    // Simulate button behavior for `role=button`
    document.addEventListener('keydown', this.simulateButton)
  }

  // Based on https://stackoverflow.com/a/79664881
  simulateButton(event) {
    const {target, key} = event;
    if (target && target.getAttribute("role") === "button") {
      if (key === 'Enter' || key === ' ') {
        event.preventDefault(); // Prevent scrolling on space
        target.click();
      }
    }
  }
}
