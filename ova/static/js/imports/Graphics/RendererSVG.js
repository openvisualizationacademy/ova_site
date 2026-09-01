import * as THREE from "three";
import { SVGRenderer } from 'three/addons/renderers/SVGRenderer.js';

export default class RendererSVG {
  constructor(world) {
    this.world = world;

    this.preserveDrawingBuffer = false;
    this.antialias = false;
    this.clearColor = 0x000000;
    this.clearAlpha = 0;

    this.setup();
  }

  get pixelRatio() {
    // return Math.min(window.devicePixelRatio, 2);
    
    // Draw in @4x always
    return 4;
  }

  resize() {
    this.instance.setSize(this.world.width, this.world.height);
    // this.instance.setPixelRatio(this.pixelRatio);
  }

  setup() {
    this.instance = new SVGRenderer({ alpha: true });

    // Add class to SVG element to match style of canvas element
    this.instance.domElement.classList.add("canvas");

    this.world.element.prepend(this.instance.domElement);

    // this.instance = new THREE.WebGLRenderer({
    //   canvas: this.world.canvas,
    //   preserveDrawingBuffer: this.preserveDrawingBuffer,
    //   antialias: this.antialias,
    // });
    this.instance.setClearColor(this.clearColor, this.clearAlpha);

    this.resize();
    // this.update();
  }

  update() {
    this.instance.render(this.world.scene.instance, this.world.camera.instance);

    // Apply background
    if (this.world.app.graphics.background === "transparent") {
      this.world.scene.instance.background = null;
      // Force SVG element to be transparent (SVGRenderer is not accepting alpha in clearColor)
      this.instance.domElement.style.background = "transparent";
    } else {
      this.instance.background = new THREE.Color(this.background);
    }
  }
}
