import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { TrackballControls } from "three/addons/controls/TrackballControls.js";

export default class Controls {
  constructor(world) {
    this.world = world;
    this.setup();
  }

  setup() {
    // Orbit for smooth rotating
    this.orbitInstance = new OrbitControls(
      this.world.camera.instance,
      this.world.canvas
    );
    this.orbitInstance.autoRotate = true;
    this.orbitInstance.enableRotate = true;
    this.orbitInstance.enableZoom = false;
    this.orbitInstance.enablePan = false;
    this.orbitInstance.enableDamping = true;
    this.orbitInstance.dampingFactor = 0.1;

    // Trackball for smooth zooming
    this.trackballInstance = new TrackballControls(
      this.world.camera.instance,
      this.world.canvas
    );
    this.trackballInstance.noRotate = true;
    this.trackballInstance.noPan = true;
    this.trackballInstance.noZoom = false;
    this.trackballInstance.zoomSpeed = 1.2;
    this.trackballInstance.minDistance = 1;
    this.trackballInstance.maxDistance = 100;
    this.trackballInstance.dynamicDampingFactor = 0.2;
  }

  update() {
    this.orbitInstance.update();
    this.trackballInstance.update();
  }
}
