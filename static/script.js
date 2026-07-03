// ============================================
// KARTNERS TRAVEL AGENCY - SCRIPT DYNAMIQUE
// ============================================

// ========== 1. MENU MOBILE ==========
document.addEventListener('DOMContentLoaded', function() {
    // Menu mobile toggle
    const mobileMenuBtn = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (mobileMenuBtn && navbarCollapse) {
        mobileMenuBtn.addEventListener('click', function() {
            navbarCollapse.classList.toggle('show');
        });
        
        // Fermer le menu lors du clic sur un lien
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                navbarCollapse.classList.remove('show');
            });
        });
    }
    
    // ========== 2. HEADER SCROLL EFFECT ==========
    const header = document.querySelector('header');
    let lastScroll = 0;
    
    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 100) {
            header.style.background = 'linear-gradient(135deg, rgba(107, 63, 160, 0.98) 0%, rgba(30, 58, 138, 0.98) 100%)';
            header.style.backdropFilter = 'blur(10px)';
        } else {
            header.style.background = 'linear-gradient(135deg, var(--violet-dark) 0%, var(--blue-dark) 100%)';
            header.style.backdropFilter = 'blur(2px)';
        }
        
        lastScroll = currentScroll;
    });
    
    // ========== 3. FORMULAIRE DE CONTACT DYNAMIQUE ==========
    const contactForm = document.getElementById('travelForm');
    const formMessage = document.getElementById('formFeedback');
    
    if (contactForm) {
        contactForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Récupération des données
            const formData = {
                name: document.getElementById('name')?.value || '',
                email: document.getElementById('email')?.value || '',
                phone: document.getElementById('phone')?.value || '',
                message: document.getElementById('message')?.value || '',
                date: new Date().toISOString()
            };
            
            // Validation
            if (!formData.name || !formData.email || !formData.message) {
                showFormMessage('Veuillez remplir tous les champs obligatoires (*)', 'error');
                return;
            }
            
            if (!isValidEmail(formData.email)) {
                showFormMessage('Veuillez entrer une adresse email valide', 'error');
                return;
            }
            
            // Afficher le message de chargement
            showFormMessage('Envoi en cours...', 'loading');
            
            try {
                // Simulation d'envoi (à remplacer par votre endpoint réel)
                // Pour l'instant, on simule une réponse API
                await simulateApiCall(formData);
                
                // Succès
                showFormMessage(`✅ Merci ${formData.name} ! Un expert Kartners vous répondra dans les plus brefs délais.`, 'success');
                contactForm.reset();
                
                // Effacer le message après 5 secondes
                setTimeout(() => {
                    if (formMessage) formMessage.innerHTML = '';
                }, 5000);
                
                // Envoyer les données à votre backend (optionnel)
                // await sendToBackend(formData);
                
            } catch (error) {
                console.error('Erreur:', error);
                showFormMessage('❌ Une erreur est survenue. Veuillez réessayer ou nous contacter directement.', 'error');
            }
        });
    }
    
    // ========== 4. NEWSLETTER ==========
    const newsletterInput = document.querySelector('.newsletter-input');
    const newsletterBtn = document.querySelector('.newsletter-btn');
    
    if (newsletterBtn && newsletterInput) {
        newsletterBtn.addEventListener('click', async () => {
            const email = newsletterInput.value.trim();
            
            if (!email) {
                showToast('Veuillez entrer votre adresse email', 'error');
                return;
            }
            
            if (!isValidEmail(email)) {
                showToast('Email invalide', 'error');
                return;
            }
            
            // Simulation d'inscription
            showToast('✅ Inscription réussie ! Vous recevrez nos offres exclusives.', 'success');
            newsletterInput.value = '';
        });
        
        newsletterInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                newsletterBtn.click();
            }
        });
    }
    
    // ========== 5. ANIMATIONS AU SCROLL ==========
    // Options de l'observateur
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    // Création de l'observateur
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target); // Arrêter d'observer une fois animé
            }
        });
    }, observerOptions);
    
    // Observer les cartes
    document.querySelectorAll('.service-card, .destination-card, .contact-info-card, .contact-form').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'all 0.6s ease-out';
        observer.observe(el);
    });
    
    // Observer les titres de section
    document.querySelectorAll('.section-title').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'all 0.5s ease-out';
        observer.observe(el);
    });
    
    // ========== 6. BOUTON RETOUR HAUT ==========
    // Créer le bouton s'il n'existe pas
    if (!document.querySelector('.scroll-top')) {
        const scrollBtn = document.createElement('button');
        scrollBtn.className = 'scroll-top';
        scrollBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
        scrollBtn.setAttribute('aria-label', 'Retour en haut');
        document.body.appendChild(scrollBtn);
        
        scrollBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    const scrollBtn = document.querySelector('.scroll-top');
    
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            scrollBtn?.classList.add('show');
        } else {
            scrollBtn?.classList.remove('show');
        }
    });
    
    // ========== 7. LIENS DE NAVIGATION SMOOTH ==========
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href && href !== '#') {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
    
    // ========== 8. BOUTONS "RÉSERVER" ==========
    document.querySelectorAll('.destination-card .btn-outline-primary, .destination-card .btn-sm').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const destinationSection = document.getElementById('contact');
            if (destinationSection) {
                destinationSection.scrollIntoView({ behavior: 'smooth' });
                // Option: pré-remplir le message avec la destination
                const destinationCard = btn.closest('.destination-card');
                const destinationName = destinationCard?.querySelector('h3')?.textContent || 'une destination';
                const messageField = document.getElementById('message');
                if (messageField) {
                    messageField.value = `Je souhaite réserver pour ${destinationName}`;
                    messageField.focus();
                }
            }
        });
    });
    
    // ========== 9. CHARGEMENT DES DESTINATIONS (API Dynamique) ==========
    loadDestinations();
    
    // ========== 10. CHARGEMENT DES SERVICES (API Dynamique) ==========
    loadServices();
});

