// Retours d'intervention : filtres par intervention et par lieu (22 octobre 2026).
// Même principe que les filtres des interventions : dans un groupe, « ou » ; entre groupes, « et ».
// Les choix vont dans l'adresse (?lieu=mediatheque) : un lien filtré se partage tel quel.
(function () {
  document.querySelectorAll('[data-retours-bloc]').forEach(bloc => {
    const form = bloc.querySelector('.filtres--retours');
    if (!form) return;
    form.hidden = false;
    const cartes = Array.from(bloc.querySelectorAll('.avis'));
    const boutons = Array.from(form.querySelectorAll('.filtre'));
    const compte = form.querySelector('[data-retours-compte]');
    const raz = form.querySelector('[data-raz]');
    const GROUPES = ['intervention', 'lieu'];

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
        const ok = GROUPES.every(g => !c[g] || c[g].includes(carte.dataset[g]));
        carte.hidden = !ok;
        if (ok) n++;
      });
      const actif = Object.keys(c).length > 0;
      compte.textContent = actif ? `${n} retour${n > 1 ? 's' : ''} sur ${cartes.length}` : `${cartes.length} retours`;
      raz.hidden = !actif;
      if (majAdresse) {
        const q = new URLSearchParams(location.search);
        GROUPES.forEach(g => { if (c[g]) q.set(g, c[g].join(',')); else q.delete(g); });
        history.replaceState(null, '', location.pathname + (q.toString() ? '?' + q : '') + location.hash);
      }
    }
    boutons.forEach(b => b.addEventListener('click', () => {
      b.setAttribute('aria-pressed', b.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
      appliquer(true);
    }));
    raz.addEventListener('click', () => { boutons.forEach(b => b.setAttribute('aria-pressed', 'false')); appliquer(true); });
    const q = new URLSearchParams(location.search);
    GROUPES.forEach(g => (q.get(g) || '').split(',').filter(Boolean).forEach(v => {
      const b = boutons.find(x => x.dataset.groupe === g && x.dataset.valeur === v);
      if (b) b.setAttribute('aria-pressed', 'true');
    }));
    appliquer(false);
  });
})();
