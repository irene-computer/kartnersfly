"""
Traduction français → anglais du site public.

Le français est la langue source : chaque texte affiché passe par `_()` avec
sa version française comme clé. Pour ajouter ou corriger une traduction
anglaise, modifiez simplement le dictionnaire EN ci-dessous.

Langue choisie : paramètre ?lang=fr|en (mémorisé dans un cookie), sinon la
langue préférée du navigateur, sinon le français.
"""
from flask import g, request

LANGUAGES = ('fr', 'en')
DEFAULT_LANGUAGE = 'fr'
COOKIE_NAME = 'kta_lang'

EN = {
    # --- Navigation, en-tête, pied de page ---
    'Accueil': 'Home',
    'Destinations': 'Destinations',
    'Services': 'Services',
    "Bourses d'études": 'Scholarships',
    'À propos': 'About us',
    'Contact': 'Contact',
    'Aller au contenu': 'Skip to content',
    'Kartners Travel Agency, accueil': 'Kartners Travel Agency, home',
    'Navigation principale': 'Main navigation',
    'Réserver': 'Book',
    'Changer de thème (clair / sombre)': 'Switch theme (light / dark)',
    'Thème clair / sombre': 'Light / dark theme',
    'Écrire sur WhatsApp': 'Message us on WhatsApp',
    'Ouvrir le menu': 'Open menu',
    "Votre agence à Douala pour les billets d'avion, les visas, les hôtels et les études à l'étranger. « Voyagez, comme vous l'imaginez. »":
        'Your Douala travel agency for flights, visas, hotels and studying abroad. "Travel the way you imagine it."',
    'Billetterie aérienne': 'Flight tickets',
    'Assistance visa': 'Visa assistance',
    'Réservation hôtelière': 'Hotel booking',
    'Pré-enrôlement passeport / CNI': 'Passport / ID pre-enrolment',
    'Agence': 'Agency',
    'Logpom, Douala, Cameroun': 'Logpom, Douala, Cameroon',
    'Lun – sam : 08:00 – 18:00': 'Mon – Sat: 8 am – 6 pm',
    'Bons plans': 'Deals',
    'Promotions sur les billets et nouvelles bourses, une à deux fois par mois.': 'Ticket deals and new scholarships, once or twice a month.',
    'Adresse email': 'Email address',
    'vous@exemple.com': 'you@example.com',
    "S'inscrire": 'Subscribe',
    'Informations légales': 'Legal information',
    'Mentions légales': 'Legal notice',
    'CGV': 'Terms of sale',
    'Confidentialité': 'Privacy',
    'Discuter avec un conseiller sur WhatsApp': 'Chat with an advisor on WhatsApp',
    "Kartners Travel Agency, agence de voyages à Douala : billetterie aérienne, assistance visa, réservation d'hôtels, pré-enrôlement et bourses d'études à l'étranger.":
        'Kartners Travel Agency, travel agency in Douala: flight tickets, visa assistance, hotel bookings, passport pre-enrolment and scholarships to study abroad.',
    "Voyagez, comme vous l'imaginez. Billets d'avion, visas, hôtels et bourses d'études depuis Douala.":
        'Travel the way you imagine it. Flights, visas, hotels and scholarships from Douala.',

    # --- Accueil ---
    "Voyagez, comme vous l'imaginez": 'Travel the way you imagine it',
    'Agence de voyages à Douala': 'Travel agency in Douala',
    'Voyagez,': 'Travel',
    "comme vous l'imaginez.": 'the way you imagine it.',
    "Billets d'avion, visa, hôtel, passeport ou bourse d'études : un conseiller Kartners prépare tout votre départ, de la première question jusqu'à l'embarquement.":
        'Flights, visa, hotel, passport or scholarship: a Kartners advisor prepares your whole trip, from your first question to boarding.',
    'Voir les destinations': 'See destinations',
    "Étudier à l'étranger": 'Study abroad',
    'Où voulez-vous aller ?': 'Where do you want to go?',
    'Départ de Douala. Un conseiller confirme le prix sous 24 h.': 'Departing from Douala. An advisor confirms the price within 24 hours.',
    'Départ': 'From',
    'Arrivée': 'To',
    'Ville ou pays': 'City or country',
    'Paris, Canada, Dubaï…': 'Paris, Canada, Dubai…',
    'Rechercher': 'Search',
    'destinations au départ de Douala': 'destinations from Douala',
    'pour une réponse à votre demande': 'to answer your request',
    'services sous un même toit': 'services under one roof',
    'Lun – sam': 'Mon – Sat',
    'agence ouverte de 8 h à 18 h': 'office open 8 am to 6 pm',
    'Les meilleurs tarifs du moment': 'Best fares right now',
    "Prix indicatifs par personne, au départ de Douala. Choisissez une destination, un conseiller vous rappelle avec l'offre exacte.":
        'Indicative prices per person, departing from Douala. Pick a destination and an advisor will call you back with the exact offer.',
    'Toutes les destinations': 'All destinations',
    'Destinations bientôt en ligne': 'Destinations coming soon',
    'Appelez-nous pour un devis personnalisé.': 'Call us for a personalised quote.',
    'Tout votre départ, au même endroit': 'Your whole trip, in one place',
    'Inutile de courir entre plusieurs bureaux : nous gérons les démarches administratives et la logistique du voyage.':
        'No need to run between offices: we handle the paperwork and the travel logistics.',
    'Détail des services': 'Service details',
    'Comment ça marche': 'How it works',
    "Quatre étapes jusqu'à l'embarquement": 'Four steps to boarding',
    'Vous choisissez': 'You choose',
    'Une destination sur le site, ou un projet à nous expliquer par WhatsApp.': 'A destination on the website, or a plan to tell us about on WhatsApp.',
    'On vous rappelle': 'We call you back',
    'Sous 24 h, avec le meilleur tarif disponible et la liste des documents.': 'Within 24 hours, with the best available fare and the list of documents.',
    'On prépare le dossier': 'We prepare your file',
    'Billet, visa, hôtel, assurance : nous suivons chaque démarche.': 'Ticket, visa, hotel, insurance: we follow up every step.',
    'Vous partez': 'You travel',
    'Billet en main, avec un conseiller joignable pendant le voyage.': 'Ticket in hand, with an advisor you can reach during your trip.',
    "Étudier à l'étranger, dossier et visa compris": 'Study abroad, application and visa included',
    'Recherche de bourse, constitution du dossier académique et visa étudiant, avec un seul interlocuteur.':
        'Scholarship search, academic application and student visa, with a single point of contact.',
    'Voir les bourses': 'See scholarships',
    "Jusqu'au": 'Until',
    'France': 'France',
    'Canada': 'Canada',
    'Belgique': 'Belgium',
    'Allemagne': 'Germany',
    'Bourses provinciales': 'Provincial scholarships',
    'Bourses ARES': 'ARES scholarships',
    'Un projet de voyage ? Parlons-en.': "Planning a trip? Let's talk.",
    'Dites-nous où et quand vous voulez partir : nous revenons vers vous avec une proposition claire, sans engagement.':
        'Tell us where and when you want to go: we will come back to you with a clear, no-obligation offer.',
    'Demander un devis': 'Get a quote',
    'Nous contacter': 'Contact us',

    # --- Cartes destinations ---
    'Europe': 'Europe',
    'Afrique': 'Africa',
    'Asie & Moyen-Orient': 'Asia & Middle East',
    'Amériques': 'Americas',
    'Océanie': 'Oceania',
    'Drapeau': 'Flag',
    'Vol Douala vers': 'Flight from Douala to',
    'À partir de': 'From',

    # --- Destinations ---
    'Toutes nos destinations au départ de Douala : Europe, Afrique, Amériques, Asie. Prix indicatifs et réservation en ligne, confirmée par un conseiller sous 24 h.':
        'All our destinations from Douala: Europe, Africa, the Americas, Asia. Indicative prices and online booking, confirmed by an advisor within 24 hours.',
    'Départs depuis Douala': 'Departures from Douala',
    'Nos destinations': 'Our destinations',
    'Filtrez par continent ou par budget, puis envoyez votre demande. Un conseiller vous confirme le tarif exact et les disponibilités sous 24 h.':
        'Filter by continent or budget, then send your request. An advisor confirms the exact fare and availability within 24 hours.',
    'Continent': 'Continent',
    'Tous': 'All',
    'Budget par personne': 'Budget per person',
    'Tous les prix': 'Any price',
    'Moins de 650 000 FCFA': 'Under 650,000 FCFA',
    '650 000 à 1 300 000 FCFA': '650,000 to 1,300,000 FCFA',
    'Plus de 1 300 000 FCFA': 'Over 1,300,000 FCFA',
    'Trier': 'Sort by',
    'Nom (A → Z)': 'Name (A → Z)',
    'Prix croissant': 'Price, low to high',
    'Prix décroissant': 'Price, high to low',
    'destination': 'destination',
    'destinations': 'destinations',
    'Réinitialiser les filtres': 'Reset filters',
    'Aucune destination ne correspond': 'No matching destination',
    'Nous organisons aussi des voyages vers des villes absentes de cette liste.': 'We also organise trips to cities that are not on this list.',
    'Demander une autre destination': 'Ask for another destination',
    'Destinations en cours de mise à jour': 'Destinations are being updated',
    'Contactez-nous directement pour un devis.': 'Contact us directly for a quote.',
    'Prix indicatifs en francs CFA (1 € = 655,957 FCFA), à confirmer par un conseiller selon les dates et la disponibilité.':
        'Indicative prices in CFA francs (€1 = 655.957 FCFA), to be confirmed by an advisor depending on dates and availability.',
    "Votre ville n'est pas dans la liste ?": "Your city isn't listed?",
    'Nous réservons des vols vers toutes les destinations desservies depuis Douala et Yaoundé, et nous montons des circuits sur mesure.':
        'We book flights to every destination served from Douala and Yaoundé, and we build tailor-made tours.',
    'Demande de réservation': 'Booking request',
    'Sans paiement en ligne : un conseiller vous rappelle pour confirmer.': 'No online payment: an advisor calls you back to confirm.',
    'Fermer': 'Close',
    'Destination': 'Destination',
    'Nom complet': 'Full name',
    'Comme sur le passeport': 'As shown on your passport',
    'Email': 'Email',
    'Téléphone / WhatsApp': 'Phone / WhatsApp',
    'Date de départ': 'Departure date',
    'Voyageurs': 'Travellers',
    'Précisions': 'Details',
    'Aller simple ou aller-retour, date de retour, hôtel souhaité, besoin de visa…': 'One-way or return, return date, preferred hotel, visa needed…',
    'Envoyer ma demande': 'Send my request',
    'Vos coordonnées servent uniquement à traiter cette demande.': 'Your details are only used to handle this request.',

    # --- Services ---
    "Billetterie aérienne, assistance visa, réservation d'hôtels, pré-enrôlement passeport et CNI, planification de voyage et assurance : les services de Kartners Travel Agency à Douala.":
        'Flight tickets, visa assistance, hotel bookings, passport and ID pre-enrolment, trip planning and insurance: Kartners Travel Agency services in Douala.',
    'Nos services': 'Our services',
    "Des démarches administratives jusqu'à l'embarquement : nous prenons en charge chaque étape de votre projet de voyage, d'études ou d'affaires.":
        'From paperwork to boarding: we take care of every step of your travel, study or business plans.',
    'Services en cours de mise à jour': 'Services are being updated',
    'Contactez-nous pour toute demande.': 'Contact us with any request.',
    'Pays pour lesquels nous montons des dossiers': 'Countries we prepare visa applications for',
    "Visas d'études, de tourisme et d'affaires. Votre pays n'apparaît pas ? Demandez-nous, la liste n'est pas limitative.":
        "Study, tourist and business visas. Your country isn't listed? Ask us, this list is not exhaustive.",
    'Amériques & Asie': 'Americas & Asia',
    'Italie': 'Italy',
    'Espagne': 'Spain',
    'Pays-Bas': 'Netherlands',
    'Suisse': 'Switzerland',
    'Royaume-Uni': 'United Kingdom',
    'États-Unis': 'United States',
    'Chine': 'China',
    'Émirats arabes unis': 'United Arab Emirates',
    'Turquie': 'Türkiye',
    'Maroc': 'Morocco',
    'Afrique du Sud': 'South Africa',
    'Sénégal': 'Senegal',
    "Côte d'Ivoire": "Côte d'Ivoire",
    'Gabon': 'Gabon',
    'Notre méthode': 'How we work',
    'Pourquoi passer par Kartners': 'Why choose Kartners',
    'Rapidité et rigueur': 'Fast and thorough',
    'Des conseillers qui connaissent les exigences des consulats et vérifient chaque pièce avant le dépôt.':
        'Advisors who know consulate requirements and check every document before submission.',
    'Un conseiller dédié': 'A dedicated advisor',
    'Une seule personne suit votre dossier, joignable par téléphone et WhatsApp.': 'One person follows your file, reachable by phone and WhatsApp.',
    "Tarifs annoncés à l'avance": 'Prices agreed upfront',
    'Le prix de notre accompagnement est fixé avant le début des démarches, sans frais cachés.': 'Our fee is set before we start, with no hidden costs.',
    'Un réseau de partenaires': 'A network of partners',
    "Compagnies aériennes, hôtels, assureurs et établissements d'enseignement à l'étranger.": 'Airlines, hotels, insurers and schools abroad.',
    'Prêt à lancer votre projet ?': 'Ready to get started?',
    'Une première étude de votre dossier est gratuite. Dites-nous ce dont vous avez besoin.': 'Your first file review is free. Tell us what you need.',
    'Demander un devis gratuit': 'Get a free quote',

    # --- Bourses ---
    "Bourses d'études & visa étudiant": 'Scholarships & student visas',
    "Bourses d'études à l'étranger : recherche de bourse, dossier académique et visa étudiant avec Kartners Travel Agency, Douala. France, Canada, Belgique, Allemagne, Maroc, Turquie.":
        'Scholarships to study abroad: scholarship search, academic application and student visa with Kartners Travel Agency, Douala. France, Canada, Belgium, Germany, Morocco, Türkiye.',
    'ÉTUDES': 'STUDY',
    'Bourses & visa étudiant': 'Scholarships & student visa',
    "Du dossier de bourse à l'embarquement,": 'From scholarship application to boarding,',
    'un seul interlocuteur.': 'one point of contact.',
    'Nous cherchons les bourses adaptées à votre profil, montons votre dossier académique et préparons votre visa étudiant.':
        'We find scholarships that match your profile, build your academic application and prepare your student visa.',
    'Déposer ma candidature': 'Apply now',
    'Poser une question': 'Ask a question',
    'Ce que nous suivons pour vous': 'What we handle for you',
    'Dossier étudiant': 'Student file',
    "Bilan d'éligibilité gratuit": 'Free eligibility check',
    'Recherche et candidature aux bourses': 'Scholarship search and applications',
    'Relevés, traductions, lettre de motivation': 'Transcripts, translations, cover letter',
    "Préparation à l'entretien consulaire": 'Consulate interview preparation',
    "Billet d'avion tarif étudiant": 'Student airfare',
    'dossiers accompagnés': 'students supported',
    'pays de destination': 'destination countries',
    'de visas obtenus': 'visa success rate',
    'pour un premier retour': 'for a first answer',
    'Opportunités': 'Opportunities',
    'Bourses ouvertes en ce moment': 'Scholarships open now',
    'Mises à jour par notre équipe. Les bourses dont la date limite est passée sont retirées automatiquement.':
        'Updated by our team. Scholarships past their deadline are removed automatically.',
    'Dès le': 'From',
    'Candidatures ouvertes': 'Applications open',
    'Détails': 'Details',
    'Aucune bourse publiée pour le moment': 'No scholarships published yet',
    "Déposez votre profil ci-dessous : nous vous prévenons dès qu'une bourse vous correspond.": 'Submit your profile below: we will let you know as soon as a scholarship matches it.',
    'Déposer mon profil': 'Submit my profile',
    'Le parcours': 'The process',
    'Quatre étapes, un accompagnement continu': 'Four steps, continuous support',
    "Chaque dossier suit le même fil, du bilan initial jusqu'à l'arrivée sur le campus.": 'Every application follows the same path, from the first assessment to arrival on campus.',
    'Bilan et orientation': 'Assessment and guidance',
    'Profil académique, budget, pays et filières compatibles avec vos objectifs.': 'Academic profile, budget, countries and programmes that fit your goals.',
    'Recherche de bourse': 'Scholarship search',
    'Programmes gouvernementaux, universitaires, Campus France, DAAD… et dépôt des candidatures.': 'Government and university programmes, Campus France, DAAD… and application submission.',
    'Constitution du dossier': 'Building your file',
    'Relevés de notes, traductions, légalisations, lettre de motivation et CV académique.': 'Transcripts, translations, certifications, cover letter and academic CV.',
    'Visa et départ': 'Visa and departure',
    "Entretien consulaire, dépôt du visa, billet d'avion et briefing avant le départ.": 'Consulate interview, visa submission, flight ticket and pre-departure briefing.',
    'Où partent nos étudiants': 'Where our students go',
    "Campus France, bourses d'excellence": 'Campus France, excellence scholarships',
    'Bourses provinciales et universitaires': 'Provincial and university scholarships',
    'Bourses ARES, universités francophones': 'ARES scholarships, French-speaking universities',
    'Bourses AMCI, filières techniques': 'AMCI scholarships, technical programmes',
    "Türkiye Bursları (bourses d'État)": 'Türkiye Bursları (government scholarships)',
    'DAAD, frais universitaires réduits': 'DAAD, low tuition fees',
    'Formules': 'Packages',
    'Un accompagnement adapté à votre avancement': 'Support that fits where you are',
    "Tarif communiqué après le bilan gratuit, selon le pays visé et l'état de votre dossier.": 'Price given after the free assessment, depending on the country and how far along your file is.',
    'Orientation': 'Guidance',
    "Pour cadrer votre projet d'études.": 'To shape your study plans.',
    'Évaluation du profil académique': 'Academic profile review',
    'Pays et filières éligibles': 'Eligible countries and programmes',
    'Liste des bourses accessibles': 'List of scholarships you can apply for',
    'Feuille de route personnalisée': 'Personalised roadmap',
    'Démarrer le bilan': 'Start the assessment',
    'Formule complète': 'Full package',
    'Bourse, dossier et visa': 'Scholarship, file and visa',
    'Un accompagnement de bout en bout.': 'End-to-end support.',
    'Recherche et candidature à la bourse': 'Scholarship search and application',
    'Dossier académique complet': 'Complete academic file',
    "Préparation à l'entretien de visa": 'Visa interview preparation',
    'Dépôt et suivi consulaire': 'Consulate submission and follow-up',
    "Réservation du billet d'avion": 'Flight booking',
    'Après le visa': 'After the visa',
    'Accompagnement au départ': 'Departure support',
    'Pour arriver sans imprévu.': 'For a smooth arrival.',
    'Logement étudiant': 'Student housing',
    'Assurance voyage et santé': 'Travel and health insurance',
    "Aide à l'arrivée et à l'installation": 'Help on arrival and settling in',
    'En savoir plus': 'Learn more',
    'Candidature': 'Application',
    "Déposez votre dossier d'études": 'Submit your study application',
    'Notre équipe étudie votre éligibilité et vous recontacte sous 24 h.': 'Our team reviews your eligibility and gets back to you within 24 hours.',
    "Niveau d'études actuel": 'Current level of study',
    'Choisir': 'Choose',
    'Baccalauréat': 'High school diploma (Baccalauréat)',
    'Licence (Bac + 3)': "Bachelor's degree",
    'Master (Bac + 5)': "Master's degree",
    'Doctorat': 'PhD',
    'Autre': 'Other',
    'Pays souhaité': 'Preferred country',
    'Autre destination': 'Other destination',
    "Domaine d'études visé": 'Field of study',
    'Médecine / Santé': 'Medicine / Health',
    'Ingénierie / Technologie': 'Engineering / Technology',
    'Commerce / Gestion': 'Business / Management',
    'Droit': 'Law',
    'Lettres / Arts': 'Humanities / Arts',
    'Sciences fondamentales': 'Natural sciences',
    'Informatique / Data': 'Computer science / Data',
    'Votre projet': 'Your plans',
    'Bourse visée, moyenne, niveau de langue, date de rentrée souhaitée…': 'Target scholarship, grade average, language level, preferred start date…',
    'Envoyer ma candidature': 'Send my application',
    'Vos informations restent confidentielles et ne sont utilisées que pour votre dossier.': 'Your information stays confidential and is only used for your application.',
    'Questions fréquentes': 'Frequently asked questions',
    'Avant de vous lancer': 'Before you start',
    'Comment savoir si je suis éligible à une bourse ?': 'How do I know if I am eligible for a scholarship?',
    'Nous étudions gratuitement votre dossier (relevés de notes, diplômes, niveau de langue) pour identifier les bourses et destinations où vos chances sont les meilleures.':
        'We review your file for free (transcripts, diplomas, language level) to find the scholarships and destinations where your chances are best.',
    'Quand faut-il candidater ?': 'When should I apply?',
    "Les campagnes ouvrent en général 6 à 10 mois avant la rentrée. Pour une rentrée en septembre, commencez à préparer votre dossier dès octobre de l'année précédente.":
        'Applications usually open 6 to 10 months before the start of the academic year. For a September start, begin preparing your file in October of the previous year.',
    "Garantissez-vous l'obtention du visa ?": 'Do you guarantee the visa?',
    'Non : la décision appartient uniquement aux ambassades et consulats. Notre taux de réussite de 87 % repose sur un contrôle rigoureux de chaque pièce du dossier.':
        'No: the decision belongs solely to embassies and consulates. Our 87% success rate comes from carefully checking every document in the file.',
    'Puis-je partir sans bourse, avec un financement personnel ?': 'Can I go without a scholarship, with my own funding?',
    "Oui. L'accompagnement pour l'admission et le visa est disponible quel que soit votre mode de financement.": 'Yes. Admission and visa support is available however you fund your studies.',
    "Prêt à étudier à l'étranger ?": 'Ready to study abroad?',
    "Rejoignez les étudiants que nous avons accompagnés jusqu'à leur campus.": "Join the students we've helped reach their campus.",
    'Déposer mon dossier': 'Submit my file',
    'Description': 'Description',
    'Avantages': 'Benefits',
    'Conditions': 'Requirements',
    'Je suis intéressé·e': "I'm interested",

    # --- Contact ---
    'Contactez Kartners Travel Agency à Logpom, Douala : téléphone, WhatsApp, email et formulaire. Réponse sous 24 h, du lundi au samedi.':
        'Contact Kartners Travel Agency in Logpom, Douala: phone, WhatsApp, email and form. Reply within 24 hours, Monday to Saturday.',
    'Délai de réponse': 'Reply time',
    'Parlons de votre projet': "Let's talk about your trip",
    "Par téléphone, WhatsApp, email ou à l'agence de Logpom. Nous répondons du lundi au samedi.": 'By phone, WhatsApp, email or at our Logpom office. We reply Monday to Saturday.',
    'Téléphone': 'Phone',
    'Copier le numéro': 'Copy number',
    'Écrire à un conseiller': 'Message an advisor',
    "Copier l'adresse email": 'Copy email address',
    'Lundi – samedi': 'Monday – Saturday',
    'Dimanche et jours fériés': 'Sundays and public holidays',
    'Fermé': 'Closed',
    'Discuter sur WhatsApp': 'Chat on WhatsApp',
    'Envoyez-nous un message': 'Send us a message',
    'Décrivez votre besoin, nous revenons vers vous sous 24 h.': 'Tell us what you need and we will get back to you within 24 hours.',
    'Service concerné': 'Service',
    'Choisir un service': 'Choose a service',
    'Pré-enrôlement': 'Passport / ID pre-enrolment',
    'Planification de voyage': 'Trip planning',
    'Assurance voyage': 'Travel insurance',
    "Bourse d'études": 'Scholarship',
    'Autre demande': 'Other request',
    'Message': 'Message',
    'Destination, dates, nombre de voyageurs, type de visa…': 'Destination, dates, number of travellers, type of visa…',
    'Envoyer le message': 'Send message',
    'Vos informations restent confidentielles.': 'Your information stays confidential.',
    'Carte : Logpom, Douala': 'Map: Logpom, Douala',
    'Itinéraire dans Google Maps': 'Directions in Google Maps',

    # --- À propos ---
    'Kartners Travel Agency, agence de voyages à Logpom, Douala : notre histoire, nos services et notre façon de travailler.':
        'Kartners Travel Agency, travel agency in Logpom, Douala: our story, our services and how we work.',
    'Les architectes de vos voyages, depuis Douala.': 'The architects of your travels, from Douala.',
    "Kartners Travel Agency accompagne particuliers, étudiants et professionnels dans tous leurs projets de voyage. Nous réunissons l'expertise locale et un réseau international pour proposer un service sur mesure, de la préparation administrative jusqu'à l'embarquement.":
        'Kartners Travel Agency supports individuals, students and professionals with all their travel plans. We combine local expertise with an international network to offer a tailor-made service, from paperwork to boarding.',
    "Billet d'avion, visa, hôtel, passeport, bourse d'études : vous gardez un seul interlocuteur, qui connaît votre dossier et reste joignable pendant tout le voyage.":
        'Flight, visa, hotel, passport, scholarship: you keep one point of contact who knows your file and stays reachable throughout your trip.',
    "« Voyagez, comme vous l'imaginez. » Ce n'est pas un slogan, c'est notre promesse.": '"Travel the way you imagine it." It is not a slogan, it is our promise.',
    "Monuments du monde entier réunis autour d'un globe": 'Landmarks from around the world gathered around a globe',
    'Ce que nous faisons': 'What we do',
    'Plusieurs métiers, un même suivi': 'Many services, one follow-up',
    'Recherche de bourse, dossier académique et visa étudiant.': 'Scholarship search, academic file and student visa.',
    'Nos engagements': 'Our commitments',
    'Ce que vous pouvez attendre de nous': 'What you can expect from us',
    'Rapidité': 'Speed',
    'Une réponse à chaque demande sous 24 h.': 'An answer to every request within 24 hours.',
    'Fiabilité': 'Reliability',
    'Des dossiers vérifiés pièce par pièce.': 'Files checked document by document.',
    'Transparence': 'Transparency',
    'Le prix est annoncé avant de commencer.': 'The price is agreed before we start.',
    'Disponibilité': 'Availability',
    'Un conseiller joignable par téléphone et WhatsApp.': 'An advisor you can reach by phone and WhatsApp.',
    'Passez nous voir à Logpom': 'Visit us in Logpom',
    'Ou écrivez-nous : votre voyage commence par une conversation.': 'Or write to us: your trip starts with a conversation.',

    # --- Erreurs ---
    'Erreur': 'Error',
    'Page introuvable': 'Page not found',
    'Une erreur est survenue de notre côté.': 'Something went wrong on our side.',
    "Cette page n'a pas décollé.": "This page didn't take off.",
    'Réessayez dans quelques instants ou contactez-nous directement.': 'Please try again in a moment or contact us directly.',
    "L'adresse est peut-être incorrecte, ou la page a été déplacée.": 'The address may be wrong, or the page has moved.',
    "Retour à l'accueil": 'Back to home',

    # --- Messages du serveur (formulaires) ---
    'Merci ! Notre équipe vous répond sous 24 h.': 'Thank you! Our team will reply within 24 hours.',
    'Candidature reçue ! Un conseiller vous recontacte sous 24 h.': 'Application received! An advisor will contact you within 24 hours.',
    'Demande envoyée. Un conseiller vous contacte sous 24 h pour confirmer.': 'Request sent. An advisor will contact you within 24 hours to confirm.',
    'Demande {ref} envoyée. Un conseiller vous contacte sous 24 h pour confirmer.': 'Request {ref} sent. An advisor will contact you within 24 hours to confirm.',
    'Inscription confirmée. À bientôt dans votre boîte mail !': "You're subscribed. See you in your inbox!",
    'La page a expiré. Rechargez-la puis renvoyez le formulaire.': 'This page has expired. Reload it and send the form again.',
    'Vous avez envoyé beaucoup de demandes. Réessayez dans une heure ou appelez-nous.': 'You have sent a lot of requests. Try again in an hour or call us.',
    'Merci de renseigner votre nom, votre email et votre message.': 'Please enter your name, email and message.',
    'Adresse email invalide.': 'Invalid email address.',
    'Message trop long (2000 caractères maximum).': 'Message too long (2,000 characters maximum).',
    "Votre message n'a pas pu être enregistré. Réessayez ou appelez-nous.": 'Your message could not be saved. Please try again or call us.',
    'Le champ « {label} » est obligatoire.': 'The "{label}" field is required.',
    "Votre candidature n'a pas pu être enregistrée. Réessayez.": 'Your application could not be saved. Please try again.',
    'Date de départ invalide.': 'Invalid departure date.',
    "La date de départ doit être aujourd'hui ou plus tard.": 'The departure date must be today or later.',
    'Le nombre de voyageurs doit être compris entre 1 et 50.': 'The number of travellers must be between 1 and 50.',
    "La réservation n'a pas pu être enregistrée. Réessayez.": 'Your booking could not be saved. Please try again.',
    'Inscription impossible pour le moment. Réessayez plus tard.': 'Subscription is unavailable right now. Please try again later.',
    'Ressource introuvable': 'Not found',
    'Trop de tentatives. Patientez une minute puis réessayez.': 'Too many attempts. Wait a minute and try again.',
    'Erreur interne. Réessayez dans un instant.': 'Internal error. Please try again in a moment.',
    # libellés de champs (messages d'erreur)
    'nom complet': 'full name', 'email': 'email', 'téléphone': 'phone', 'date de départ': 'departure date',
    'pays souhaité': 'preferred country', "niveau d'études": 'level of study', "domaine d'études": 'field of study',
}

