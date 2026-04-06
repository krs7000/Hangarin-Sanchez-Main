const CACHE_NAME = 'hangarin-cache-v1';
const STATIC_ASSETS = [
    '/',
    '/static/hangarin/auth.css',
    '/static/hangarin/dashboard.css',
    '/static/hangarin/img/icon-192.png',
    '/static/hangarin/img/icon-512.png',
    '/static/hangarin/login-scene.svg',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS);
        })
    );
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});
