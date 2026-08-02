export default class ShowAll {
  constructor(app, selector = ".show-all") {
    this.app = app;
    this.selector = selector;

    this.elements = document.querySelectorAll(this.selector);
    if (this.elements.length === 0) return;

    // Setting whether the cut line should always cut a child element in half
    this.showTopHalf = true;
    this.childrenSelector = `div[role="button"]`;

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

  getChildren(element) {
    // Enable searching for custom children by specifiying a data-attribute in the .show-all element
    const childrenSelector = element.dataset.childrenSelector || this.childrenSelector;

    return element.querySelectorAll(childrenSelector);
  }

  getChildMidpoint(element, max) {
    
    // Use boundings boxes to find the first child that is above the max height
    const elementRect = element.getBoundingClientRect();
    const children = this.getChildren(element);

    // Go from last to first to I can stop as soon as one above is found
    for (let i = children.length - 1; i >= 0; i--) {
      const child = children[i];
      const childRect = child.getBoundingClientRect();
      const distanceFromTop = childRect.top - elementRect.top;

      // If child is above
      if (distanceFromTop < max) {

        // Return the distance from top of the parent to its first half;
        const midpoint = distanceFromTop + childRect.height * .5;

        return midpoint;
      }
    }

    return null;
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

      // If I should cut one element in half
      if (this.showTopHalf) {

        // TODO: Calculate height that cuts one child in half
        const adjustedMax = this.getChildMidpoint(element, max);

        // Limit element height
        element.style.maxHeight = `${adjustedMax}px`;
        return
      }

      // Limit element height
      element.style.maxHeight = `${max}px`;

      // Stop executing further
      return;
    } 

    // Otherwise, remove class to indicate to CSS content is smaller than max height
    this.reset(element);
  }

  handleFocus(child, element) {

    // If element was already expanded, do nothing
    if (element.dataset.wasExpanded === "true") return;

    // Get actual max height from element
    const maxHeight = parseFloat(element.style.maxHeight);

    // If not currently clamped ("initial"), do nothing
    if (isNaN(maxHeight)) return;

    // Get rects to check if element is even partially clipped
    const elementRect = element.getBoundingClientRect();
    const childRect = child.getBoundingClientRect();

    // Distance from top of the element to the bottom of the focused child (uses scroll top to account for automatic vertical scroll when tabbing)
    const distanceToBottom = childRect.bottom - elementRect.top + element.scrollTop

    // If the focused child sits below the visible clamp, expand
    if (distanceToBottom > maxHeight) {
      this.reset(element);
      element.dataset.wasExpanded = "true";
    }
  }

  setup() {

    this.elements.forEach(element => {

      // Create flag to remember if user has already expanded this item
      element.dataset.wasExpanded = "false";

      // Create show more button
      const button = this.button;

      // Define what should happen when button is clicked
      button.addEventListener("click", () => {

        // Switch flag
        element.dataset.wasExpanded = "true"
        
        this.reset(element);
      });

      // Add button to element
      element.append(button);

      // Handle when users tab or focus into any of the element’s children
      this.getChildren(element).forEach(child => {
        child.addEventListener("focus", (event) => this.handleFocus(child, element));
      });

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
