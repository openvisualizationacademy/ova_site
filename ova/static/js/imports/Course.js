import Progress from "./Progress.js";
import Video from "./Video.js";
import Quiz from "./Quiz.js";

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
    this.quiz = new Quiz(this, ".quiz");
  }

  update() {}
}