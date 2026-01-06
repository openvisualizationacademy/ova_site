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
    this.videoProgressElement = this.course.element.querySelector(".video-progress");

    // Keeps track of last timeupdate call for throttle feature
    this.lastSeconds = 0;

    // Consider something as watched if the below amount of secodns had passed since lastSeconds
    this.delay = 3;

    // This will be updated with actual video duration
    this.duration = 0;

    // NOTE: 100ms offset is used at start because Vimeo refuses to play video when percent is 0
    this.offsetStart = 0.1;

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

    // Create HTML element with all parts (and set some as watched)
    const parts = this.course.app.utils.html(`
      <div class="video-progress-parts">
        <div class="playhead"></div>
        ${
          this.parts.map((watched, i) => 
            `<button class="video-progress-part reset" data-watched="${ watched }" data-percent="${ i / this.parts.length }"></button>`
          ).join("")
        }
      </div>`);

    // Create HTML element with nicely formatted watch percentage
    const percentage = this.course.app.utils.html(`
      <p class="video-progress-percentage">
        <small>
          Video <span>${ this.percentWatched }%</span> watched
        </small>
      </p>`);

    // Add elements to user interface
    this.videoProgressElement.append(parts, percentage);

    // Select elements to be easily updated in showProgress
    this.videoProgressPartElements = parts.querySelectorAll(".video-progress-part");
    this.videoProgressPlayheadElement = parts.querySelector(".playhead");
    this.videoProgressPercentElement = percentage.querySelector("span");

    // Allow clicking in a part to skip the video to that moment
    this.videoProgressPartElements.forEach( part => {
      part.addEventListener("click", () => {
        this.seekToPart(part);
      });
    });
  }

  async seekToPart(part) {
    // Ensure part parameter exists
    if (!part) return;

    // If video duration was not already obtained
    if (!this.duration) {

      // Get video duration in seconds and cache it
      this.duration = await this.player.getDuration();
    }
          
    // Get clicked percentage as decimal
    let seconds = Math.floor(parseFloat(part.dataset.percent) * this.duration);

    // NOTE: 100ms offset is used at start because Vimeo refuses to play video when percent is 0
    if (seconds === 0) seconds = this.offsetStart;

    this.seekToSeconds(seconds);
  }

  async seekToSeconds(seconds) {

    // Add “loading” class to parent (as to add a spinner in CSS)
    this.videoProgressElement.classList.add("processing");

    // Pause video
    await this.player.pause();
  
    try {

      // Sets a time (and checks the precise time Vimeo seeked to)
      const seekedSeconds = await this.player.setCurrentTime(seconds);

      // Update tracked time so part has a delay before being set as watched
      this.lastSeconds = seekedSeconds;

    } catch (error) {

      // TODO: Handle errors
      console.error(error.name, error);
    }
    
    try {
      
      // Ask Vimeo to play the video
      await this.player.play();

      // Remove visual feedback after video actually starts playing
      this.videoProgressElement.classList.remove("processing");

    } catch (error) {
      
      // TODO: Handle errors
      console.error(error.name, error);
    }
  }

  showProgress() {
    if (!this.videoProgressElement) return;

    // Only update part nodes here (instead of recreating them)
    this.parts.forEach( (watched, i) => {
      this.videoProgressPartElements[i].dataset.watched = watched;
    });

    // Update percentage (10%, 20%, 30%, etc)
    this.videoProgressPercentElement.textContent = `${ this.percentWatched }%`;
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
    this.player.on("pause", () => {
      this.isPlaying = false;
    });

    // When user seeks/scrubs/skips to a certain moment
    this.player.on("seeked", (data) => {
      // Update this to add delay in watched check
      this.lastSeconds = data.seconds;
    }); 

    // When video is progressing or user is scrubbing
    this.player.on("timeupdate", (data) => {

      // Ensure video is actually playing
      if (!this.isPlaying) return;

      // If video duration was not already obtained
      if (!this.duration) {

        // Get video duration in seconds and cache it
        this.duration = data.duration
      }

      // Get current position of video (in seconds)
      const { seconds } = data;

      // Visually mark current position of video on parts bar
      this.updatePlayhead(seconds);

      // Throttle to run roughly once every 3 seconds
      if (Math.abs(seconds - this.lastSeconds) < this.delay) return;

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

        // TODO: Optimistically display green checkmark on segment title and on chapter list
      }

    });

    this.setupProgress();
  }
  
  setup() {    
    this.setupPlayer();
  }

  updatePlayhead(seconds) {
    const percent = `${ seconds / this.duration * 100 }%`;
    this.videoProgressPlayheadElement.style.insetInlineStart = percent;
  }
}