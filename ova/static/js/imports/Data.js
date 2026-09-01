import { csv, json, autoType } from "d3";

export default class Data {
  constructor() {}

  load(sources = [], callback) {
    const promises = sources.map((source) => {
      if (source.type === "json") return json(source.path, autoType);
      if (source.type === "csv") return csv(source.path, autoType);
    });

    Promise.all(promises).then((values) => {
      sources.forEach((source, index) => {
        this[source.name] = values[index];
      });

      if (callback) callback();
    });
  }
}
