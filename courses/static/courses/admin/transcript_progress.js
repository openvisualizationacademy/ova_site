(function () {
  "use strict";

  var TRANSCRIPT_ACTIONS = ["fetch_missing_transcripts", "redownload_transcript"];

  function showOverlay() {
    var overlay = document.createElement("div");
    overlay.id = "transcript-progress-overlay";
    overlay.style.cssText =
      "position:fixed;inset:0;z-index:9999;display:flex;flex-direction:column;" +
      "align-items:center;justify-content:center;gap:1rem;" +
      "background:rgba(0,0,0,0.65);color:#fff;font-family:sans-serif;font-size:1rem;";

    var spinner = document.createElement("div");
    spinner.style.cssText =
      "width:2.5rem;height:2.5rem;border-radius:50%;" +
      "border:0.3rem solid rgba(255,255,255,0.3);border-top-color:#fff;" +
      "animation:transcript-progress-spin 0.8s linear infinite;";

    var style = document.createElement("style");
    style.textContent =
      "@keyframes transcript-progress-spin{to{transform:rotate(360deg);}}";

    var text = document.createElement("div");
    text.textContent = "Fetching transcripts from Vimeo — this may take a moment…";

    overlay.appendChild(style);
    overlay.appendChild(spinner);
    overlay.appendChild(text);
    document.body.appendChild(overlay);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("changelist-form");
    if (!form) return;

    form.addEventListener("submit", function () {
      var actionSelect = form.querySelector('select[name="action"]');
      if (!actionSelect || TRANSCRIPT_ACTIONS.indexOf(actionSelect.value) === -1) {
        return;
      }

      var goButton = form.querySelector('button[type="submit"], input[type="submit"]');
      if (goButton) {
        goButton.disabled = true;
      }

      showOverlay();
    });
  });
})();
