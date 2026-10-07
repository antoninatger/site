// Galerie « En intervention » : agrandit une photo au clic, avec précédente / suivante.
// Sans JavaScript, le lien ouvre simplement la grande image.
(function () {
  var g = document.querySelector('[data-galerie]');
  if (!g || typeof HTMLDialogElement === 'undefined') return;
  var liens = Array.prototype.slice.call(g.querySelectorAll('a'));
  if (!liens.length) return;
  var d = document.createElement('dialog');
  d.className = 'visionneuse';
  d.setAttribute('aria-label', 'Photo agrandie');
  d.innerHTML = '<figure><img alt=""><figcaption></figcaption></figure>' +
    '<button type="button" class="visionneuse__fermer" aria-label="Fermer">×</button>' +
    '<button type="button" class="visionneuse__prec" aria-label="Photo précédente">‹</button>' +
    '<button type="button" class="visionneuse__suiv" aria-label="Photo suivante">›</button>';
  document.body.appendChild(d);
  var img = d.querySelector('img'), legende = d.querySelector('figcaption'), i = 0, retour = null;
  function montrer(n) {
    i = (n + liens.length) % liens.length;
    var a = liens[i], fig = a.closest('figure');
    img.src = a.getAttribute('href');
    img.alt = a.querySelector('img').alt;
    legende.textContent = fig && fig.querySelector('figcaption') ? fig.querySelector('figcaption').textContent : '';
  }
  liens.forEach(function (a, n) {
    a.addEventListener('click', function (e) {
      e.preventDefault(); retour = a; montrer(n); d.showModal();
    });
  });
  d.querySelector('.visionneuse__fermer').addEventListener('click', function () { d.close(); });
  d.querySelector('.visionneuse__prec').addEventListener('click', function () { montrer(i - 1); });
  d.querySelector('.visionneuse__suiv').addEventListener('click', function () { montrer(i + 1); });
  d.addEventListener('click', function (e) { if (e.target === d) d.close(); });
  d.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowLeft') { e.preventDefault(); montrer(i - 1); }
    if (e.key === 'ArrowRight') { e.preventDefault(); montrer(i + 1); }
  });
  d.addEventListener('close', function () { img.removeAttribute('src'); if (retour) retour.focus(); });
})();
