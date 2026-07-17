/* =========================================================
   NIZA ISABELA — animations.js
   Animaciones de UI: fade-in on scroll, pulso de carrito,
   sombra de header on scroll. Independiente de main.js.
   ========================================================= */

(function () {

  /* ---- 1. Fade-in on scroll (tarjetas) ---- */
  var revealSelector = '.card, .course-card, .cat-card';
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  function prepararReveal(el) {
    if (el.dataset.revealReady) return;
    el.dataset.revealReady = '1';
    el.classList.add('reveal-on-scroll');
    io.observe(el);
  }

  function escanearTarjetas(root) {
    (root || document).querySelectorAll(revealSelector).forEach(prepararReveal);
  }

  // Escaneo inicial (tarjetas ya presentes al cargar)
  escanearTarjetas();

  // Las tarjetas de catálogo/cursos se inyectan después vía fetch en main.js,
  // así que observamos el DOM para detectarlas apenas aparezcan.
  var mo = new MutationObserver(function (mutations) {
    mutations.forEach(function (m) {
      m.addedNodes.forEach(function (node) {
        if (node.nodeType !== 1) return;
        if (node.matches && node.matches(revealSelector)) prepararReveal(node);
        if (node.querySelectorAll) escanearTarjetas(node);
      });
    });
  });
  mo.observe(document.body, { childList: true, subtree: true });

  /* ---- 2. Sombra en header al hacer scroll ---- */
  var nav = document.querySelector('nav.site-nav');
  if (nav) {
    var onScrollNav = function () {
      if (window.scrollY > 8) nav.classList.add('scrolled');
      else nav.classList.remove('scrolled');
    };
    window.addEventListener('scroll', onScrollNav, { passive: true });
    onScrollNav();
  }

  /* ---- 3. Pulso en el contador del carrito ---- */
  var cartCount = document.querySelector('.cart-icon-count');
  if (cartCount) {
    var ultimoTexto = cartCount.textContent;
    var cartObserver = new MutationObserver(function () {
      if (cartCount.textContent !== ultimoTexto) {
        ultimoTexto = cartCount.textContent;
        cartCount.classList.remove('pulse');
        // Forzar reflow para poder reiniciar la animación
        void cartCount.offsetWidth;
        cartCount.classList.add('pulse');
      }
    });
    cartObserver.observe(cartCount, { characterData: true, childList: true, subtree: true });
  }


  /* ---- 4. Entrada "wow" del hero (solo existe en index.html) ---- */
  var heroItems = document.querySelectorAll('.hero .hero-anim-item');
  if (heroItems.length) {
    heroItems.forEach(function (el, i) {
      el.style.transitionDelay = (i * 0.15) + 's';
    });
    // Doble requestAnimationFrame para asegurar que el navegador
    // registre el estado inicial antes de animar (evita saltos raros)
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        heroItems.forEach(function (el) {
          el.classList.add('hero-in');
        });
      });
    });
  }

  /* ---- 5. Fade reversible al hacer scroll (secciones grandes) ---- */
  var fadeSections = document.querySelectorAll('.fade-scroll-section');
  if (fadeSections.length) {
    var fsObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        entry.target.classList.toggle('fs-hidden', !entry.isIntersecting);
      });
    }, { threshold: 0.1 });
    fadeSections.forEach(function (el) { fsObserver.observe(el); });
  }

})();