// AgentNxt title override — watches for title changes and prepends "AgentNxt · "
(function() {
  var appName = document.currentScript && document.currentScript.getAttribute('data-app');
  var prefix = appName ? 'AgentNxt \u00b7 ' + appName : 'AgentNxt';

  function setTitle() {
    if (document.title && document.title !== prefix && !document.title.startsWith('AgentNxt')) {
      document.title = prefix;
    } else if (!document.title) {
      document.title = prefix;
    }
  }

  setTitle();

  // Watch for SPA title changes
  var observer = new MutationObserver(function() { setTitle(); });
  var titleEl = document.querySelector('title');
  if (titleEl) {
    observer.observe(titleEl, { childList: true, characterData: true, subtree: true });
  } else {
    // Title element doesn't exist yet — wait for it
    var headObserver = new MutationObserver(function() {
      var t = document.querySelector('title');
      if (t) {
        setTitle();
        observer.observe(t, { childList: true, characterData: true, subtree: true });
        headObserver.disconnect();
      }
    });
    if (document.head) {
      headObserver.observe(document.head, { childList: true });
    }
  }
})();
