import * as THREE from "three";
import World from "./World.js";

export default class Graphics {
  constructor(app, selector = ".graphics", sources = []) {
    
    this.app = app;
    this.selector = selector;
    
    this.element = document.querySelector(this.selector);
    if (!this.element) return;
    
    this.form = this.element.querySelector("form");
    if (!this.form) return;
    
    // Define drawing options
    this.baseHeight = 720;

    // Load required data (within app class)
    this.app.data.load(sources, () => {
      this.setup();
    });

    // TEMP
    // this.canvas = this.element.querySelector("canvas");
    // this.ctx = this.canvas.getContext("2d");
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
    // Extract settings from form
    this.getFormData();
    
    // Initialize 3D world
    this.app.world = new World(this.app, ".canvas", ".canvas2D");

    // Set the world to the correct dimensions on page load
    this.update();

    // Update 3D world when form is changed
    this.form.addEventListener("change", () => {
      this.update();
    });
  }

  update() {
    // Extract settings from form
    this.getFormData();

    // Apply dimensions
    this.app.world.resize();
    
    // Background is applied in renderer update call
  }
}
