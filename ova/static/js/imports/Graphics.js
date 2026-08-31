export default class ShowAll {
  constructor(app, selector = ".show-all") {
    this.app = app;
    this.selector = selector;

    this.element = document.querySelector(this.selector);
    if (!this.element) return;

    this.setup();
  }

  setup() {
    console.log(this.element);
  }

  update() {

  }
}
