export default class Utils {
  constructor() {

  }

  html(string) {
    // Create a DocumentFragment
    const fragment = document.createRange().createContextualFragment(string);

    // console.log(...fragment.children);

    // If it has a single child element, return it
    if (fragment.childElementCount === 1) {
      return fragment.firstElementChild;
    }

    // Otherwise, wrap all children in a div and return them
    const div = document.createElement("div");
    div.append(...fragment.children);
    return div;
  }
}