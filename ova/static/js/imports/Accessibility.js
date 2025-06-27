export default class Accessibility {
  constructor(app) {
    this.app = app;
    this.reducedMotion = false;
    this.queries = {};

    this.setup();
  }

  setup() {
    this.queries.reducedMotion = window.matchMedia(`(prefers-reduced-motion: reduce)`);
    this.reducedMotion = this.queries.reducedMotion.matches;
    this.queries.reducedMotion.addEventListener("change", (event) => (this.reducedMotion = event.matches));
  }
}
