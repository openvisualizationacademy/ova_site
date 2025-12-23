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
    this.setupOverview();

    // Remember chapter compact view toggle preference (whether input is checked or not)
    this.setupCompactView();

    // Remember sign in warning (for certificate) state (whether warning was dismissed or not)
    this.setupSignInWarning();

    // Simulate button behavior for `role=button`
    document.addEventListener('keydown', this.simulateButton);
  }

  setupSignInWarning() {
    const description = document.querySelector("#sign-in-description");
    if (!description) return;

    description.addEventListener("click", () => {
      description.classList.remove("warning");
      localStorage.setItem("signInWarning", "false");
    }); 
  }

  setupCompactView() {
    const input = document.querySelector('.switch input[name="compact-view"]');
    if (!input) return;

    input.addEventListener("change", () => {
      localStorage.setItem("compactView", input.checked ? "true" : "false");
    }); 
  }

  setupOverview() {
    const details = document.querySelector(".overview details");
    if (!details) return;

    // If users open or close course overview, store that preference
    details.addEventListener("toggle", () => {
      localStorage.setItem("overviewOpen", details.open ? "true" : "false");
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
