import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

export default class People {
  constructor(app, selector, role, property) {
    this.app = app;

    this.element = document.querySelector(selector);
    if (!this.element) return;

    this.dialog = this.element.querySelector('dialog');
    this.role = role;
    this.property = property;

    this.domains = {
      "linkedin.com" : "linkedin",
      "instagram.com" : "instagram",
      "github.com" : "github",
      "medium.com" : "medium",
      "bsky.app" : "bluesky",
      "x.com" : "x",
    }

    this.index = 0;

    this.setup();
  }

  setupCards() {
    this.data.forEach((person, index) => {
      const card = `
      <div role="button" tabindex="0" class="person" data-role="${this.role}" onclick="app.${this.property}.open(${index})">
        <figure>
          ${
            person.photo
              ? `<img class="media" src="/static/media/people/small/${person.photo}" loading="lazy" alt="Profile">`
              : `<div class="media"></div>`
          }
          <figcaption>
            <strong>${person.name}</strong>
            <span class="tagline">${person.tagline}</span>  
          </figcaption>
        </figure>
      </div>
      `;
      this.element.insertAdjacentHTML("beforeend", card);
    });
  }

  async setup() {
    this.data = await d3.json("/static/data/people.json");
    this.data.sort((a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()));
    this.data = this.data.filter((person) => person.role === this.role);
    this.setupCards();
  }

  clear() {
    this.dialog.querySelector('.details').remove()
  }

  getDetails(person) {
    // Overridden by classes that extend People, like Contributors and Instructors 
    return `${person.name}`;
  }

  open(index) {
    this.index = index;

    if (!this.dialog) return;
    this.clear();

    if (this.index < 0) this.index = this.data.length - 1;
    if (this.index > this.data.length - 1) this.index = 0;

    const person = this.data[this.index];

    const details = this.getDetails(person);

    this.dialog.insertAdjacentHTML('beforeend', details);
    this.dialog.showModal();

    // Update dynamically created svg icon placeholders
    this.app.icons.update();
  }

  close() {
    this.dialog.close();
  }

  icon(link) {
    let platform = "internet";

    for (let domain in this.domains) {
      if (link.includes(`//${domain}`) || link.includes(`//www.${domain}`) ) {
        platform = this.domains[ domain ];
        break;
      }
    }

    const svg = this.app.icons.getPlaceholder(platform);
    return svg;
  }

  clean(link) {
    const start = /^(https?:\/\/)?(www\.)?/i;
    const end = /\/$/i;
    return link.replace(start, "").replace(end, "").toLowerCase();
  }

  list(links) {
    return links.map( link => `
      <li>
        <a href="${ link }" target="_blank">
          ${ this.icon(link) }
          ${ this.clean(link) }
        </a>
      </li>
    `).join("");
  }

  update() {}
}
