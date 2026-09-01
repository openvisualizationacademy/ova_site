import { CSS2DRenderer } from "three/addons/renderers/CSS2DRenderer.js";

export default class Renderer2D {
  constructor(world) {
    this.world = world;
    this.setup();
  }

  resize() {
    this.instance.setSize(this.world.width, this.world.height);
  }

  setup() {
    this.instance = new CSS2DRenderer({ element: this.world.canvas2D });
    this.resize();
    this.update();
  }

  update() {
    this.instance.render(this.world.scene.instance, this.world.camera.instance);
  }
}
