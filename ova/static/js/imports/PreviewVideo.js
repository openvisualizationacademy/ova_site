export default class PreviewVideos {
  constructor(app, selector) {
    this.app = app;
    this.element = document.querySelector(selector);
    this.video = this.element.querySelector("video");
    this.customControls = false;
    this.controls = this.element.querySelectorAll("[data-control]");
    this.controlsElement = this.element.querySelector(".controls");
    this.icons = {};
    this.icons.play = this.element.querySelector('[data-iconoir="play"]');
    this.icons.pause = this.element.querySelector('[data-iconoir="pause"]');
    this.icons.soundOn = this.element.querySelector('[data-iconoir="sound-high"]');
    this.icons.soundOff = this.element.querySelector('[data-iconoir="sound-off-alt"]');

    this.setup();
  }

  get isFulllScreen() {
    if (document.fullscreenElement && document.fullscreenElement !== null) return true;
    if (document.webkitFullscreenElement && document.webkitFullscreenElement !== null) return true;
    if (document.mozFullScreenElement && document.mozFullScreenElement !== null) return true;
    if (document.msFullscreenElement && document.msFullscreenElement !== null) return true;

    return false;
  }

  requestFullscreen() {
    // Video or wrapper element
    const element = this.video;

    if (element.requestFullScreen) {
      element.requestFullScreen();
      return;
    }

    if (element.mozRequestFullScreen) {
      element.mozRequestFullScreen();
      return;
    }

    if (element.webkitRequestFullScreen) {
      element.webkitRequestFullScreen();
      return;
    }

    if (this.video.webkitEnterFullScreen) {
      this.video.webkitEnterFullScreen();
      return;
    }
  }

  exitFullscreen() {
    if (document.exitFullscreen) {
      document.exitFullscreen();
      return;
    }

    if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
      return;
    }

    if (document.mozCancelFullScreen) {
      document.mozCancelFullScreen();
      return;
    }

    if (document.msExitFullscreen) {
      document.msExitFullscreen();
      return;
    }
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
      this.icons.pause.removeAttribute("hidden");
      this.icons.play.setAttribute("hidden", "");
      return;
    }

    this.pause();
  }

  pause() {
    this.video.pause();
    this.icons.pause.setAttribute("hidden", "");
    this.icons.play.removeAttribute("hidden");
  }

  unmute(force = false) {
    if (this.video.muted || force) {
      this.video.muted = false;
      this.icons.soundOn.removeAttribute("hidden");
      this.icons.soundOff.setAttribute("hidden", "");
      return;
    }

    this.video.muted = true;
    this.icons.soundOn.setAttribute("hidden", "");
    this.icons.soundOff.removeAttribute("hidden");
  }

  expand() {
    if (!this.isFulllScreen) {
      this.requestFullscreen();
      return;
    }

    this.exitFullscreen();
  }

  setup() {
    if (this.app.accessibility.reducedMotion) {
      this.pause();
    }

    this.controls.forEach((element) => {
      element.addEventListener("click", () => {
        const handler = element.dataset.control;
        if (handler in this) {
          this[handler]();
        }

        if (handler === "playWithAudio") {
          element.remove();

          if (this.customControls) {
            this.controlsElement.hidden = false;
            setTimeout(() => {
              this.icons.play.parentElement.focus();
            }, 100);
          } else {
            this.video.controls = true;
            setTimeout(() => {
              this.video.focus();
            }, 100);
          }
        }
      });
    });
  }

  update() {}
}
