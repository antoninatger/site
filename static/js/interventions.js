// Page Interventions : filtres par âge, cadre, durée et format (27 septembre 2026).
// Dans un même groupe, les choix s'additionnent (« collège OU lycée ») ; entre groupes,
// ils se cumulent (« collège ET à distance »). Les choix vont dans l'adresse de la page
// (?age=college&mode=distanciel) : un lien filtré se partage tel quel.
(function () {
  const form = document.getElementById('filtres-interventions');
  if (!form) return;
  form.hidden = false;                       // sans JavaScript, la page reste la liste complète
  const cartes = Array.from(document.querySelectorAll('.fiche-card[data-age]'));
  const sections = Array.from(document.querySelectorAll('.groupe-fiches'));
  const boutons = Array.from(form.querySelectorAll('.filtre'));
  const compte = document.getElementById('filtres-compte');
  const raz = document.getElementById('filtres-raz');
  const vide = document.getElementById('filtres-vide');
  const GROUPES = ['age', 'cadre', 'duree', 'mode'];

  function choix() {
    const c = {};
    boutons.forEach(b => {
      if (b.getAttribute('aria-pressed') === 'true') (c[b.dataset.groupe] = c[b.dataset.groupe] || []).push(b.dataset.valeur);
    });
    return c;
  }
  function appliquer(majAdresse) {
    const c = choix();
    let n = 0;
    cartes.forEach(carte => {
      const ok = GROUPES.every(g => !c[g] || c[g].some(v => (carte.dataset[g] || '').split(' ').includes(v)));
      carte.hidden = !ok;
      if (ok) n++;
    });
    sections.forEach(s => { s.hidden = !s.querySelector('.fiche-card:not([hidden])'); });
    const actif = Object.keys(c).length > 0;
    compte.textContent = actif ? `${n} intervention${n > 1 ? 's' : ''} sur ${cartes.length}` : `${cartes.length} interventions`;
    raz.hidden = !actif;
    vide.hidden = n > 0;
    if (majAdresse) {
      const q = new URLSearchParams();
      GROUPES.forEach(g => { if (c[g]) q.set(g, c[g].join(',')); });
      history.replaceState(null, '', location.pathname + (q.toString() ? '?' + q : '') + location.hash);
    }
  }
  function toutAfficher() {
    boutons.forEach(b => b.setAttribute('aria-pressed', 'false'));
    appliquer(true);
  }
  boutons.forEach(b => b.addEventListener('click', () => {
    b.setAttribute('aria-pressed', b.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
    appliquer(true);
  }));
  raz.addEventListener('click', toutAfficher);
  document.querySelectorAll('[data-raz]').forEach(b => b.addEventListener('click', toutAfficher));
  // Filtres repris de l'adresse.
  const q = new URLSearchParams(location.search);
  GROUPES.forEach(g => (q.get(g) || '').split(',').filter(Boolean).forEach(v => {
    const b = boutons.find(x => x.dataset.groupe === g && x.dataset.valeur === v);
    if (b) b.setAttribute('aria-pressed', 'true');
  }));
  appliquer(false);
})();
