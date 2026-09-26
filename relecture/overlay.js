// Relecture du site — barre d'outils injectée par serveur_relecture.py. N'existe pas sur le site en ligne.
(function () {
  'use strict';
  var API = '/__relecture/api/commentaires';
  var PAGE = location.pathname;
  var TITRE = PAGE === '/' ? 'Accueil' : (document.title || '').split(/\s[—·|]\s/)[0].trim();
  var CATEGORIES = ['Texte', 'Mise en page', 'Couleur / police', 'Supprimer', 'Déplacer', 'Ajouter', 'Autre'];
  var commentaires = [];
  var modeCommentaire = false;
  var cible = null;          // élément survolé / choisi
  var courant = null;        // commentaire en cours d'édition (objet) ou null

  // ------------------------------------------------------------ utilitaires
  function h(tag, attrs, enfants) {
    var el = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === 'text') el.textContent = attrs[k];
      else if (k === 'html') el.innerHTML = attrs[k];
      else if (k.slice(0, 2) === 'on') el.addEventListener(k.slice(2), attrs[k]);
      else el.setAttribute(k, attrs[k]);
    });
    (enfants || []).forEach(function (e) { if (e) el.appendChild(typeof e === 'string' ? document.createTextNode(e) : e); });
    return el;
  }
  function dansUI(el) { return !!(el && el.closest && el.closest('.rl-ui')); }
  function selecteurDe(el) {
    var parts = [];
    while (el && el.nodeType === 1 && el !== document.body) {
      var s = el.tagName.toLowerCase();
      if (el.id) { parts.unshift(s + '#' + CSS.escape(el.id)); break; }
      var p = el.parentElement;
      if (p) {
        var freres = Array.prototype.filter.call(p.children, function (c) { return c.tagName === el.tagName; });
        if (freres.length > 1) s += ':nth-of-type(' + (freres.indexOf(el) + 1) + ')';
      }
      parts.unshift(s);
      el = p;
    }
    return parts.join(' > ');
  }
  function baliseDe(el) {
    var s = el.tagName.toLowerCase();
    var cl = (el.getAttribute('class') || '').trim().split(/\s+/).filter(function (c) { return c && !/^(is-|rl-)/.test(c); })[0];
    return cl ? s + '.' + cl : s;
  }
  function blocDe(el) {
    var b = el.parentElement && el.parentElement.closest('header, footer, section, article, aside, nav, main, form, figure, .card, .encart');
    return b ? baliseDe(b) : '';
  }
  function texteDe(el) {
    if (el.tagName === 'IMG') return (el.getAttribute('alt') || '') + ' [' + (el.getAttribute('src') || '').split('/').pop() + ']';
    var t = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
    return t.slice(0, 300);
  }
  function trouver(sel) { try { return sel ? document.querySelector(sel) : null; } catch (e) { return null; } }
  function requete(methode, url, corps) {
    return fetch(url, { method: methode, headers: { 'Content-Type': 'application/json' }, body: corps ? JSON.stringify(corps) : undefined })
      .then(function (r) { return r.json().then(function (j) { if (!r.ok) throw new Error(j.erreur || r.status); return j; }); });
  }

  // ------------------------------------------------------------ interface
  var couche = h('div', { 'class': 'rl-ui rl-couche' });
  var cadre = h('div', { 'class': 'rl-ui rl-cadre', hidden: '' });
  var etiquette = h('div', { 'class': 'rl-ui rl-etiquette', hidden: '' });
  var toast = h('div', { 'class': 'rl-ui rl-toast', hidden: '' });
  var boutonMode = h('button', { 'class': 'rl-bouton rl-bouton--principal', type: 'button', onclick: function () { basculerMode(); } }, ['Commenter']);
  var boutonPage = h('button', { 'class': 'rl-bouton', type: 'button', title: 'Une remarque qui ne porte pas sur un élément précis', onclick: function () { ouvrirPanneau(null, null); } }, ['Remarque sur la page']);
  var lienTableau = h('a', { 'class': 'rl-bouton rl-bouton--lien', href: '/__relecture/', title: 'Toutes les remarques, toutes pages confondues' }, ['0 remarque']);
  var barre = h('div', { 'class': 'rl-ui rl-barre' }, [
    h('span', { 'class': 'rl-barre__titre', text: 'Relecture' }), boutonMode, boutonPage, lienTableau,
    h('span', { 'class': 'rl-barre__aide', text: 'Écran ' + window.innerWidth + ' px' })
  ]);
  var panneau = h('div', { 'class': 'rl-ui rl-panneau', hidden: '' });

  document.body.appendChild(couche);
  document.body.appendChild(cadre);
  document.body.appendChild(etiquette);
  document.body.appendChild(toast);
  document.body.appendChild(barre);
  document.body.appendChild(panneau);
  window.addEventListener('resize', function () { barre.querySelector('.rl-barre__aide').textContent = 'Écran ' + window.innerWidth + ' px'; placerEpingles(); });

  function afficherToast(txt) {
    toast.textContent = txt; toast.hidden = false;
    clearTimeout(toast._t); toast._t = setTimeout(function () { toast.hidden = true; }, 2200);
  }

  // ------------------------------------------------------------ mode commentaire
  function basculerMode(force) {
    modeCommentaire = typeof force === 'boolean' ? force : !modeCommentaire;
    document.documentElement.classList.toggle('rl-mode', modeCommentaire);
    boutonMode.textContent = modeCommentaire ? 'Cliquez un élément · Échap pour finir' : 'Commenter';
    boutonMode.classList.toggle('rl-bouton--actif', modeCommentaire);
    if (!modeCommentaire) { cadre.hidden = true; etiquette.hidden = true; cible = null; }
  }
  function encadrer(el, fixe) {
    if (!el) { cadre.hidden = true; etiquette.hidden = true; return; }
    var r = el.getBoundingClientRect();
    cadre.hidden = false;
    cadre.style.top = (r.top + window.scrollY - 3) + 'px'; cadre.style.left = (r.left + window.scrollX - 3) + 'px';
    cadre.style.width = (r.width + 6) + 'px'; cadre.style.height = (r.height + 6) + 'px';
    cadre.classList.toggle('rl-cadre--fixe', !!fixe);
    etiquette.hidden = false; etiquette.textContent = baliseDe(el);
    etiquette.style.top = Math.max(0, r.top + window.scrollY - 24) + 'px'; etiquette.style.left = (r.left + window.scrollX - 3) + 'px';
  }
  document.addEventListener('mousemove', function (e) {
    if (!modeCommentaire || !panneau.hidden) return;
    var el = e.target;
    if (dansUI(el) || el === document.body || el === document.documentElement) { encadrer(null); return; }
    cible = el; encadrer(el);
  }, true);
  document.addEventListener('click', function (e) {
    if (!modeCommentaire) return;
    if (dansUI(e.target)) return;
    e.preventDefault(); e.stopPropagation();
    if (!panneau.hidden) return;
    var el = e.target;
    if (el === document.body || el === document.documentElement) return;
    cible = el; encadrer(el, true);
    ouvrirPanneau(el, null);
  }, true);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      if (!panneau.hidden) fermerPanneau();
      else if (modeCommentaire) basculerMode(false);
    }
  });

  // ------------------------------------------------------------ panneau
  function ouvrirPanneau(el, commentaire) {
    courant = commentaire;
    var estEdition = !!commentaire;
    var cat = commentaire ? commentaire.categorie : 'Texte';
    var texteEl = el ? texteDe(el) : (commentaire && commentaire.texte_element) || '';
    var entete = el ? baliseDe(el) + (blocDe(el) ? ' dans ' + blocDe(el) : '') : (commentaire && commentaire.selecteur ? commentaire.balise + (commentaire.bloc ? ' dans ' + commentaire.bloc : '') : 'Remarque sur la page ' + PAGE);
    panneau.innerHTML = '';
    var zone = h('textarea', { 'class': 'rl-zone', placeholder: 'Ce qui vous gêne, ce que vous voudriez à la place…', rows: '5' });
    if (commentaire) zone.value = commentaire.commentaire;
    var chips = h('div', { 'class': 'rl-chips' }, CATEGORIES.map(function (c) {
      return h('button', { type: 'button', 'class': 'rl-chip' + (c === cat ? ' rl-chip--actif' : ''), text: c, onclick: function (e) {
        cat = c; Array.prototype.forEach.call(chips.children, function (b) { b.classList.toggle('rl-chip--actif', b.textContent === c); });
      } });
    }));
    var boutons = h('div', { 'class': 'rl-actions' }, [
      h('button', { type: 'button', 'class': 'rl-bouton rl-bouton--principal', onclick: function () {
        var txt = zone.value.trim();
        if (!txt) { zone.focus(); return; }
        if (estEdition) {
          requete('PUT', API + '/' + commentaire.id, { commentaire: txt, categorie: cat }).then(function (c) {
            remplacer(c); fermerPanneau(); afficherToast('Remarque #' + c.id + ' modifiée');
          }).catch(function (e) { afficherToast('Erreur : ' + e.message); });
        } else {
          var corps = { page: PAGE, titre_page: TITRE, categorie: cat, commentaire: txt, ecran: window.innerWidth };
          if (el) { corps.selecteur = selecteurDe(el); corps.balise = baliseDe(el); corps.bloc = blocDe(el); corps.texte_element = texteEl; }
          requete('POST', API, corps).then(function (c) {
            commentaires.push(c); placerEpingles(); fermerPanneau(); afficherToast('Remarque #' + c.id + ' enregistrée');
          }).catch(function (e) { afficherToast('Erreur : ' + e.message); });
        }
      } }, [estEdition ? 'Enregistrer' : 'Enregistrer la remarque']),
      h('button', { type: 'button', 'class': 'rl-bouton', onclick: fermerPanneau }, ['Annuler'])
    ]);
    if (estEdition) {
      var fait = commentaire.statut === 'fait';
      boutons.appendChild(h('button', { type: 'button', 'class': 'rl-bouton', onclick: function () {
        requete('PUT', API + '/' + commentaire.id, { statut: fait ? 'ouvert' : 'fait' }).then(function (c) { remplacer(c); fermerPanneau(); afficherToast(fait ? 'Remarque rouverte' : 'Marquée comme faite'); });
      } }, [fait ? 'Rouvrir' : 'Marquer faite']));
      boutons.appendChild(h('button', { type: 'button', 'class': 'rl-bouton rl-bouton--danger', onclick: function () {
        requete('DELETE', API + '/' + commentaire.id).then(function () {
          commentaires = commentaires.filter(function (c) { return c.id !== commentaire.id; }); placerEpingles(); fermerPanneau(); afficherToast('Remarque supprimée');
        });
      } }, ['Supprimer']));
    }
    panneau.appendChild(h('div', { 'class': 'rl-panneau__tete' }, [
      h('b', { text: estEdition ? 'Remarque #' + commentaire.id : 'Nouvelle remarque' }),
      h('button', { type: 'button', 'class': 'rl-fermer', title: 'Fermer (Échap)', onclick: fermerPanneau }, ['×'])
    ]));
    panneau.appendChild(h('div', { 'class': 'rl-panneau__ou', text: entete }));
    if (texteEl) panneau.appendChild(h('div', { 'class': 'rl-panneau__extrait', text: '« ' + texteEl.slice(0, 140) + (texteEl.length > 140 ? '…' : '') + ' »' }));
    panneau.appendChild(chips);
    panneau.appendChild(zone);
    panneau.appendChild(boutons);
    if (estEdition && commentaire.reponse) panneau.appendChild(h('div', { 'class': 'rl-panneau__reponse', text: 'Réponse : ' + commentaire.reponse }));
    panneau.style.bottom = (barre.offsetHeight + 28) + 'px';
    panneau.hidden = false;
    zone.focus();
  }
  function fermerPanneau() { panneau.hidden = true; courant = null; if (modeCommentaire) { cadre.hidden = true; etiquette.hidden = true; } }
  function remplacer(c) { commentaires = commentaires.map(function (x) { return x.id === c.id ? c : x; }); placerEpingles(); }

  // ------------------------------------------------------------ épingles
  function placerEpingles() {
    couche.innerHTML = '';
    var ici = commentaires.filter(function (c) { return c.page === PAGE; });
    var perdus = 0;
    ici.forEach(function (c) {
      if (!c.selecteur) return;
      var el = trouver(c.selecteur);
      if (!el) { perdus++; return; }
      var r = el.getBoundingClientRect();
      var pin = h('button', { type: 'button', 'class': 'rl-pin' + (c.statut === 'fait' ? ' rl-pin--fait' : ''), title: '#' + c.id + ' · ' + c.categorie + ' — ' + c.commentaire.slice(0, 120), text: String(c.id), onclick: function (e) {
        e.preventDefault(); e.stopPropagation(); encadrer(el, true); ouvrirPanneau(null, c);
      } });
      pin.style.top = (r.top + window.scrollY - 10) + 'px'; pin.style.left = (r.left + window.scrollX - 10) + 'px';
      couche.appendChild(pin);
    });
    var generales = ici.filter(function (c) { return !c.selecteur; });
    var n = commentaires.filter(function (c) { return c.statut !== 'fait'; }).length;
    lienTableau.textContent = n + ' remarque' + (n > 1 ? 's' : '') + ' à traiter' + (ici.length ? ' · ' + ici.length + ' sur cette page' : '');
    var bande = barre.querySelector('.rl-barre__generales');
    if (bande) bande.remove();
    if (generales.length || perdus) {
      bande = h('div', { 'class': 'rl-barre__generales' });
      generales.forEach(function (c) {
        bande.appendChild(h('button', { type: 'button', 'class': 'rl-pin rl-pin--inline' + (c.statut === 'fait' ? ' rl-pin--fait' : ''), text: '#' + c.id + ' page', title: c.commentaire, onclick: function () { ouvrirPanneau(null, c); } }));
      });
      if (perdus) bande.appendChild(h('span', { 'class': 'rl-barre__aide', text: perdus + ' remarque(s) dont l’élément a disparu (voir le tableau)' }));
      barre.appendChild(bande);
    }
  }
  if (window.ResizeObserver) new ResizeObserver(function () { placerEpingles(); }).observe(document.body);
  window.addEventListener('load', placerEpingles);

  // ------------------------------------------------------------ démarrage
  requete('GET', API).then(function (j) {
    commentaires = j.commentaires || [];
    placerEpingles();
    var m = location.hash.match(/rl=(\d+)/);
    if (m) {
      var c = commentaires.filter(function (x) { return x.id === +m[1]; })[0];
      if (c) {
        var el = trouver(c.selecteur);
        if (el) { el.scrollIntoView({ block: 'center' }); encadrer(el, true); }
        ouvrirPanneau(null, c);
      }
    }
  }).catch(function () { afficherToast('Le serveur de relecture ne répond pas'); });
})();
