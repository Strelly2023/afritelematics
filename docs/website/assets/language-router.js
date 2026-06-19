(function () {
  var storageKey = "novatech.language";
  var supported = ["en", "fr", "sw"];
  var routes = {
    home: {
      en: "",
      fr: "fr/",
      sw: "sw/"
    },
    platform: {
      en: "",
      fr: "fr/platform.html",
      sw: "sw/platform.html"
    },
    programming: {
      en: "",
      fr: "fr/programming.html",
      sw: "sw/programming.html"
    },
    verify: {
      en: "https://verify.afritechnology.com/public/verify/portal",
      fr: "fr/verify.html",
      sw: "sw/verify.html"
    }
  };

  function normalize(language) {
    var value = String(language || "").toLowerCase();
    if (value.indexOf("fr") === 0) return "fr";
    if (value.indexOf("sw") === 0 || value.indexOf("kiswahili") === 0) return "sw";
    if (value.indexOf("en") === 0) return "en";
    return "";
  }

  function readStoredLanguage() {
    try {
      return normalize(window.localStorage.getItem(storageKey));
    } catch (error) {
      return "";
    }
  }

  function storeLanguage(language) {
    try {
      window.localStorage.setItem(storageKey, language);
    } catch (error) {
      return;
    }
  }

  function requestedLanguage() {
    var queryLanguage = normalize(new URLSearchParams(window.location.search).get("lang"));
    if (queryLanguage) {
      storeLanguage(queryLanguage);
      return queryLanguage;
    }

    var storedLanguage = readStoredLanguage();
    if (storedLanguage) return storedLanguage;

    var browserLanguages = window.navigator.languages || [window.navigator.language];
    for (var index = 0; index < browserLanguages.length; index += 1) {
      var browserLanguage = normalize(browserLanguages[index]);
      if (browserLanguage) return browserLanguage;
    }

    return "en";
  }

  function bindLanguageLinks() {
    document.addEventListener("click", function (event) {
      var link = event.target.closest ? event.target.closest("a[data-lang]") : null;
      if (!link) return;
      var language = normalize(link.getAttribute("data-lang"));
      if (supported.indexOf(language) !== -1) storeLanguage(language);
    });
  }

  bindLanguageLinks();

  var script = document.currentScript;
  var routeName = script ? script.getAttribute("data-route") : "";
  if (!routeName || !routes[routeName]) return;

  var language = requestedLanguage();
  var target = routes[routeName][language] || routes[routeName].en;
  if (!target) return;

  if (window.location.hash && target.indexOf("#") === -1) {
    target += window.location.hash;
  }

  var destination = new URL(target, window.location.href);
  if (destination.href === window.location.href) return;

  window.location.replace(destination.href);
})();