// ========== FONCTIONS UTILITAIRES ==========

// Validation d'email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Afficher les messages du formulaire
function showFormMessage(message, type) {
    const formMessage = document.getElementById('formFeedback');
    if (!formMessage) return;
    
    formMessage.innerHTML = message;
    formMessage.style.display = 'block';
    
    switch(type) {
        case 'success':
            formMessage.style.color = '#10B981';
            formMessage.style.background = '#D1FAE5';
            break;
        case 'error':
            formMessage.style.color = '#EF4444';
            formMessage.style.background = '#FEE2E2';
            break;
        case 'loading':
            formMessage.style.color = '#F59E0B';
            formMessage.style.background = '#FEF3C7';
            break;
        default:
            formMessage.style.color = '#6B3FA0';
            formMessage.style.background = '#EDE9FE';
    }
    
    formMessage.style.padding = '12px';
    formMessage.style.borderRadius = '12px';
    formMessage.style.marginTop = '15px';
    
    setTimeout(() => {
        if (formMessage.innerHTML === message) {
            formMessage.style.opacity = '0';
            setTimeout(() => {
                formMessage.innerHTML = '';
                formMessage.style.opacity = '1';
                formMessage.style.display = 'none';
            }, 300);
        }
    }, 5000);
}

// Afficher des toasts
function showToast(message, type) {
    // Créer le toast s'il n'existe pas
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
        `;
        document.body.appendChild(toastContainer);
    }
    
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.style.cssText = `
        background: ${type === 'success' ? '#10B981' : '#EF4444'};
        color: white;
        padding: 12px 24px;
        border-radius: 12px;
        margin-top: 10px;
        font-size: 14px;
        font-weight: 500;
        animation: slideInRight 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        cursor: pointer;
    `;
    toast.innerHTML = message;
    
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
    
    toast.addEventListener('click', () => toast.remove());
}

// Simulation d'appel API (à remplacer par votre vrai backend)
function simulateApiCall(data) {
    return new Promise((resolve) => {
        setTimeout(() => {
            console.log('Données envoyées:', data);
            resolve({ success: true });
        }, 1500);
    });
}

// Envoi vers backend (décommentez et adaptez)
/*
async function sendToBackend(data) {
    const response = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return await response.json();
}
*/

// ========== CHARGEMENT DYNAMIQUE DES DESTINATIONS ==========
async function loadDestinations() {
    const container = document.querySelector('#destinations .row');
    if (!container || container.querySelector('.destination-card')) return;
    
    // Données des destinations (peuvent venir d'une API)
    const destinations = [
        {
            name: 'Santorini, Grèce',
            image: 'https://images.unsplash.com/photo-1533105079780-92b9be482077?w=600&auto=format',
            description: 'Couchers de soleil légendaires, architecture cycladique.',
            price: '890'
        },
        {
            name: 'Maldives',
            image: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&auto=format',
            description: 'Lagons turquoise, overwater villas et sérénité absolue.',
            price: '1590'
        },
        {
            name: 'Paris, France',
            image: 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=600&auto=format',
            description: 'Art, gastronomie et romantisme au cœur de l\'Europe.',
            price: '620'
        },
        {
            name: 'Tokyo, Japon',
            image: 'https://images.unsplash.com/photo-1523800503107-5bc3ba2a6f81?w=600&auto=format',
            description: 'Culture futuriste et traditions millénaires.',
            price: '1320'
        },
        {
            name: 'Amalfi, Italie',
            image: 'https://images.unsplash.com/photo-1516483638261-f4dbaf03663a?w=600&auto=format',
            description: 'Costiera Amalfitana, douceur de vivre.',
            price: '990'
        },
        {
            name: 'Marrakech, Maroc',
            image: 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=600&auto=format',
            description: 'Saveurs, souks et désert du Sahara.',
            price: '690'
        }
    ];
    
    // Ajouter chaque destination dynamiquement
    destinations.forEach(dest => {
        const col = document.createElement('div');
        col.className = 'col-md-4';
        col.innerHTML = `
            <div class="destination-card">
                <img src="${dest.image}" class="destination-img" alt="${dest.name}">
                <h3>${dest.name}</h3>
                <p>${dest.description}</p>
                <div class="price">à partir de ${dest.price}€</div>
                <a href="#contact" class="btn btn-sm btn-outline-primary mt-2 rounded-pill">Réserver</a>
            </div>
        `;
        container.appendChild(col);
    });
    
    // Réobserver les nouvelles cartes
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.destination-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'all 0.6s ease-out';
        observer.observe(el);
    });
}

// ========== CHARGEMENT DYNAMIQUE DES SERVICES ==========
async function loadServices() {
    const container = document.querySelector('#services .row');
    if (!container || container.querySelector('.service-card')) return;
    
    const services = [
        { icon: 'fas fa-globe-americas', title: 'Voyages sur mesure', desc: 'Itinéraires uniques selon vos envies, circuits privés et expériences authentiques.' },
        { icon: 'fas fa-ticket-alt', title: 'Billets & Vols', desc: 'Meilleurs tarifs garantis, classes premium et assistance 24/7 pour vos départs.' },
        { icon: 'fas fa-hotel', title: 'Hôtels & Séjours', desc: 'Réservations dans des établissements d\'exception, du boutique au palace.' },
        { icon: 'fas fa-car', title: 'Transferts & Location', desc: 'Voitures de luxe, navettes VIP et autonomie totale sur votre destination.' },
        { icon: 'fas fa-umbrella-beach', title: 'Circuits & Croisières', desc: 'Évadez-vous sur les mers ou partez en road trip organisé, sans stress.' },
        { icon: 'fas fa-champagne-glasses', title: 'Lune de miel & Événements', desc: 'Séjours romantiques, demandes spéciales et célébrations inoubliables.' }
    ];
    
    services.forEach(service => {
        const col = document.createElement('div');
        col.className = 'col-md-4';
        col.innerHTML = `
            <div class="service-card">
                <i class="${service.icon} service-icon"></i>
                <h3>${service.title}</h3>
                <p>${service.desc}</p>
            </div>
        `;
        container.appendChild(col);
    });
}

// ========== PWA - SERVICE WORKER ==========
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
        .then(reg => console.log('✅ Service Worker enregistré', reg))
        .catch(err => console.log('❌ Erreur Service Worker:', err));
}

// ========== AJOUT DES ANIMATIONS CSS ==========
// Ajouter dynamiquement les animations si elles n'existent pas
const styleSheet = document.createElement('style');
styleSheet.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .toast-notification {
        animation: slideInRight 0.3s ease;
    }
    
    .scroll-top {
        position: fixed;
        bottom: 30px;
        right: 30px;
        background: linear-gradient(135deg, #8B5CF6, #3B82F6);
        color: white;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
        z-index: 999;
        border: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .scroll-top.show {
        opacity: 1;
        visibility: visible;
    }
    
    .scroll-top:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    .navbar-collapse {
        transition: all 0.3s ease;
    }
    
    @media (max-width: 991px) {
        .navbar-collapse {
            background: linear-gradient(135deg, #6B3FA0, #1E3A8A);
            padding: 20px;
            border-radius: 20px;
            margin-top: 15px;
        }
        
        .nav-link {
            text-align: center;
            padding: 12px !important;
        }
    }
`;
document.head.appendChild(styleSheet);

// ========== PRÉVENTION DES DOUBLONS ==========
console.log('✨ Kartners Travel Agency - Site dynamique chargé avec succès !');