export default class Quiz {
  constructor(course, selector) {
    this.course = course;

    this.form = this.course.element.querySelector(selector);
    if (!this.form || this.form.tagName != "FORM") return;

    this.setup();
  }

  enableFields() {

    // Enable all form elements so they get sent to backend
    this.form.querySelectorAll(":disabled").forEach((element) => {
      element.disabled = false;
    });
  }
 
  setup() {
    
    // When quiz form gets submitted
    this.form.addEventListener("submit", () => {
      this.enableFields();

      // TODO: Add spinner and announce “Submitting” to screen readers
    });
  }
}