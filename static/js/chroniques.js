// antoninatger.com — page Chroniques : filtre par thème et recherche, sans rechargement.
// L'adresse garde le filtre (?theme=complotisme&q=soral) pour pouvoir la partager.
(function () {
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var boutons = $$('.chron-filtre'), cartes = $$('.chron'), annees = $$('[data-chron-annee]');
  var q = $('[data-chron-q]'), compte = $('[data-chron-compte]'), mot = $('[data-chron-mot]'), desc = $('[data-chron-desc]'), vide = $('[data-chron-vide]');
  var sansAccents = function (s) { return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); };
  cartes.forEach(function (c) { c._texte = sansAccents(c.dataset.texte); c._themes = (c.dataset.themes || '').split(' '); });
  var theme = '';

  function appliquer(majAdresse) {
    var cherche = sansAccents(q.value.trim()), n = 0;
    cartes.forEach(function (c) {
      var ok = (!theme || c._themes.indexOf(theme) >= 0) && (!cherche || c._texte.indexOf(cherche) >= 0);
      c.hidden = !ok; if (ok) n++;
    });
    annees.forEach(function (a) { a.hidden = !$$('.chron', a).some(function (c) { return !c.hidden; }); });
    boutons.forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.theme === theme ? 'true' : 'false'); });
    compte.textContent = n;
    mot.textContent = n > 1 ? 'chroniques' : 'chronique';
    var b = boutons.filter(function (x) { return x.dataset.theme === theme; })[0];
    desc.textContent = theme && b ? ' · ' + (b.title || '') : '';
    vide.hidden = n > 0;
    if (majAdresse && window.history && history.replaceState) {
      var p = new URLSearchParams();
      if (theme) p.set('theme', theme);
      if (q.value.trim()) p.set('q', q.value.trim());
      history.replaceState(null, '', location.pathname + (p.toString() ? '?' + p : ''));
    }
  }

  boutons.forEach(function (b) {
    b.addEventListener('click', function () {
      theme = (theme === b.dataset.theme) ? '' : b.dataset.theme;
      appliquer(true);
    });
  });
  // les étiquettes des cartes filtrent sur place au lieu de recharger la page
  $$('[data-theme-lien]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault(); theme = a.dataset.themeLien; appliquer(true);
      $('[data-chron-outils]').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
  var attente;
  q.addEventListener('input', function () { clearTimeout(attente); attente = setTimeout(function () { appliquer(true); }, 120); });
  var raz = $('[data-chron-raz]');
  if (raz) raz.addEventListener('click', function () { theme = ''; q.value = ''; appliquer(true); });

  var p = new URLSearchParams(location.search);
  theme = p.get('theme') || '';
  if (!boutons.some(function (b) { return b.dataset.theme === theme; })) theme = '';
  q.value = p.get('q') || '';
  appliquer(false);
})();
