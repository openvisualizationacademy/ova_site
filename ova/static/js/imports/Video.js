export default class Video {
  constructor(course, selector) {
    this.course = course;
    this.iframe = this.course.element.querySelector(selector);
    if (!this.iframe) return;

    // Keep track of whether video is playing or paused
    this.isPlaying = false;

    // Define how many fractions of the video should be tracked (watched or not)
    this.partsCount = 10;

    // Get element for displaying course progress
    this.videoProgress = this.course.element.querySelector(".video-progress");

    // Keeps track of last timeupdate call for throttle feature
    this.lastSeconds = 0;

    this.setup();
  }

  get percentWatched() {
    
    // Count how many watched (true) parts
    const count = this.parts.filter(watched => watched === true).length;

    // Get percentage as a decimal
    const percent = count / this.parts.length;

    // Get percentage as integer from 0 to 100;
    return Math.round(percent * 100);
  }
  
  setupProgress() {
    // TODO: Check if parts of current video already exists in localStorage before creating empty array

    // TODO: Check if percent of completion in DB is > 0 before creating empty array

    // Keep track of which parts of the video were already watched
    this.parts = Array.from({ length: this.partsCount }, () => false);

    // Show video progress tracker even before video plays
    this.showProgress();
  }

  showProgress() {
    if (!this.videoProgress) return;

    // TODO: Move markup generation to setupProgress() and only update nodes here (instead of replacing them)

    // Create HTML element with of parts (and set some as watched)
    const parts = this.course.app.utils.html(`
      <div class="video-progress-parts">
        ${
          this.parts.map((watched, i) => 
            `<div class="video-progress-part" data-watched="${ watched }" data-percent="${ (i + 1) / this.parts.length }"></div>`
          ).join("")
        }
      </div>`);

    // Create HTML element with nicely formatted watch percentage
    const percentage = this.course.app.utils.html(`
      <p class="video-progress-percentage">
        <small>
          Video ${ this.percentWatched }% watched
        </small>
      </p>`);

    // Update user interface
    this.videoProgress.replaceChildren(parts, percentage);
  }

  setupPlayer() {
    // Retry in 1s if the Vimeo API is not yet available
    if (!Vimeo) {
      setTimeout(() => {
        this.setupPlayer();
      }, 1000 );

      // TODO: Add error message after N retries
      return;
    };
    
    // Create instance of Player class
    this.player = new Vimeo.Player(this.iframe);
  
    // When video starts playing
    this.player.on("play", () => {
      this.isPlaying = true;
    });

    // When video gets paused
    this.player.on("pause", (data) => {
      this.isPlaying = false;
    });

    // When video is progressing or user is scrubbing
    this.player.on("timeupdate", (data) => {

      // Ensure video is actually playing
      if (!this.isPlaying) return;

      // Get current position of video (in seconds)
      const { seconds } = data;

      // Throttle to run roughly once every 3 seconds
      if (Math.abs(seconds - this.lastSeconds) < 3) return;

      // Store seconds for checking in next timeupdate call
      this.lastSeconds = seconds;

      // Check which part of the video is currently being played
      for (let i = 0; i < this.parts.length; i++) {

        // Get limit of current part as decimal (.1, .2, .3, …, 1)
        const upperLimit = (i + 1) / this.parts.length;

        // If user is watching the current part (like 1/10, 2/10, 3/10)
        if (data.percent < upperLimit) {

          // Update part in parts array as true (watched)
          this.parts[i] = true;

          // Stop checking further
          break;
        }
      }

      // Update UI
      this.showProgress();

      // Ensure segmentId is provided
      if (segmentId === undefined) return;

      // TODO: Add refined logic for determining if user watched video
      const percent = this.percentWatched;

      // TODO: Consider sending updates with other percentages too
      if (percent === 100) {
        // Send API request to update completion status 
        this.course.progress.updateSegment(segmentId, percent);
      }

    });

  }
  
  setup() {    
    this.setupProgress();
    this.setupPlayer();
  }
}