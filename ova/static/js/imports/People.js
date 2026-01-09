import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

export default class People {
  constructor(app, selector) {
    this.app = app;

    this.element = document.querySelector(selector);
    if (!this.element) return;

    this.dialog = this.element.querySelector("dialog");
    this.details = this.dialog.querySelector(".details");

    this.domains = {
      "linkedin.com" : "linkedin",
      "instagram.com" : "instagram",
      "github.com" : "github",
      "medium.com" : "medium",
      "bsky.app" : "bluesky",
      "x.com" : "x",
    }

    this.setup();
  }

  setup() {}

  clear() {
    this.details.replaceChildren();
  }

  open(id) {

    if (!this.dialog) return;
    this.clear();

    const template = this.element.querySelector(`template[data-person="${ id }"]`);

    if (!template) return;

    const clone = document.importNode(template.content, true);

    // Make icon match respective platforms based on domain
    clone.querySelectorAll(".links a").forEach( (a) => {
      a.querySelector("svg[data-icon]").dataset.icon = this.icon(a.href)
    });

    this.details.replaceChildren(clone);

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

    return platform;
  }

  update() {}
}
