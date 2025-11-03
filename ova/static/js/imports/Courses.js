export default class Courses {
  constructor(app, selector) {
    this.app = app;

    this.element = document.querySelector(selector);
    if (!this.element) return;

    this.filters = this.element.querySelector(".filters");
    this.cards = this.element.querySelector(".cards");
    this.tags = this.element.querySelector(".tag");
    this.courses = this.cards.querySelectorAll(".course");

    this.setup();
  }

  setupFilters() {
    this.filters.addEventListener("input", (event) => {
      const selectedTags = [...this.filters.elements.tag].filter((input) => input.checked).map((input) => input.value);
      this.filterCards(selectedTags);
    });
  }

  filterCards(selectedTags) {
    if (selectedTags.length === 0 || selectedTags[0] === "all") {
      console.log("Show all");
      this.courses.forEach((course) => {
        course.hidden = false;
      });
      return;
    }

    this.courses.forEach((course) => {
      const courseTags = course.dataset.tags.split(",");
      const isMatch = selectedTags.some((tag) => courseTags.includes(tag));
      course.hidden = !isMatch;
    });
  }

  setup() {
    this.setupFilters();
  }

  update() {}
}