export default class ShowAll {
  constructor(app, selector = ".show-all") {
    this.app = app;

    this.elements = document.querySelectorAll(selector);
    if (this.elements.length === 0) return;

    // Measured in 0-1 as percentage of vh
    this.maxViewportHeight = .8;
    this.maxTolerance = .2;
    
    this.setup();
  }

  get button() {
    // Create button as HTML element
    const button = this.app.utils.html(
      `<button class="button secondary">Show all</button>`
    );

    return button
  }

  reset(element) {
    // Remove class, to hide button and gradient
    element.classList.remove("is-larger");

    // Remove max height
    element.style.maxHeight = "initial";
  }

  checkHeight(element) {

    // If element was already expanded, ignore everything below
    if (element.dataset.wasExpanded === "true") return;
  
    const height = element.scrollHeight;
    const max = window.innerHeight * this.maxViewportHeight;
    const tolerance = window.innerHeight * this.maxTolerance;

    // If content exceeds maximum
    if (height > max + tolerance) {

      // Add class for displaying button and gradient
      element.classList.add("is-larger");

      // Limit element height
      element.style.maxHeight = `${max}px`;

      // Stop executing further
      return;
    } 

    // Otherwise, remove class to indicate to CSS content is smaller than max height
    this.reset(element);
  }

  setup() {

    this.elements.forEach(element => {

      // Create flag to remember if user has already expanded this item
      element.dataset.wasExpanded = "false";

      // Create show more button
      const button = this.button;

      // Define what should happen when button is clicked
      button.addEventListener("click", () => {

        console.log("Clicked button for", element);

        // Switch flag
        element.dataset.wasExpanded = "true"
        
        this.reset(element);
      });

      // Add button to element
      element.append(button);
    });

    // Update on page load
    this.update();

    // Update on resize
    window.addEventListener("resize", () => this.update());
  }

  update() {

    this.elements.forEach(element => {
      this.checkHeight(element);
    });

  }
}
