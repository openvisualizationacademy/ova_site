import * as THREE from "three";

export default class Camera {
  constructor(world) {
    this.world = world;

    this.fov = 50;
    this.near = 0.1;
    this.far = 2000;
    this.zoom = 1;
    this.x = 0;
    this.y = 0;
    this.z = 12;
    
    this.frustum = 24;

    this.setup();
  }

  get aspect() {
    return this.world.width / this.world.height;
  }

  get origin() {
    return new THREE.Vector3(0, 0, 0);
  }

  get left() {
    return this.frustum * this.aspect * -0.5;
  }

  get right() {
    return this.frustum * this.aspect * 0.5;
  }

  get top() {
    return this.frustum * 0.5;
  }

  get bottom() {
    return this.frustum * -0.5;
  }

  resize() {
    this.instance.aspect = this.aspect;
    this.instance.updateProjectionMatrix();
  }

  setup() {

    this.instance = new THREE.OrthographicCamera(this.left, this.right, this.top, this.bottom, this.near, this.far);
    // this.instance = new THREE.OrthographicCamera( width / - 2, width / 2, height / 2, height / - 2, 1, 1000); 
    this.instance.position.set(this.x, this.y, this.z);
    this.instance.lookAt(this.origin);
    this.world.scene.instance.add(this.instance);


    // this.instance = new THREE.PerspectiveCamera(
    //   this.fov,
    //   this.aspect,
    //   this.near,
    //   this.far
    // );

    // this.instance.zoom = this.zoom;
    // this.instance.position.set(this.x, this.y, this.z);

    // this.instance.lookAt(this.origin);
    // this.world.scene.instance.add(this.instance);
  }

  resize() {
    this.instance.aspect = this.aspect;
    this.instance.left = this.left;
    this.instance.right = this.right;
    this.instance.top = this.top;
    this.instance.bottom = this.bottom;
    this.instance.updateProjectionMatrix();
  }

  update() {}
}
