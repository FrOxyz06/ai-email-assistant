const CACHE = "email-demo-v2";
const ASSETS = ["/", "/static/style.css", "/static/app.js", "/manifest.webmanifest",
  "/static/icons/icon-192.png", "/static/icons/icon-512.png"];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)));
});

self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key === "mohamed-ai-v1" || (key.startsWith("email-demo-") && key !== CACHE))
      .map(key => caches.delete(key))
  )));
});

self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);
  // Only cache the app shell, never inbox or calendar responses.
  if (event.request.method !== "GET" || url.origin !== self.location.origin || !ASSETS.includes(url.pathname)) return;
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
