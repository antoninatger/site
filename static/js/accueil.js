// antoninatger.com — effets propres à la page d'accueil.
// Les apparitions communes (data-rv, titres mot par mot, compteurs) sont dans site.js.
(function () {
  var anim = document.documentElement.classList.contains('anim');
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var borne = function (v) { return v < 0 ? 0 : v > 1 ? 1 : v; };

  // Bandes qui défilent : on double le contenu pour une boucle sans couture
  var bande = $('[data-boucle]');
  if (bande) bande.innerHTML += bande.innerHTML.replace(/<a /g, '<a aria-hidden="true" tabindex="-1" ');
  var pr = $('[data-retours]');
  if (pr && pr.children.length) {
    while (pr.children.length < 6) pr.innerHTML += pr.innerHTML;
    pr.innerHTML += pr.innerHTML.replace(/<figure /g, '<figure aria-hidden="true" ');
    pr.style.setProperty('--duree', Math.max(30, pr.children.length * 6) + 's');
  }

  // Le texte qui s'allume : chaque mot devient une unité ; <em> = passage en rouge
  var allume = $('[data-allume]'), motsManif = [];
  if (allume && anim) {
    (function decoupe(n, fort) {
      Array.prototype.slice.call(n.childNodes).forEach(function (c) {
        if (c.nodeType === 3) {
          var f = document.createDocumentFragment();
          c.textContent.split(/(\s+)/).forEach(function (mot) {
            if (!mot) return;
            if (/^\s+$/.test(mot)) { f.appendChild(document.createTextNode(mot)); return; }
            var s = document.createElement('span'); s.className = 'w' + (fort ? ' fort' : ''); s.textContent = mot;
            motsManif.push(s); f.appendChild(s);
          });
          n.replaceChild(f, c);
        } else if (c.nodeType === 1) {
          decoupe(c, fort || c.tagName === 'EM');
        }
      });
    })(allume, false);
  }

  // Une séance en trois temps : l'étape au milieu de l'écran choisit la photo
  var etapes = $$('[data-etape]'), photos = $$('.recit__visuel img'), num = $('[data-recit-num]');
  if (etapes.length && 'IntersectionObserver' in window) {
    var ioE = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        var k = +e.target.dataset.etape;
        etapes.forEach(function (x, j) { x.classList.toggle('actif', j === k); });
        photos.forEach(function (x, j) { x.classList.toggle('actif', j === k); });
        if (num) num.textContent = k + 1;
      });
    }, { rootMargin: '-45% 0px -45% 0px' });
    etapes.forEach(function (e) { ioE.observe(e); });
  }

  // « D'où je parle » : une seule colonne ouverte ; survol sur ordinateur, toucher sur téléphone.
  // En quittant la grille à la souris, on revient à la colonne ouverte au départ.
  var grille = $('[data-facettes]');
  if (grille) {
    var faces = $$('.facette', grille), defaut = Math.max(0, faces.findIndex(function (f) { return f.classList.contains('ouverte'); }));
    var survol = window.matchMedia('(hover: hover) and (min-width: 961px)');
    var ouvrir = function (k) {
      faces.forEach(function (f, j) { f.classList.toggle('ouverte', j === k); f.setAttribute('aria-expanded', j === k ? 'true' : 'false'); });
      grille.style.setProperty('--cols', faces.map(function (f, j) { return j === k ? '2.2fr' : '1fr'; }).join(' '));
      window.dispatchEvent(new Event('scroll'));
    };
    faces.forEach(function (f, k) {
      f.addEventListener('mouseenter', function () { if (survol.matches) ouvrir(k); });
      f.addEventListener('focusin', function () { ouvrir(k); });
      f.addEventListener('click', function (e) { if (!f.classList.contains('ouverte')) { e.preventDefault(); ouvrir(k); } });
      f.addEventListener('keydown', function (e) { if ((e.key === 'Enter' || e.key === ' ') && e.target === f) { e.preventDefault(); ouvrir(k); } });
    });
    grille.addEventListener('mouseleave', function () { if (survol.matches) ouvrir(defaut); });
    ouvrir(defaut);
  }

  if (!anim) return;

  // Ce qui suit la position de la page
  var photoOuv = $('[data-parallax]'), manif = $('[data-manifeste]');
  var frise = $('[data-frise]'), trait = $('.frise__trait'), cartes = $$('.temoin'), attente = false;
  var lignes = $$('[data-ligne]');
  // Galerie : la section est aussi haute que le chemin à parcourir par la piste
  var defile = $('[data-defile]'), piste = $('[data-piste]'), course = 0;
  function mesure() {
    if (!defile || !piste) return;
    course = Math.max(0, piste.scrollWidth - window.innerWidth);
    defile.style.height = (window.innerHeight + course * 0.6) + 'px';   // la piste va plus vite que la page
  }
  mesure(); window.addEventListener('load', mesure);
  function rendu() {
    attente = false;
    var y = window.scrollY, h = window.innerHeight;
    if (photoOuv) {
      var p0 = borne(y / h);
      photoOuv.style.transform = 'translateY(' + (p0 * 40) + 'px) scale(' + (1.12 - p0 * 0.12) + ')';
    }
    if (manif && motsManif.length) {
      var r = manif.getBoundingClientRect(), pm = borne((-r.top + h * 0.15) / (r.height - h * 1.1));
      var n = Math.round(pm * motsManif.length);
      motsManif.forEach(function (w, i) { w.classList.toggle('on', i < n); });
    }
    if (frise && trait) {
      var rf = frise.getBoundingClientRect();
      trait.style.setProperty('--p', borne((h * 0.7 - rf.top) / rf.height));
    }
    // colonnes « D'où je parle » : chaque ligne se dessine, les points s'allument au passage
    lignes.forEach(function (l) {
      var rl = l.getBoundingClientRect(), pl = borne((h * 0.78 - rl.top) / rl.height);
      l.style.setProperty('--p', pl);
      $$('li', l).forEach(function (li) { li.classList.toggle('on', li.offsetTop + 10 <= pl * rl.height); });
    });
    if (defile && piste) {
      var rd = defile.getBoundingClientRect(), pd = borne(-rd.top / Math.max(1, rd.height - h));
      piste.style.transform = 'translateX(' + (-pd * course) + 'px)';
    }
    cartes.forEach(function (c, i) {
      var suivante = cartes[i + 1]; if (!suivante) return;
      var d = suivante.getBoundingClientRect().top - c.getBoundingClientRect().top;
      var pc = borne(1 - d / c.offsetHeight);
      c.style.transform = 'scale(' + (1 - pc * 0.05) + ')';
      c.style.opacity = 1 - pc * 0.35;
    });
  }
  function demande() { if (!attente) { attente = true; requestAnimationFrame(rendu); } }
  window.addEventListener('scroll', demande, { passive: true });
  window.addEventListener('resize', function () { mesure(); demande(); });
  rendu();
})();
