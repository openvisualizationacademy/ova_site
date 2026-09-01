import * as THREE from "three";

export default class Renderer {
  constructor(world) {
    this.world = world;

    this.preserveDrawingBuffer = false;
    this.antialias = false;
    this.clearColor = 0x000000;
    this.clearAlpha = 0;

    this.setup();
  }

  get pixelRatio() {
    return Math.min(window.devicePixelRatio, 2);
  }

  resize() {
    this.instance.setSize(this.world.width, this.world.height);
    this.instance.setPixelRatio(this.pixelRatio);
  }

  setup() {
    this.instance = new THREE.WebGLRenderer({
      canvas: this.world.canvas,
      preserveDrawingBuffer: this.preserveDrawingBuffer,
      antialias: this.antialias,
    });
    this.instance.setClear;
    this.instance.setClearColor(this.clearColor, this.clearAlpha);

    this.resize();
    // this.update();
  }

  update() {
    this.instance.render(this.world.scene.instance, this.world.camera.instance);
  }
}
