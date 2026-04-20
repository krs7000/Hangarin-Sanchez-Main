self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open('hangarin-cache-v1').then(function(cache) {
      return cache.addAll([
        '/',
        '/static/hangarin/dashboard.css',
        '/static/hangarin/img/icon-192.png',
        '/static/hangarin/img/icon-512.png',
      ]);
    })
  );
});

self.addEventListener('fetch', function(e) {
  e.respondWith(
    caches.match(e.request).then(function(response) {
      return response || fetch(e.request);
    })
  );
});
