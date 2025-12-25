export default class Courses {
  constructor(app, selector) {
    this.app = app;

    this.element = document.querySelector(selector);
    if (!this.element) return;

    this.filters = this.element.querySelector(".filters");
    this.labels = this.filters.querySelectorAll("label[data-tag]");
    this.cards = this.element.querySelector(".cards");
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

  // Pre-calculate how many courses each category contains
  countFilters() {
    const tagCount = {};

    this.courses.forEach((course) => {
      const courseTags = course.dataset.tags.split(",");

      courseTags.forEach((tag) => {
        if (tag in tagCount) {
          tagCount[tag]++;
        } else {
          tagCount[tag] = 1;
        }
      });
    });

    this.labels.forEach(label => {
      const tag = label.dataset.tag;

      if (tag === "all") {
        label.dataset.count = this.courses.length
      } else {
        label.dataset.count = tagCount[tag];
      }
    });
  }

  setup() {
    this.setupFilters();
    this.countFilters();
  }

  update() {}
}