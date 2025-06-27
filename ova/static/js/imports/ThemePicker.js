export default class ThemePicker {
  constructor(selector) {
    this.pictures = document.querySelectorAll('picture:has(source[media*="prefers-color-scheme"]') || [];
    this.element = document.querySelector(selector);

    this.light = this.element.querySelector('input[value="light"]');
    this.dark = this.element.querySelector('input[value="dark"]');
    this.inputs = [this.light, this.dark];
    this.system = "light";
    this.tempClass = "theme-adjusted";
    this.setup();
  }

  get checkedInput() {
    return this.inputs.find((input) => input.checked);
  }

  get user() {
    return this.checkedInput.value;
  }

  get matchesSystem() {
    return this.system === this.user;
  }

  setup() {
    this.mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    this.system = this.mediaQuery.matches ? "dark" : "light";
    this.dark.checked = this.mediaQuery.matches;
    this.light.checked = !this.mediaQuery.matches;
    this.mediaQuery.addEventListener("change", (event) => {
      this.system = this.mediaQuery.matches ? "dark" : "light";
      this.dark.checked = event.matches;
      this.light.checked = !event.matches;
      this.update();
    });
    this.inputs.forEach((input) => {
      input.addEventListener("change", (event) => {
        this.update();
      });
    });
  }

  addTemporaryImage(picture) {
    console.log("user theme is", this.user);

    const themeSrc = picture.querySelector(`source[media*="${this.user}"`)?.srcset;
    const pictureImg = picture.querySelector("img");

    console.log(themeSrc, pictureImg);

    if (!themeSrc || !pictureImg) return;

    const img = pictureImg.cloneNode();
    img.classList.add(this.tempClass);
    img.src = themeSrc;

    picture.after(img);
    picture.hidden = true;
  }

  removeTemporaryImage(picture) {
    if (!picture.nextElementSibling?.classList.contains(this.tempClass)) return;

    picture.nextElementSibling.remove();
    picture.hidden = false;
  }

  updatePictures() {
    const { matchesSystem } = this;
    this.pictures.forEach((picture) => {
      if (matchesSystem) {
        this.removeTemporaryImage(picture);
      } else {
        this.addTemporaryImage(picture);
      }
    });
  }

  update() {
    this.updatePictures();
  }
}
