// ── Analytics Init — AgentStudio ─────────────────────────────
// PostHog + OpenPanel (both cloud, loaded in parallel)

// ── PostHog ──────────────────────────────────────────────────
!function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+" (stub)"},o="capture identify alias people.set people.set_once set_config register register_once unregister opt_out_capturing has_opted_out_capturing opt_in_capturing reset isFeatureEnabled onFeatureFlags getFeatureFlag getFeatureFlagPayload reloadFeatureFlags group updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures getActiveMatchingSurveys getSurveys getNextSurveyStep onSessionId setPersonPropertiesForFlags".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);

posthog.init("phc_oa1L9yxPtOyZmvLr4FXnJBMxYZYyyleoKqcPNPytqPt", {
  api_host: "https://us.i.posthog.com",
  person_profiles: "identified_only",
  capture_pageview: true,
  capture_pageleave: true
});

// ── OpenPanel ─────────────────────────────────────────────────
(function(){
  var s = document.createElement("script");
  s.src = "https://cdn.openpanel.dev/op1.js";
  s.async = true;
  s.setAttribute("data-client-id", "fbd43e73-eef4-49f3-ba15-d8dcb33b419d");
  s.setAttribute("data-client-secret", "sec_9a66faf2ff579c1f10f2");
  s.setAttribute("data-track-screen-views", "true");
  s.setAttribute("data-track-outgoing-links", "true");
  s.setAttribute("data-track-attributes", "true");
  document.head.appendChild(s);
})();
