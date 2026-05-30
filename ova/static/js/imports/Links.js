export default class Links {
  constructor(app, selector) {
    this.app = app;
    
    this.writtenContent = document.querySelector(selector);
    this.anchorLinks = document.querySelectorAll('a[href^="#"]')

    this.setup();
  }

  setup() {
    this.dontChangeUrl(this.anchorLinks);
    this.targetBlank(this.writtenContent);
  }

  // Apply target="_blank" to all <a> tags inside element
  targetBlank(element) {

    // If no element is found, stop executing
    if (!element) return

    // Loop over every <a> inside element of course content
    element.querySelectorAll("a").forEach((a) => {
      // Set its target attribute to blank
      a.setAttribute("target", "_blank");
    });
  }

  // Allow anchor navigation, but don’t change url
  dontChangeUrl(links) {

    links.forEach((a) => {
      // Extract element id
      const id = a.hash.replace("#", "");

      // When anchor is clicked
      a.addEventListener("click", (event) => {

        // Prevent default scrolling behavior
        event.preventDefault();

        // Find target element (or default to body)
        const element = id ? document.getElementById(id) : document.body;

        // Scroll to it
        element.scrollIntoView();
      });
    });
  }
}
