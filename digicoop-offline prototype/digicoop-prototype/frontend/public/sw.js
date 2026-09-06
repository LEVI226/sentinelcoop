// Service worker minimal : ne fait que garder l'app shell en cache pour que
// la PWA se recharge même sans réseau. La logique de synchronisation vit
// dans la page elle-même (src/sync), pas ici.
const CACHE_NAME = "digicoop-shell-v1";
const APP_SHELL = ["/", "/index.html", "/manifest.webmanifest"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  // Les appels de synchronisation ne doivent jamais être servis depuis le cache :
  // c'est la sentinelle réseau (voir connectivitySentinel.js) qui décide de leur sort.
  if (event.request.url.includes("/sync/") || event.request.url.includes("/health")) return;

  event.respondWith(
    caches.match(event.request).then((cached) => {
      return (
        cached ||
        fetch(event.request)
          .then((response) => {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
            return response;
          })
          .catch(() => cached)
      );
    })
  );
});
