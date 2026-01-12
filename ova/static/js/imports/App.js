import Utils from "./Utils.js";
import Accessibility from "./Accessibility.js";
import Logo from "./Logo.js";
import ThemePicker from "./ThemePicker.js";
import PreviewVideo from "./PreviewVideo.js";
import Icons from "./Icons.js";
import Courses from "./Courses.js";
import Course from "./Course.js";
import Instructors from "./Instructors.js";
import Contributors from "./Contributors.js";
import Certificate from "./Certificate.js";
import Background from "./Background.js";

export default class App {
  constructor(selector) {
    this.element = document.querySelector(selector) || document.body;
    this.setup();
  }

  setup() {
    this.utils = new Utils(this);
    this.icons = new Icons(this);
    this.accessibility = new Accessibility(this);

    this.logo = new Logo(this, {
      parent: ".logo",
      margin: 1,
      side: 96,
    });

    this.wave = new Logo(this, {
      parent: ".wave",
      margin: 168 / 2,
      side: 168,
      wave: true,
      interactive: false,
    });

    this.previewVideo = new PreviewVideo(this, ".preview");
    this.courses = new Courses(this, ".courses .widget");
    this.course = new Course(this, ".course-page");
    this.instructors = new Instructors(this, ".instructors");
    this.contributors = new Contributors(this, ".contributors");
    this.themePicker = new ThemePicker(this, ".theme-picker");
    this.certificate = new Certificate(this, ".certificate");
    this.background = new Background(this, ".background");

    // Allow anchor navigation, but don’t change url
    document.querySelectorAll('a[href^="#"]').forEach((a) => {
      const id = a.hash.replace("#", "");
      a.addEventListener("click", (event) => {
        event.preventDefault();
        const element = id ? document.getElementById(id) : document.body;
        element.scrollIntoView();
      });
    });
  }

  update() {}
}
