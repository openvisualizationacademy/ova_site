export default class DeltaTime {
  constructor(lastTime) {
    this.lastTime = lastTime === undefined ? 0 : lastTime;
    this.value = 0;
  }

  valueOf() {
    return this.value;
  }

  update(currentTime) {
    this.value = (currentTime - this.lastTime) / 1000;
    this.lastTime = currentTime;
  }
}
