/* Service worker — Kartners Travel Agency
 * - Pages : réseau d'abord (contenu toujours à jour), copie de secours hors ligne.
 * - Fichiers /static : cache d'abord.
 * - Jamais de cache pour l'administration ni pour l'API.
 */
const CACHE = 'kta-v4';
const PRECACHE = ['/', '/static/css/kta.css?v=4', '/static/js/kta.js?v=4', '/static/images/kta-logo.png', '/static/images/icon-192.png'];

self.addEventListener('install', event => {
    event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(PRECACHE)).catch(() => {}));
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', event => {
    const req = event.request;
    if (req.method !== 'GET') return;
    const url = new URL(req.url);
    if (url.origin !== location.origin) return;
    if (url.pathname.startsWith('/admin') || url.pathname.startsWith('/api/')) return;

    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(req).then(hit => hit || fetch(req).then(res => {
                if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
                return res;
            }))
        );
        return;
    }

    if (req.mode === 'navigate') {
        event.respondWith(
            fetch(req).then(res => {
                if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
                return res;
            }).catch(() => caches.match(req).then(hit => hit || caches.match('/')))
        );
    }
});
