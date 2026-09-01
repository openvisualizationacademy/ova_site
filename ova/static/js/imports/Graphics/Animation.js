export default class Animation {
  constructor(world) {
    this.world = world;
    this.setup();
  }

  setup() {}

  update() {}

  // Thanks to Freya Holmér’s Lerp Smoothing https://youtu.be/LSNQuFEDOyQ
  expDecay(a, b, decay = 12, deltaTime = this.world.deltaTime) {
    return b + (a - b) * Math.exp(-decay * deltaTime);
  }
}
