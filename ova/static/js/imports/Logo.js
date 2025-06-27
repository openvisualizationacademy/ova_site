import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

export default class Logo {
  constructor(app, options = {}) {
    this.app = app;
    // Define default options
    this.defaults = {
      parent: document.body,
      side: 168,
      margin: 24,
      pixelRatio: 4,
      segments: 6,
      thickness: 1,
      decays: [6, 8, 10, 12],
      ranges: [
        [0, 3],
        [5, 6],
      ],

      wave: false,
      background: false, // color string or false
      needsUpdate: true, // will be toggled to prevent redrawing same logo
      firstTime: true, // enable initial logo to be drawn

      templates: [
        // horizontal
        {
          from: [0, 1, 1, 0], // 0 means ranges[0], 1 means ranges[1]
          to: [0, 0, 1, 1],
        },
        {
          from: [0, 0, 1, 1],
          to: [0, 1, 1, 0],
        },
        // vertical
        {
          from: [0, 0, 1, 1],
          to: [1, 0, 0, 1],
        },
        {
          from: [1, 0, 0, 1],
          to: [0, 0, 1, 1],
        },
      ],
      format: "png", // TODO: Support svg
      palettes: ["YlOrRd", "YlGnBu", "RdPu"],
      grid: false,

      dot: {
        palette: "YlOrRd",
        steps: 255,
        from: {
          coords: [3, 3, 3, 3],
        },
        to: {
          coords: [3, 3, 3, 3],
        },
      },

      line: {
        palette: "YlOrRd",
        steps: 255,
        from: {
          coords: [0, 3, 6, 3],
        },
        to: {
          coords: [0, 3, 6, 3],
        },
      },

      flat: {
        palette: "YlOrRd",
        steps: 255,
        from: {
          coords: [0, 0, 6, 0],
        },
        to: {
          coords: [0, 6, 6, 6],
        },
      },

      original: {
        palette: "YlOrRd",
        steps: 255,
        from: {
          coords: [1, 5 - 0.5, 6, 1 - 0.5],
        },
        to: {
          coords: [0, 3 - 0.5, 5, 6 - 0.5],
        },
      },
    };

    // Copy original symbol as the current one
    this.defaults.current = this.clone(this.defaults.original);

    // Merge provided options with defaults
    Object.assign(this, this.defaults, options);

    // Handle parents provided as CSS selector strings
    if (typeof this.parent === "string") {
      this.parent = document.querySelector(this.parent);
    }

    // Create properties to keep track of time elapsed
    this.lastTime = 0;
    this.deltaTime = 0;

    // Set initial target state
    this.setTarget();

    // Run setup once
    this.setup();

    // Run update for the first time
    window.requestAnimationFrame((ms) => this.update(ms));
  }

  clone(object) {
    if (typeof structuredClone === "function") {
      return structuredClone(object);
    }

    // Polyfill for old iOS
    return JSON.parse(JSON.stringify(this.defaults.original));
  }

  closeEnough(arr1 = this.current.to.coords, arr2 = this.target.to.coords, tolerance = 0.001) {
    if (arr1.length !== arr2.length) return false;
    return arr1.every((val, i) => Math.abs(val - arr2[i]) <= tolerance);
  }

  // Cool transition from Freya Holmér’s Lerp Smoothing talk https://youtu.be/LSNQuFEDOyQ
  expDecay(a, b, decay = 2, deltaTime = this.deltaTime) {
    return b + (a - b) * Math.exp(-decay * deltaTime);
  }

  setupCanvas() {
    // Create canvas element
    this.canvas = document.createElement("canvas");

    // Create drawing context
    this.context = this.canvas.getContext("2d");

    // Define dimensions
    const width = this.side + this.margin * 2;
    this.canvas.width = width * this.pixelRatio;
    this.canvas.height = width * this.pixelRatio;
    this.canvas.style.width = `${width}px`;

    // Add canvas to page
    if (this.parent) {
      this.parent.append(this.canvas);
    } else {
      console.warn('Logo parent element not found!');
    }
  }

  addHoverEvents() {
    // Add hover events, but prevent triggering it immediatly when page loads
    setTimeout(() => {
      this.parent.addEventListener("mouseenter", () => {
        this.resetTarget("flat");
      });
      this.parent.addEventListener("mouseleave", () => {
        this.resetTarget("original");
      });
    }, 100);
  }

  drawLine(x1, y1, x2, y2) {
    this.context.beginPath();
    this.context.moveTo(x1, y1);
    this.context.lineTo(x2, y2);
    this.context.stroke();
  }

  drawGrid() {
    const cell = (this.side / this.segments) * this.pixelRatio;
    const length = this.side * this.pixelRatio;

    // Define stroke thickness
    this.context.lineWidth = 1 * this.pixelRatio;

    // Define stroke color
    this.context.strokeStyle = "#d3d3d3";

    // Draw lines for each segment
    for (let i = 0; i <= this.segments; i++) {
      // Get current column and row
      const point = i * cell;

      // Draw vertical line
      this.drawLine(point, 0, point, length);

      // Draw horizontal line
      this.drawLine(0, point, length, point);
    }
  }

