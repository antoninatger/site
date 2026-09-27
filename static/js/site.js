// antoninatger.com — menu mobile, menu Jeux, apparitions au défilement, vidéos chargées au clic, formulaires.
(function () {
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.querySelector('.nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // Menu Jeux : clic (et survol sur ordinateur) ; Échap ou clic ailleurs pour fermer
  var mj = document.querySelector('.menu-jeux'), bj = mj && mj.querySelector('.menu-jeux__bouton');
  if (mj && bj) {
    var survol = window.matchMedia('(hover: hover) and (min-width: 901px)');
    var ouvrir = function () { mj.classList.add('ouvert'); bj.setAttribute('aria-expanded', 'true'); };
    var fermer = function () { mj.classList.remove('ouvert'); bj.setAttribute('aria-expanded', 'false'); };
    bj.addEventListener('click', function () { mj.classList.contains('ouvert') ? fermer() : ouvrir(); });
    mj.addEventListener('mouseenter', function () { if (survol.matches) ouvrir(); });
    mj.addEventListener('mouseleave', function () { if (survol.matches) fermer(); });
    document.addEventListener('click', function (e) { if (!mj.contains(e.target)) fermer(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && mj.classList.contains('ouvert')) { fermer(); bj.focus(); } });
  }

  // Barre de lecture et ombre de l'en-tête
  var barre = document.querySelector('.progression'), entete = document.querySelector('.site-header'), attente = false;
  var fils = Array.prototype.slice.call(document.querySelectorAll('[data-fil]'));
  function defile() {
    attente = false;
    var y = window.scrollY, H = document.documentElement.scrollHeight - window.innerHeight;
    if (barre) barre.style.transform = 'scaleX(' + (H > 0 ? y / H : 0) + ')';
    if (entete) entete.classList.toggle('defile', y > 10);
    fils.forEach(function (f) {
      var r = f.getBoundingClientRect(), p = (window.innerHeight * 0.75 - r.top) / r.height;
      f.style.setProperty('--p', p < 0 ? 0 : p > 1 ? 1 : p);
    });
  }
  window.addEventListener('scroll', function () { if (!attente) { attente = true; requestAnimationFrame(defile); } }, { passive: true });
  defile();

  // Titres découpés en mots (data-mots)
  document.querySelectorAll('[data-mots]').forEach(function (el) {
    var i = 0;
    (function decoupe(n) {
      Array.prototype.slice.call(n.childNodes).forEach(function (c) {
        if (c.nodeType === 3) {
          var f = document.createDocumentFragment();
          c.textContent.split(/(\s+)/).forEach(function (mot) {
            if (!mot) return;
            if (/^\s+$/.test(mot)) { f.appendChild(document.createTextNode(mot)); return; }
            var m = document.createElement('span'); m.className = 'm';
            var s = document.createElement('span'); s.textContent = mot; s.style.setProperty('--i', i++);
            m.appendChild(s); f.appendChild(m);
          });
          n.replaceChild(f, c);
        } else if (c.nodeType === 1) decoupe(c);
      });
    })(el);
  });

  // Apparitions à l'entrée dans l'écran
  var cibles = document.querySelectorAll('[data-rv], [data-mots], [data-rv-clip], [data-rv-etape]');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('vu'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.05 });
    cibles.forEach(function (el) { io.observe(el); });
  } else cibles.forEach(function (el) { el.classList.add('vu'); });

  // Compteurs (data-compte) : de 0 au nombre quand ils arrivent à l'écran
  if (document.documentElement.classList.contains('anim') && 'IntersectionObserver' in window) {
    var ioC = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        ioC.unobserve(e.target);
        var el = e.target, fin = +el.dataset.compte, suf = el.dataset.suffixe || '', t0 = null;
        (function pas(t) {
          if (!t0) t0 = t;
          var p = Math.min(1, (t - t0) / 1600), v = Math.round(fin * (1 - Math.pow(1 - p, 3)));
          el.textContent = v + (p === 1 ? suf : '');
          if (p < 1) requestAnimationFrame(pas);
        })(performance.now());
      });
    }, { threshold: 0.6 });
    document.querySelectorAll('[data-compte]').forEach(function (el) { el.textContent = '0'; ioC.observe(el); });
  }
  // Vidéos YouTube : une vignette, l'iframe n'arrive qu'au clic (pas de traceur avant).
  document.querySelectorAll('.video[data-id]').forEach(function (v) {
    var lien = v.querySelector('.video-lien');
    if (!lien) return;
    lien.addEventListener('click', function (e) {
      e.preventDefault();
      var f = document.createElement('iframe');
      f.src = 'https://www.youtube-nocookie.com/embed/' + v.dataset.id + '?autoplay=1&rel=0';
      f.allow = 'accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture';
      f.allowFullscreen = true;
      f.title = lien.getAttribute('aria-label') || 'Vidéo';
      v.innerHTML = '';
      v.appendChild(f);
    });
  });
  // Formulaires (Web3Forms) : envoi sans quitter la page, objet du mail composé à partir des champs
  // pour qu'on le reconnaisse dans Outlook. Sans JavaScript, Web3Forms renvoie sur la page avec ?envoye=1.
  Array.prototype.forEach.call(document.querySelectorAll('form[data-web3]'), function (form) {
    form.addEventListener('submit', function (e) {
      if (!window.fetch || !window.FormData) return;
      e.preventDefault();
      var bouton = form.querySelector('[type="submit"]'), texteBouton = bouton ? bouton.textContent : '';
      var donnees = {};
      new FormData(form).forEach(function (v, k) { donnees[k] = typeof v === 'string' ? v.trim() : v; });
      if (donnees.botcheck) return;                       // robot : on ne fait rien
      delete donnees.botcheck; delete donnees.redirect;
      var morceaux = (form.getAttribute('data-objet-champs') || '').split(' ').map(function (k) { return donnees[k]; }).filter(Boolean);
      donnees.subject = form.getAttribute('data-web3') + ' ' + (morceaux.join(' | ') || 'Message depuis antoninatger.com');
      if (donnees.nom) donnees.name = donnees.nom;
      var erreur = form.querySelector('.form-erreur');
      if (erreur) erreur.hidden = true;
      if (bouton) { bouton.disabled = true; bouton.textContent = 'Envoi…'; }
      // commentaire : le serveur fournit un lien « Publier » signé, ajouté au mail (si le serveur ne répond pas, le mail part quand même)
      var serveur = form.getAttribute('data-serveur');
      var lien = !serveur ? Promise.resolve(null) : Promise.race([
        fetch(serveur.replace(/\/$/, '') + '/commentaire', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(donnees) })
          .then(function (r) { return r.ok ? r.json() : null; }).then(function (r) { return r && r.lien; }),
        new Promise(function (ok) { setTimeout(function () { ok(null); }, 6000); })
      ]).catch(function () { return null; });
      lien.then(function (l) {
        if (l) donnees.message = donnees.message + '\n\n----------\nPour publier ce commentaire sur le site, un clic : ' + l;
        return fetch(form.action, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(donnees) });
      })
        .then(function (r) { return r.json(); })
        .then(function (r) {
          if (!r.success) throw new Error(r.message || 'refus');
          form.hidden = true;
          var m = form.parentNode.querySelector('[data-message-envoye]');
          if (m) { m.hidden = false; m.focus && m.setAttribute('tabindex', '-1'); m.focus && m.focus(); }
        })
        .catch(function () {
          if (bouton) { bouton.disabled = false; bouton.textContent = texteBouton; }
          if (!erreur) { erreur = document.createElement('p'); erreur.className = 'alerte form-erreur'; erreur.setAttribute('role', 'alert'); form.appendChild(erreur); }
          erreur.textContent = "Le message n'est pas parti (connexion ou service indisponible). Réessayez dans un instant ; votre texte est toujours là.";
          erreur.hidden = false;
        });
    });
  });
  // Formulaires sans JavaScript : Web3Forms renvoie sur la page avec ?envoye=1 (champ « redirect »).
  var q = new URLSearchParams(location.search);
  if (q.get('envoye')) {
    var m = document.querySelector('[data-message-envoye]');
    if (m) { m.hidden = false; m.scrollIntoView({ block: 'center' }); }
  }
  // Abonnement au blog : subscribe.wordpress.com renvoie ici avec ?subscribe=…
  var ab = q.get('subscribe');
  if (ab) {
    var textes = {
      success: 'Merci ! Un e-mail de confirmation vient de vous être envoyé : cliquez sur son lien pour activer l\'abonnement.',
      pending: 'Votre abonnement attend sa confirmation : regardez votre boîte de réception (et les indésirables).',
      already: 'Cette adresse est déjà abonnée.',
      invalid_email: 'Cette adresse e-mail ne semble pas valide.',
      blocked_email: 'Cette adresse ne peut pas être abonnée.',
      flooded_email: 'Trop de tentatives, réessayez dans quelques minutes.'
    };
    var ma = document.querySelector('[data-message-abonnement]');
    if (ma) { ma.textContent = textes[ab] || 'Merci, votre demande a bien été reçue.'; ma.hidden = false; ma.scrollIntoView({ block: 'center' }); }
  }
})();
