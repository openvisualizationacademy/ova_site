import People from "./People.js";

export default class Instructors extends People {
  constructor(app, selector) {
    super(app, selector, "instructor", "instructors");
  }

  getDetails(person) {
    const alt = person.alt ? person.alt : "Profile";

    return `
    <div class="details">
      <div class="person" data-role="${this.role}">
        ${
          person.photo
            ? `<img class="media" src="/static/media/people/small/${person.photo}" loading="lazy" alt="${alt}">`
            : `<div class="media"></div>`
        }
        <div class="info">
          <h2><strong>${person.name}</strong></h2>
          <span class="tagline">${person.tagline}</span>  
          <p class="bio">${person.bio}</p>          

          <h3>${ person.courses.length > 1 ? "Courses" : "Course" }</h3>
          <ul class="courses">
            ${ person.courses.map(course => `<li>${course}</li>`).join("") }
          </ul>
        </div>
        <ul class="links">
          ${ this.list(person.links) }
        </ul>
      </div>
    </div>
    `;
  }
}
