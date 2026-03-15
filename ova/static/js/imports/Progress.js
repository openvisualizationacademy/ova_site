export default class Progress {
  constructor(course) {
    this.course = course;
    this.endpoint = "/api/progress/update/";
    this.api = this.endpoint;

    this.setup();
  }

  async updateSegment(segmentId, percent) {

    const payload = {
      segment_id: segmentId,
      percent_watched: percent
    };

    const response = await fetch(this.api, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    return data;
  }

  setup() {}
}