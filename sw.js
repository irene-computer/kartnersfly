// Service Worker pour Kartners Travel Agency PWA
const CACHE_NAME = 'kartners-v1';
const urlsToCache = [
  '/',
  '/static/style.css',
  '/static/script.js',
  '/manifest.json'
];

// Installation du service worker
self.addEventListener('install', event => {
  console.log('[SW] Installation du service worker');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Mise en cache des ressources');
        return cache.addAll(urlsToCache);
      })
  );
});

// Récupération des ressources (offline first)
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Retourne la ressource du cache si elle existe
        if (response) {
          return response;
        }
        // Sinon, va chercher sur le réseau
        return fetch(event.request);
      })
  );
});

// Activation - nettoyage des anciens caches
self.addEventListener('activate', event => {
  console.log('[SW] Activation du service worker');
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME)
          .map(key => {
            console.log('[SW] Suppression de l\'ancien cache:', key);
            return caches.delete(key);
          })
      );
    })
  );
});