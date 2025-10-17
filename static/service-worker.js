self.addEventListener('install', function(event) {
    console.log('Service Worker installé.');
});

self.addEventListener('fetch', function(event) {
    // Tu peux ajouter un cache ici pour offline si tu veux
    event.respondWith(fetch(event.request));
});
