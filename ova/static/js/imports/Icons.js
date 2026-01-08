export default class Icons {
  constructor(app) {
    this.app = app;
    this.selector = '[data-icon]';

    this.cache = {};

    this.update();
  }

  update() {
    this.elements = document.querySelectorAll(this.selector);
    this.elements.forEach(element => this.updatePlaceholder(element));
  }

  async updatePlaceholder(element) {
    // Skip elements that were already built
    if (element.children.length) return;

    // Skip elements that did not specify an icon name
    const name = element.dataset.icon;
    if (!name) return;

    // Update placeholder element with svg node
    const icon = await this.get(name, element);
    if (icon) element.replaceWith(icon);
  }

  async get(name, element) {
    // If icon is not in the cache object
    if (!(name in this.cache)) {
      // Fetch icon svg as string from media/icons/ and store it in cache
      const response = await fetch(`/static/media/icons/${name}.svg`);
      if (!response.ok) return;

      const string = await response.text();
      if (!string) return;

      // Store it in cache
      this.cache[name] = string;
    }

    const string = this.cache[name];
    const svg = this.app.utils.html(string);

    // Add width and height
    svg.setAttribute("width", 24);
    svg.setAttribute("height", 24);

    // Add data-icon
    svg.dataset.icon = name;

    // Keep certain attributes
    svg.ariaHidden = element.ariaHidden;
    svg.ariaLabel = element.ariaLabel;

    return svg;
  }

  getPlaceholder(name, ariaHidden = true) {
    const string = `<svg width="24" height="24" data-icon="${name}" aria-hidden="${ariaHidden}"></svg>`;
    return string
  }
 
}