import * as THREE from "three";
import * as d3 from "d3";

export default class Lines {
  constructor(world) {
    this.world = world;

    // Define how many lines will be drawn (including first, excluding last);
    this.steps = 64 - 1;

    // Will store references to drawn lines
    // this.list = [];

    // Will be populated on update function
    this.list = [];

    // Define whether to use logo shape or random coordinates
    this.mode = "logo"; // logo|random

    this.setup();
  }

  randomizeCoordinates() {
    
    // Get random in from -6 to 6
    const units = 6;
    const randomPosition = d3.randomInt(-units, units + 1);

    // Get an array of two objects
    const randomized = ["first", "last"].map(d => ({
      a: [randomPosition(), randomPosition(), randomPosition()],
      b: [randomPosition(), randomPosition(), randomPosition()]
    }));

    return randomized;
  }

  get lines() {

    // Assume mode is "logo" 
    let extremes = this.world.app.data.lines;
    
    // If mode is "random"
    if (this.mode === "random") {
      // Randomize first and last line coordinates
      extremes = this.randomizeCoordinates();
    }

    return this.blend(this.steps, extremes);
  }

  blend(steps, extremes) {

    // Will be populated with blended (interpolated) lines
    const lines = [];

    // Store starting and ending points for both lines
    const first = extremes.at(0);
    const last = extremes.at(-1);

    // Add first line to list
    lines.push(first)

    // For each step after first
    for (let step = 1; step <= steps; step++) {

      // Will be filled during following for loops
      const blended = {}

      for (let point of ["a", "b"]) {

        // Empty array will be filled below with x, y, z coords
        blended[point] = [];

        // Calculate “in-between” value for x, y, z coordinates
        for (let i = 0; i < 3; i++) { 
          
          const from = first[point][i];
          const to = last[point][i];
          const diff = to - from;
          const increment = diff / steps;

          blended[point][i] = from + increment * step;
        }
      }

      // Add in-between line to array
      lines.push(blended);
    }

    return lines;
  }

  palette(t) {

    if (!this.colorScale) {
      // Make colors avoid extremes (either too light or too dark)
      this.colorScale = d3.scaleLinear().domain([0, 1]).range([0.2, 0.8]);
    }

    return d3.interpolateYlOrRd(this.colorScale(t));
  }

  clearScene() {
    const scene = this.world.scene.instance;

    // Iterate backwards since we're removing while iterating
    while (scene.children.length > 0) {
      const child = scene.children[0];

      // Dispose geometry
      if (child.geometry) {
        child.geometry.dispose();
      }

      // Dispose material(s) - could be an array
      if (child.material) {
        if (Array.isArray(child.material)) {
          child.material.forEach(material => material.dispose());
        } else {
          child.material.dispose();
        }
      }

      scene.remove(child);
    }
}

  renderLines() {

    this.clearScene();

    this.lines.forEach((line, index) => {

      // Get value between 0-1
      const t = index / (this.lines.length - 1);

      const material = new THREE.LineBasicMaterial( { color: this.palette(t) } );
      const points = [];
      points.push( new THREE.Vector3( ...line.a ) );
      points.push( new THREE.Vector3( ...line.b) );
      const geometry = new THREE.BufferGeometry().setFromPoints( points );
      const mesh = new THREE.Line( geometry, material );

      this.world.scene.instance.add( mesh );
    });
  }

  randomize() {
    console.log(this);
    this.mode = "random";
    this.renderLines();
  }

  setup() {
    this.renderLines()
  }

  update() {
    

  }
}
