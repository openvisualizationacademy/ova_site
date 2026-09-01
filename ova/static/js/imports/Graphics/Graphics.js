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

  get steps() {
    // Decrease by 1 to get the exact amount of lines
    return Number(this.data.get("lines")) - 1;
  }

  get thickness() {
    return Number(this.data.get("thickness"));
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

  downloadSVG() {

    // Grab current element
    const element = this.app.world.renderer.instance.domElement;

    // Clone it (for modifying it)
    const svg = element.cloneNode(true);
    
    // Increase SVG support by adding name space
    svg.setAttribute("xmlns", "http://www.w3.org/2000/svg");

    // Remove style (since it only renders the background color in-browser)
    svg.removeAttribute("style");

    // Remove any class (since it has no use outside of this page)
    svg.removeAttribute("class");

    // Create link and trigger it
    const source = new XMLSerializer().serializeToString(svg);
    const blob = new Blob([source], { type: "image/svg+xml;charset=utf-8", });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "ova-graphics.svg";
    link.click();

    // Clear leftovers
    link.remove();
    URL.revokeObjectURL(url);
  }

  setup() {
    // Extract settings from form
    this.getFormData();
    
    // Initialize 3D world
    this.app.world = new World(this.app, ".canvas", ".canvas2D");

    // Set the world to the correct dimensions on page load
    this.update();

    // Update 3D world as form values change
    this.form.addEventListener("input", () => {
      this.update();
    });
  }

  update() {
    // Extract settings from form
    this.getFormData();

    // Apply dimensions
    this.app.world.resize();
    
    // Apply steps
    this.app.world.lines.update();

    // Background is applied in renderer update call
  }
}
