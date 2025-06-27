import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

export default class Contributors {
  constructor(selector, role) {
    this.element = document.querySelector(selector) || document.body;
    if (!this.element) return;

    this.role = "contributor";

    this.setup();
  }

  setupCards() {
    this.data.forEach((person) => {
      const card = `
      <a href="${person.links[0]}" target="_blank" class="person" data-role="${this.role}" data-former="${!!person.former}">
        <strong>${person.name}<span class="screen-reader"/>.</span></strong>
        <span class="tagline">${person.tagline}</span> 

        <svg class="icon" data-iconoir="open-new-window" viewBox="0 0 24 24" width="24px" height="24px" stroke-width="2" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M21 3L15 3M21 3L12 12M21 3V9"></path>
          <path d="M21 13V19C21 20.1046 20.1046 21 19 21H5C3.89543 21 3 20.1046 3 19V5C3 3.89543 3.89543 3 5 3H11"></path>
        </svg>
      </a>
      `;
      this.element.innerHTML += card;
    });
  }

  async setup() {
    this.data = await d3.json("./data/people.json");
    this.data.sort((a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()));
    this.data = this.data.filter((person) => person.role === this.role);

    this.setupCards();
  }

  update() {}
}
