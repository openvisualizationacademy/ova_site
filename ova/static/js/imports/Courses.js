export default class Courses {
  constructor(app, selector) {
    this.app = app;

    this.element = document.querySelector(selector);
    if (!this.element) return;

    this.filters = this.element.querySelector(".filters");
    this.labels = this.filters.querySelectorAll("label[data-tag]");
    this.cards = this.element.querySelector(".cards");
    this.courses = this.cards.querySelectorAll(".course");
    this.count = this.element.querySelector(".course-count");

    this.setup();
  }

  // Get selected tag filter (rely on HTMLFormElement)
  get tag() {
    return this.filters.elements.tag.value;
  }

  // Check if default filter is selected
  get allTags() {
    return this.tag === "all";
  }

  // Get selected topic option (rely on HTMLFormElement).
  // The topic select is only rendered when topics exist; fall back to "all".
  get topic() {
    const select = this.filters.elements.topic;
    return select ? select.value : "all";
  }

  // Check if default filter is selected
  get allTopics() {
    return this.topic === "all";
  }

  setupFilters() {

    // When form fields change
    this.filters.addEventListener("change", (event) => {
      this.filterCards(this.tag, this.topic);
      this.countCourses();
    });
  }

  filterCards(tag, topic) {

    const allTags = this.allTags;
    const allTopics = this.allTopics;

    // If showing all
    if (allTags && allTopics) {
      this.courses.forEach((course) => {
        course.hidden = false;
      });
      return;
    }

    this.courses.forEach((course) => {
      const courseTags = course.dataset.tags.split(";");
      const courseTopics = course.dataset.topics.split(";");

      const hasTag = allTags || courseTags.includes(tag);
      const hasTopic = allTopics || courseTopics.includes(topic);

      // Show course if it matches both filters
      if (hasTag && hasTopic) {
        course.hidden = false;
        return;
      }

      // Otherwise, hide it
      course.hidden = true;
    });
  }

  // Check how many course items are visible and display total
  countCourses() {
    let count = 0;
    this.courses.forEach(course => {
      if (!course.hidden) count++;
    });

    this.count.textContent = `
      ${count === 0 ? 'No' : count}
      ${count === 1 ? 'course' : 'courses' }
      found`;

    // Add empty class if count is 0, remove it otherwise
    this.cards.classList.toggle("empty", count === 0);

    // const tag = (["Lecture", "Tutorial"].includes(this.tag) ? `${this.tag}s` : this.tag).toLowerCase();
    // const topic = this.topic.toLowerCase();

    // if (this.allTags && this.allTopics) {
    //   this.count.textContent = `${count} ${count === 1 ? 'course' : 'courses' } found`;
    //   return;
    // }

    // if (!this.allTags && !this.allTopics) {
    //   this.count.textContent = `${count} ${count === 1 ? 'course covers' : 'courses cover' } ${topic} ${tag}`;
    //   return;
    // }

    // if (this.allTags) {
    //   this.count.textContent = `${count} ${count === 1 ? 'course covers' : 'courses cover' } ${topic}`;
    //   return;
    // }

    // if (this.allTopics) {
    //   this.count.textContent = `${count} ${count === 1 ? 'course covers' : 'courses cover' } ${tag}`;
    //   return;
    // } 
  }

  setup() {
    this.setupFilters();
  }

  update() {}
}