# Textes utilisés par le JavaScript (static/js/kta.js et scripts des pages).
JS_KEYS = [
    'destination', 'destinations', 'Réserver :', 'Du', 'au', "Jusqu'au", 'À partir du', 'Candidatures ouvertes',
    'Intéressé·e par :', 'Envoi…', 'Vérifiez les champs signalés en rouge.',
    'Connexion impossible. Vérifiez votre réseau puis réessayez.', 'Une erreur est survenue. Réessayez.',
    'Le serveur ne répond pas correctement. Réessayez dans un instant.', 'Copié :',
    'Thème sombre activé', 'Thème clair activé',
]
EN.update({
    'Réserver :': 'Book:', 'Du': 'From', 'au': 'to', 'À partir du': 'From',
    'Intéressé·e par :': 'Interested in:', 'Envoi…': 'Sending…',
    'Vérifiez les champs signalés en rouge.': 'Please check the fields highlighted in red.',
    'Connexion impossible. Vérifiez votre réseau puis réessayez.': 'Connection failed. Check your network and try again.',
    'Une erreur est survenue. Réessayez.': 'Something went wrong. Please try again.',
    'Le serveur ne répond pas correctement. Réessayez dans un instant.': 'The server is not responding properly. Please try again in a moment.',
    'Copié :': 'Copied:', 'Thème sombre activé': 'Dark theme on', 'Thème clair activé': 'Light theme on',
})


def get_lang():
    lang = getattr(g, 'lang', None)
    if lang:
        return lang
    lang = DEFAULT_LANGUAGE
    try:
        asked = (request.args.get('lang') or '').lower()
        if asked in LANGUAGES:
            lang = asked
        elif request.cookies.get(COOKIE_NAME) in LANGUAGES:
            lang = request.cookies.get(COOKIE_NAME)
        else:
            lang = request.accept_languages.best_match(LANGUAGES, default=DEFAULT_LANGUAGE)
    except RuntimeError:
        pass  # hors requête
    g.lang = lang
    return lang


def gettext(text, **kwargs):
    if get_lang() == 'en':
        text = EN.get(text, text)
    return text.format(**kwargs) if kwargs else text


def translate_field(row, field):
    """Champ en base dans la langue courante (repli sur le français)."""
    if row is None:
        return ''
    try:
        value = row[field]
    except (KeyError, IndexError):
        value = ''
    if get_lang() == 'en':
        try:
            en = row[f'{field}_en']
        except (KeyError, IndexError):
            en = None
        if en:
            return en
    return value or ''


def js_strings():
    return {key: gettext(key) for key in JS_KEYS}
