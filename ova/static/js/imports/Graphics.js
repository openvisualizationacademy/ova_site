export default class Graphics {
  constructor(app, selector = ".graphics") {
    this.app = app;
    this.selector = selector;

    this.element = document.querySelector(this.selector);
    if (!this.element) return;

    this.form = this.element.querySelector("form");
    if (!this.form) return;

    // TEMP
    this.canvas = this.element.querySelector("canvas");
    this.ctx = this.canvas.getContext("2d");

    this.baseHeight = 720;

    this.setup();
  }

  get background() {
    return this.data.get("background");
  }

  get ratio() {
    const [w, h] = this.data.get("ratio").split(':').map(Number);
    return h === undefined ? w : w / h;
  }

  get width() {
    return this.baseHeight * this.ratio;
  }

  get height() {
    return this.baseHeight;
  }

  getFormData() {
    this.data = new FormData(this.form);
  }

  setup() {
    this.form.addEventListener("change", () => {
        this.update();
    });

    this.update();
  }

  update() {
    this.getFormData();

    // TEMP
    this.canvas.style.aspectRatio = this.ratio;
    this.canvas.width = this.width;
    this.canvas.height = this.height;

    // TEMP
    this.ctx.fillStyle = this.background;
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    
    // console.log(this.background, this.ratio);
  }
}
