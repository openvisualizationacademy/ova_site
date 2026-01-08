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

  showLoading() {

    // Get element for screen reader announcement
    const polite = this.form.querySelector('[aria-live="polite"]');

    // Ensure it exists
    if (!polite) return;

    // Announce “Submitting” to screen readers
    polite.textContent = "Submitting…";
    // TODO: Add spinner 
    ;
  }
 
  setup() {
    
    // When quiz form gets submitted
    this.form.addEventListener("submit", () => {
      this.showLoading();
      this.enableFields();
    });
  }
}