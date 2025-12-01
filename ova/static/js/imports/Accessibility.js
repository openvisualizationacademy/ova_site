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

    // Remember course overview toggle preference (whether details is open or not)
    this.setupOverviewState();

    // Simulate button behavior for `role=button`
    document.addEventListener('keydown', this.simulateButton);
  }

  setupOverviewState() {
    const details = document.querySelector(".overview details");
    if (!details) return;

    // Moved snippet to HTML template for performance
    // If users have last closed a course overview, keep new ones closed
    // if (localStorage.getItem("overviewState") === "closed") {
    //   details.open = false
    // }

    // If users open or close course overview, store that preference
    details.addEventListener("toggle", () => {
      localStorage.setItem("overviewState", details.open ? "open" : "closed");
    });
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
