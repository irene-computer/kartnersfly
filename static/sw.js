// ============================================
// SERVICE WORKER - KARTNERS TRAVEL AGENCY
// ============================================

const CACHE_NAME = 'kartners-v1';
const urlsToCache = [
    '/',
    '/static/style.css',
    '/static/script.js',
    '/static/images/kta.png',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css',
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap'
];

// Installation du Service Worker
self.addEventListener('install', event => {
    console.log('Service Worker installation');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Cache ouvert');
                return cache.addAll(urlsToCache);
            })
            .catch(err => console.log('Erreur cache:', err))
    );
    self.skipWaiting();
});

// Activation
self.addEventListener('activate', event => {
    console.log('Service Worker activé');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cache => {
                    if (cache !== CACHE_NAME) {
                        console.log('Ancien cache supprimé:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Interception des requêtes
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Retourner le cache si trouvé
                if (response) {
                    return response;
                }
                
                // Sinon, faire la requête réseau
                return fetch(event.request)
                    .then(response => {
                        // Vérifier si la réponse est valide
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }
                        
                        // Mettre en cache la nouvelle réponse
                        const responseToCache = response.clone();
                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(event.request, responseToCache);
                            });
                        
                        return response;
                    })
                    .catch(() => {
                        // Page hors ligne pour les pages HTML
                        if (event.request.headers.get('accept').includes('text/html')) {
                            return caches.match('/offline.html');
                        }
                    });
            })
    );
});

// Gestion des notifications push (optionnel)
self.addEventListener('push', event => {
    const options = {
        body: event.data.text(),
        icon: '/static/images/kta.png',
        badge: '/static/images/kta.png',
        vibrate: [200, 100, 200],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        }
    };
    
    event.waitUntil(
        self.registration.showNotification('Kartners Travel', options)
    );
});