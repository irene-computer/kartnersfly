/* Kartners Travel Agency — interactions communes du site public */
(function () {
    'use strict';
    document.documentElement.classList.add('js');
    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ---------- Traductions (fournies par la page, voir i18n.py) ---------- */
    var strings = {};
    try { strings = JSON.parse(document.getElementById('kta-i18n').textContent); } catch (e) {}
    function t(key) { return strings[key] || key; }
    window.ktaT = t;

    /* ---------- Notifications ---------- */
    function toast(message, type) {
        var box = document.querySelector('.toasts');
        if (!box) {
            box = document.createElement('div');
            box.className = 'toasts';
            box.setAttribute('role', 'status');
            box.setAttribute('aria-live', 'polite');
            document.body.appendChild(box);
        }
        var el = document.createElement('div');
        el.className = 'toast ' + (type || 'ok');
        var icon = document.createElement('i');
        icon.className = type === 'error' ? 'fas fa-circle-exclamation' : 'fas fa-circle-check';
        var text = document.createElement('span');
        text.textContent = message;
        el.append(icon, text);
        box.appendChild(el);
        setTimeout(function () { el.remove(); }, 5200);
    }
    window.ktaToast = toast;

    /* ---------- Envoi JSON commun aux formulaires ---------- */
    async function postJSON(url, data) {
        var res;
        try {
            res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify(data)
            });
        } catch (e) {
            return { success: false, message: t('Connexion impossible. Vérifiez votre réseau puis réessayez.') };
        }
        try {
            return await res.json();
        } catch (e) {
            return { success: false, message: t('Le serveur ne répond pas correctement. Réessayez dans un instant.') + ' (' + res.status + ')' };
        }
    }
    window.ktaPostJSON = postJSON;

    function setBusy(button, busy, label) {
        if (!button) return;
        if (busy) {
            button.dataset.label = button.innerHTML;
            button.disabled = true;
            button.innerHTML = '<span class="spinner" aria-hidden="true"></span> ' + (label || t('Envoi…'));
        } else {
            button.disabled = false;
            if (button.dataset.label) button.innerHTML = button.dataset.label;
        }
    }

    function showFormMessage(form, message, ok) {
        var box = form.querySelector('[data-form-message]');
        if (!box) { toast(message, ok ? 'ok' : 'error'); return; }
        box.hidden = false;
        box.className = 'alert ' + (ok ? 'alert-ok' : 'alert-error');
        box.textContent = message;
    }

    /*
     * Formulaire AJAX générique : <form data-ajax="/api/xxx">.
     * Valide les champs requis, envoie en JSON et affiche le résultat.
     */
    function bindAjaxForms(root) {
        (root || document).querySelectorAll('form[data-ajax]').forEach(function (form) {
            if (form.dataset.bound) return;
            form.dataset.bound = '1';
            form.addEventListener('submit', async function (e) {
                e.preventDefault();
                var box = form.querySelector('[data-form-message]');
                if (box) box.hidden = true;
                form.querySelectorAll('.is-invalid').forEach(function (el) { el.classList.remove('is-invalid'); });

                var firstInvalid = null;
                form.querySelectorAll('input, select, textarea').forEach(function (el) {
                    if (!el.checkValidity()) {
                        el.classList.add('is-invalid');
                        firstInvalid = firstInvalid || el;
                    }
                });
                if (firstInvalid) {
                    showFormMessage(form, t('Vérifiez les champs signalés en rouge.'), false);
                    firstInvalid.focus();
                    return;
                }

                var button = form.querySelector('[type="submit"]');
                setBusy(button, true);
                var data = Object.fromEntries(new FormData(form).entries());
                var tokenMeta = document.querySelector('meta[name="kta-form-token"]');
                data.form_token = tokenMeta ? tokenMeta.content : '';
                var result = await postJSON(form.dataset.ajax, data);
                setBusy(button, false);

                if (result.success) {
                    showFormMessage(form, result.message, true);
                    form.reset();
                    form.dispatchEvent(new CustomEvent('kta:success', { detail: result }));
                } else {
                    showFormMessage(form, result.message || t('Une erreur est survenue. Réessayez.'), false);
                }
            });
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        /* En-tête */
        var header = document.querySelector('.site-header');
        var onScroll = function () { header && header.classList.toggle('is-scrolled', window.scrollY > 8); };
        onScroll();
        window.addEventListener('scroll', onScroll, { passive: true });

        /* Menu mobile */
        var toggle = document.querySelector('.nav-toggle');
        var nav = document.getElementById('main-nav');
        if (toggle && nav) {
            var setOpen = function (open) {
                nav.classList.toggle('is-open', open);
                toggle.setAttribute('aria-expanded', String(open));
                toggle.innerHTML = open ? '<i class="fas fa-xmark"></i>' : '<i class="fas fa-bars"></i>';
            };
            toggle.addEventListener('click', function () { setOpen(!nav.classList.contains('is-open')); });
            nav.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', function () { setOpen(false); }); });
            document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setOpen(false); });
        }

        /* Diaporama du héros */
        var slides = document.querySelectorAll('.hero-slides span');
        if (slides.length > 1 && !reduceMotion) {
            var i = 0;
            setInterval(function () {
                slides[i].classList.remove('is-active');
                i = (i + 1) % slides.length;
                slides[i].classList.add('is-active');
            }, 6000);
        }

        /* Thème clair / sombre : choix mémorisé dans le navigateur */
        var themeBtn = document.querySelector('[data-theme-toggle]');
        if (themeBtn) {
            themeBtn.addEventListener('click', function () {
                var root = document.documentElement;
                var current = root.getAttribute('data-theme') ||
                    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
                var next = current === 'dark' ? 'light' : 'dark';
                var apply = function () { root.setAttribute('data-theme', next); };
                if (document.startViewTransition && !reduceMotion) document.startViewTransition(apply); else apply();
                try { localStorage.setItem('kta-theme', next); } catch (e) {}
                themeBtn.setAttribute('aria-pressed', String(next === 'dark'));
                toast(t(next === 'dark' ? 'Thème sombre activé' : 'Thème clair activé'), 'ok');
            });
        }

        /* Cascade : chaque élément d'une grille apparaît un peu après le précédent */
        document.querySelectorAll('.stagger').forEach(function (group) {
            Array.prototype.forEach.call(group.children, function (child, index) {
                child.style.setProperty('--i', String(index % 6));
            });
        });

        /* Chiffres qui défilent jusqu'à leur valeur */
        var counters = document.querySelectorAll('[data-count]');
        var runCounter = function (el) {
            var end = parseInt(el.getAttribute('data-count'), 10);
            if (!end || reduceMotion) return;
            var start = performance.now(), duration = 1200;
            var step = function (now) {
                var p = Math.min(1, (now - start) / duration);
                el.textContent = String(Math.round(end * (1 - Math.pow(1 - p, 3))));
                if (p < 1) requestAnimationFrame(step);
            };
            requestAnimationFrame(step);
        };
        if ('IntersectionObserver' in window && counters.length) {
            var co = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) { runCounter(entry.target); co.unobserve(entry.target); }
                });
            }, { threshold: .6 });
            counters.forEach(function (el) { co.observe(el); });
        }

        /* Inclinaison 3D légère des cartes sous la souris (ordinateur uniquement) */
        if (!reduceMotion && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
            document.querySelectorAll('.pass, .lift').forEach(function (card) {
                card.addEventListener('pointermove', function (e) {
                    var r = card.getBoundingClientRect();
                    var x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
                    card.style.setProperty('--ry', (x * 6).toFixed(2) + 'deg');
                    card.style.setProperty('--rx', (-y * 6).toFixed(2) + 'deg');
                });
                card.addEventListener('pointerleave', function () {
                    card.style.removeProperty('--rx'); card.style.removeProperty('--ry');
                });
            });
        }

        /* Apparition au défilement */
        var reveals = document.querySelectorAll('.reveal');
        if ('IntersectionObserver' in window) {
            var io = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) { entry.target.classList.add('is-visible'); io.unobserve(entry.target); }
                });
            }, { rootMargin: '0px 0px -40px 0px' });
            reveals.forEach(function (el) { io.observe(el); });
        } else {
            reveals.forEach(function (el) { el.classList.add('is-visible'); });
        }

        /* Fenêtres : fermeture par bouton ou clic sur le fond */
        document.querySelectorAll('dialog.modal').forEach(function (dlg) {
            dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
            dlg.querySelectorAll('[data-close]').forEach(function (b) { b.addEventListener('click', function () { dlg.close(); }); });
        });

        /* Boutons "copier" */
        document.querySelectorAll('[data-copy]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var value = btn.getAttribute('data-copy');
                var done = function () { toast(t('Copié :') + ' ' + value, 'ok'); };
                if (navigator.clipboard) navigator.clipboard.writeText(value).then(done, function () { toast(value, 'ok'); });
                else toast(value, 'ok');
            });
        });

        /* Images manquantes : on affiche le visuel de remplacement */
        document.querySelectorAll('img[data-fallback]').forEach(function (img) {
            var swap = function () {
                img.hidden = true;
                var ph = img.parentElement && img.parentElement.querySelector('.placeholder');
                if (ph) ph.hidden = false;
            };
            if (img.complete && img.naturalWidth === 0) swap();
            img.addEventListener('error', swap);
        });

        /* Drapeaux externes indisponibles : on les masque plutôt qu'une icône cassée */
        document.querySelectorAll('.pass-flag, .scholar-country img, .region img, img[src^="https://flagcdn.com"]').forEach(function (img) {
            var hide = function () { img.hidden = true; };
            if (img.complete && img.naturalWidth === 0) hide();
            img.addEventListener('error', hide);
        });

        var filters = document.getElementById('filters');
        if (filters) filters.addEventListener('submit', function (e) { e.preventDefault(); });

        bindAjaxForms(document);
    });

    /* Service worker (mode hors ligne / installation) */
    if ('serviceWorker' in navigator && location.protocol === 'https:') {
        window.addEventListener('load', function () {
            navigator.serviceWorker.register('/sw.js').catch(function () {});
        });
    }
})();