  drawWave() {
    // TEMP: Fixed number of steps
    this.current.steps = 64 - 1;

    // Apply transparency
    this.context.globalAlpha = 0.5;
    this.colorScale = d3.scaleLinear().domain([0, 1]).range([0.2, 0.8]);

    // Draw a line for each step
    for (let i = 0; i <= this.current.steps; i++) {
      // Reset translation
      this.context.resetTransform();

      // Get value between 0 and 1
      const t = (1 / this.current.steps) * i;

      // Define stroke thickness
      this.context.lineWidth =
        (this.thickness * 0.75 + Math.sin(t - this.lastTime * 0.001) * (this.thickness * 0.5)) * this.pixelRatio;

      // Translate to account for offsets and pivot for rotation
      let xOffset = (this.margin + t * this.side) * this.pixelRatio;
      let yOffset = (this.margin + this.side / 2) * this.pixelRatio;
      this.context.translate(xOffset, yOffset);

      // Define base coords
      let coords = [0, this.segments * -0.5, 0, this.segments * 0.5];

      // Decrese length of the lines as they get further away
      coords[1] += (1 - t) * 1;
      coords[3] -= (1 - t) * 1;

      // Adjust those values based on sizes and resolution
      coords = coords.map((coord) => coord * (this.side / this.segments) * this.pixelRatio);

      // Define stroke color
      this.context.strokeStyle = d3[`interpolate${this.target.palette}`](this.colorScale(t));
      this.context.rotate(Math.cos(Math.pow(t, 1) * 1.5 + this.lastTime * 0.0005) * (Math.PI * 0.75));

      // Draw line
      this.drawLine(...coords);
    }

    this.firstTime = false;
  }

  toggleWave() {
    this.wave = !this.wave;
  }

  updateCanvas() {
    // Avoid animating graphics if users prefer reduced motion
    if (!this.firstTime && this.app?.accessibility?.reducedMotion) {
      return;
    }

    // Avoid redrawing logo if it’s already drawn and is very similar to target
    if (!this.wave && !this.firstTime && this.closeEnough()) {
      return;
    }

    // Reset translation
    this.context.resetTransform();

    // Clear canvas
    this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);

    // Pain background with solid color, if provided
    if (this.background) {
      this.context.fillStyle = this.background;
      this.context.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }

    if (this.wave) {
      this.drawWave();
      return;
    }

    // Calculate in-transition “from” and “to” values so they get closer to target
    this.current.from.coords.forEach((a, i, arr) => {
      const b = this.target.from.coords[i];
      arr[i] = this.expDecay(a, b, this.decays[i]);
    });
    this.current.to.coords.forEach((a, i, arr) => {
      const b = this.target.to.coords[i];
      arr[i] = this.expDecay(a, b, this.decays[i]);
    });

    // Calculate in-transition step count so it gets closer to target
    this.current.steps = this.expDecay(this.current.steps, this.target.steps, this.decays[0]);

    // Define interpolator for current “from“ and “to” values
    this.interpolator = d3.interpolate(this.current.from, this.current.to);

    // Define scale for colors scale and range
    this.colorScale = d3.scaleLinear().domain([0, 1]).range([0.8, 0.2]);

    // Account for margins when drawing
    this.context.translate(this.margin * this.pixelRatio, this.margin * this.pixelRatio);
    if (this.grid) {
      this.drawGrid();
    }

    // Draw a line for each step
    for (let i = 0; i <= this.current.steps; i++) {
      // Get value between 0 and 1
      const t = (1 / this.current.steps) * i;

      // Find values for the current step
      const blend = this.interpolator(t);

      // Adjust those values based on sizes and resolution
      blend.coords = blend.coords.map((coord) => coord * (this.side / this.segments) * this.pixelRatio);

      // Define stroke thickness
      this.context.lineWidth = this.thickness * this.pixelRatio;

      // Define stroke color
      this.context.strokeStyle = d3[`interpolate${this.target.palette}`](this.colorScale(t));

      // Draw blended line
      this.drawLine(...blend.coords);
    }

    this.firstTime = false;
  }

  setupSVG() {}

  updateSVG() {}

  setup() {
    if (this.format === "png") this.setupCanvas();
    if (this.format === "svg") this.setupSVG();

    // If device supports hover
    if (window.matchMedia("(hover: hover)").matches) {
      this.addHoverEvents();
    }
  }

  update(ms) {
    // Get time elapsed since last frame (in seconds)
    this.deltaTime = (ms - this.lastTime) / 1000;
    this.lastTime = ms;
    if (this.format === "png") this.updateCanvas();
    if (this.format === "svg") this.updateSVG();

    // Run update for every frame
    window.requestAnimationFrame((ms) => this.update(ms));
  }

  randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  randomItem(array) {
    return array[Math.floor(Math.random() * array.length)];
  }

  resetTarget(settings = "original") {
    this.target = this.defaults[settings];
  }

  // TODO: Randomize colors (and thickness as well?)
  randomizeTarget() {
    // Get random template (regions where a line and start and end)
    const template = this.randomItem(this.templates);
    const options = {
      palette: this.randomItem(this.palettes),
      steps: this.randomInt(255, 255),
      from: {
        coords: template.from.map((i) => this.randomInt(...this.ranges[i])),
        // thickness: this.randomInt(1, 4),
      },
      to: {
        coords: template.to.map((i) => this.randomInt(...this.ranges[i])),
        // thickness: this.randomInt(1, 4),
      },
    };
    this.target = options;
  }

  spin() {}

  autoplay() {
    this.grid = false;
    this.decays = [6, 8, 10, 12].map((decay) => decay * 0.1);
    this.palettes = ["YlOrRd"];
    this.interval = setInterval(() => this.randomizeTarget(), 4000);
  }

  downloadPNG() {
    const dataURL = this.canvas.toDataURL();
    const a = document.createElement("a");
    a.href = dataURL;
    a.download = "logo";
    a.click();
    a.remove();
  }

  download() {
    if (this.format === "png") this.downloadPNG();
    if (this.format === "svg") this.downloadSVG();
  }

  setTarget(options) {
    if (options === undefined) {
      this.resetTarget();
      return;
    }

    // TODO: Apply provided options more carefully
    this.target = options;
  }
}
