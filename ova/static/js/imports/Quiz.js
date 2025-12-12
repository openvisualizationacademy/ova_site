export default class Quiz {
  constructor(course, selector) {
    this.course = course;

    this.element = this.course.element.querySelector(selector);
    if (!this.element) return;

    this.setup();
  }

  setup() {
    console.log("Quiz class is setup");
  }
}