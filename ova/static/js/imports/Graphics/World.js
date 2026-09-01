import * as THREE from "three";

import DeltaTime from "./DeltaTime.js";
import Scene from "./Scene.js";
import Camera from "./Camera.js";
import Controls from "./Controls.js";
import Renderer from "./Renderer.js";
import Pointer from "./Pointer.js";
import Renderer2D from "./Renderer2D.js";
import Animation from "./Animation.js";
import Raycaster from "./Raycaster.js";

import Lines from "./Lines.js";

export default class World {
  constructor(app, canvas, canvas2D) {
    this.app = app;
    this.element = document.querySelector(".world");
    this.canvas = this.element.querySelector(canvas);
    this.canvas2D = this.element.querySelector(canvas2D);

    this.setup();
  }

  get width() {
    // return this.element.offsetWidth;
    return this.app.graphics.width;
  }

  get height() {
    // return this.element.offsetHeight;
    return this.app.graphics.height;
  }

  setup() {
    this.deltaTime = new DeltaTime();

    // Basic
    this.scene = new Scene(this);
    this.camera = new Camera(this);
    this.controls = new Controls(this);
    this.renderer = new Renderer(this);
    this.pointer = new Pointer(this);
    this.renderer2D = new Renderer2D(this);
    this.animation = new Animation(this);
    this.raycaster = new Raycaster(this);

    // Custom
    this.lines = new Lines(this);

    // window.addEventListener("resize", () => {
    //   this.resize();
    // });

    requestAnimationFrame((ms) => this.update(ms));
  }

  resize() {
    this.camera.resize();
    this.renderer.resize();
    this.renderer2D.resize();
  }

  update(ms) {
    this.deltaTime.update(ms);

    // Basic
    this.scene.update();
    this.camera.update();
    this.controls.update();
    this.renderer.update();
    this.pointer.update();
    this.renderer2D.update();
    this.animation.update();
    this.raycaster.update();

    // Custom
    this.lines.update();

    requestAnimationFrame((ms) => this.update(ms));
  }
}
