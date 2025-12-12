class Progress {
  constructor(course) {
    this.course = course;
    this.endpoint = "/api/progress/update/";
    // this.api = `https://ova-blue.azurewebsites.net${ this.endpoint }`;
    this.api = this.endpoint;

    this.setup();
  }

  async updateSegment(segmentId, percent) {

    const payload = {
      segment_id: segmentId,
      percent_watched: percent
    };
    console.log("Payload:", payload);

    const response = await fetch(this.api, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    console.log("Sending data…");

    const data = await response.json();
    console.log(data);
  }

  setup() {}
}

class Video {
  constructor(course, selector) {
    this.course = course;

    this.iframe = course.element.querySelector(selector);
    if (!this.iframe) return;

    this.setup();
  }
  
  setupPlayer() {
    // TODO: Considering adding a retry if the Vimeo API is not yet available
    if (!Vimeo) return;

    this.player = new Vimeo.Player(this.iframe);

    this.player.on("play", (data) => {
      
      // TODO: Add refined logic for determining if user watched video
      const percent = 100;

      // TODO: Consider using scoped variable instead of global one
      if (segmentId === undefined) return;
      this.course.progress.updateSegment(segmentId, percent);
    });
  }

  setup() {    
    this.setupPlayer();
  }
}

export default class Course {
  constructor(app, selector) {
    this.app = app;

    this.element = document.querySelector(selector);
    if (!this.element) return;

    this.setup();
  }
  
  setup() {
    this.progress = new Progress(this);
    this.video = new Video(this, ".vimeo-embed iframe");
  }

  update() {}
}