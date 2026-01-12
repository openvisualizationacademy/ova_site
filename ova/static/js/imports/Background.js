export default class Background {
  constructor(app, selector) {
    this.app = app;
    
    this.element = document.querySelector(selector);
    if (!this.element) return;

    this.setup();
  }

  setup() {
    // Show background after “page load” to prevent “FOUC” in dark mode (white image background blinks, then CSS invert filter gets applied)
    this.show();
  }

  show() {
    this.element.hidden = false;
  }
}