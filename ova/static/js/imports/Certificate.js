export default class Certificate {
  constructor(app, selector) {
    this.app = app;
    
    this.element = document.querySelector(selector);
    if (!this.element) return;

    this.bubbleCount = 16;
    
    this.setup();
  }

  setupBubbles() {

    // Select .bubbles container
    const bubblesContainer = this.element.querySelector(".bubbles");
    
    // Ensure it exists
    if (!bubblesContainer) return;

    for (let i = 0; i < this.bubbleCount; i++) {

      // From .2 to .6rem
      const size = Math.random() * 0.4 + 0.2; 

      // From -200 to 200%
      const translateX = Math.random() * 400 - 200;

      // From 0 to -100%
      const translateY = Math.random() * -100;

      // From 0 to -3s
      const delay = Math.random() * -3;

      // From 3 to 4s
      const duration = Math.random() * 1 + 3;

      // Create bubble as HTML element with random styles
      const bubble = this.app.utils.html(
        `<div
          style="
            width: ${size}rem; 
            height: ${size}rem; 
            translate: ${translateX}% ${translateY}%; 
            animation-delay: ${delay}s;
            animation-duration: ${duration}s;
          "
        ></div>`
      );

      // Add it to the page
      bubblesContainer.append(bubble);
    }
  }
  
  setup() {
    this.setupBubbles();
  }
}