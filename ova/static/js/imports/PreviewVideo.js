export default class PreviewVideos {
  constructor(app, selector) {
    this.app = app;
    this.element = document.querySelector(selector);

    // Stop executing if provided selector doesn’t exist
    if (!this.element) return;

    this.video = this.element.querySelector("video");
    this.minutes = this.element.querySelector(".minutes");
    this.controls = this.element.querySelectorAll("[data-control]");

    this.setup();
  }

  playWithAudio() {
    this.restart();
    setTimeout(() => {
      this.play(true);
      this.unmute(true);
    }, 100);
  }

  restart() {
    this.video.currentTime = 0;
  }

  play(force = false) {
    if (this.video.paused || force) {
      this.video.play();
      return;
    }

    this.pause();
  }

  pause() {
    this.video.pause();
  }

  unmute(force = false) {
    if (this.video.muted || force) {
      this.video.muted = false;
      return;
    }

    this.video.muted = true;
  }

  setup() {
    if (this.app.accessibility.reducedMotion) {
      this.pause();
    }

    this.minutes.textContent = `${ Math.round(this.video.duration / 60) } min`;

    this.controls.forEach((element) => {
      element.addEventListener("click", () => {
        const handler = element.dataset.control;
        if (handler in this) {
          this[handler]();
        }

        if (handler === "playWithAudio") {
          element.remove();
            this.video.controls = true;
            setTimeout(() => {
              this.video.focus();
            }, 100);
        }
      });
    });
  }

  update() {}
}
