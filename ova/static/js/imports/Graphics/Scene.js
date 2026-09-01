import * as THREE from "three";

export default class Scene {
  constructor(world) {
    this.world = world;
    this.setup();
  }

  setup() {
    this.instance = new THREE.Scene();
  }

  update() {}
}
