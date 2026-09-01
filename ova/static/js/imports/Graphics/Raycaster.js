import * as THREE from "three";

export default class Raycaster {
  constructor(world) {
    this.world = world;
    this.matches = [];

    this.setup();
  }

  closest(property, value) {
    if (this.matches.length === 0) {
      return undefined;
    }

    if (property === undefined || value == undefined) {
      const match = this.matches[0];
      return match.object;
    }

    const match = this.matches.find(
      (match) => match.object.userData[property] === value
    );

    if (match) {
      return match.object;
    }

    return undefined;
  }

  setup() {
    this.instance = new THREE.Raycaster();
  }

  updatePosition() {
    this.instance.setFromCamera(
      this.world.pointer.coords,
      this.world.camera.instance
    );
  }

  updateMatches() {
    if (this.world.pointer.dragging) {
      this.matches = [];
      return;
    }

    const { children } = this.world.scene.instance;
    this.matches = this.instance.intersectObjects(children);
  }

  updateHover() {
    const { children } = this.world.scene.instance;
    children.forEach((child) => {
      child.userData.hover = false;
      child.userData.proximity = undefined;
    });

    this.matches.forEach((match, index) => {
      match.object.userData.hover = true;
      match.object.userData.proximity = index;
    });
  }

  update() {
    this.updatePosition();
    this.updateMatches();
    this.updateHover();
  }
}
