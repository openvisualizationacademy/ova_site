import * as THREE from "three";

export default class Pointer {
  constructor(world) {
    this.world = world;

    this.coords = new THREE.Vector2(0, 0);

    this.range = [-1, 1];
    this.diff = this.range[1] - this.range[0];
    this.threshold = this.diff * 0.005;
    this.dragging = false;
    this.down = false;
    this.pointerType = "";

    this.events = {
      pointerdown: "handlePointerDown",
      pointermove: "handlePointerMove",
      pointerup: "handlePointerUp",
    };

    this.setup();
  }

  getCoords(event) {
    const { offsetX, offsetY } = event;
    const { width, height } = this.world;
    const x = (offsetX / width) * this.diff - this.diff / 2;
    const y = -(offsetY / height) * this.diff + this.diff / 2;

    return new THREE.Vector2(x, y);
  }

  handlePointerDown(event) {
    this.down = true;
    this.prevCoords = this.getCoords(event);
    this.coords = this.getCoords(event);

    this.pointerType = event.pointerType;
    console.log(this.pointerType);
  }

  handlePointerMove(event) {
    this.coords = this.getCoords(event);

    if (this.down && !this.dragging) {
      const distance = this.prevCoords.distanceTo(this.coords);

      if (distance > this.threshold) {
        this.dragging = true;

        this.world.controls.orbitInstance.autoRotate = false;
      }
    }
  }

  handlePointerUp(event) {
    this.coords = this.getCoords(event);

    if (this.dragging === false) {
      this.handleClick();
    }

    this.down = false;
    this.dragging = false;
  }

  handleClick() {
    const closest = this.world.raycaster.closest("type", "cat");

    if (closest) {
      alert(closest.userData.title);
    }
  }

  setup() {
    for (let [name, handler] of Object.entries(this.events)) {
      this.world.element.addEventListener(name, (event) => {
        this[handler](event);
      });
    }
  }

  update() {}
}
