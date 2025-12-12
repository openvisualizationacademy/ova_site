export default class Video {
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