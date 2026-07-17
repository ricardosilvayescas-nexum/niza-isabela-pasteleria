/* =========================================================
   NIZA ISABELA — main.js
   Interactividad compartida entre todas las páginas
   ========================================================= */

/* ---------- Conexión con el backend ----------
   Cambia esta URL cuando despliegues el backend en Azure
   (ej. https://niza-isabela-api.azurewebsites.net) */
const API_BASE_URL = 'https://niza-isabela-api-c9d8a3ghbddqe3hr.centralus-01.azurewebsites.net';
/* ---------- Carrito de compras (localStorage) ---------- */
const CART_KEY = 'niza_carrito';

function getCart() {
  try { return JSON.parse(localStorage.getItem(CART_KEY)) || []; } catch { return []; }
}

function saveCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  actualizarContadorCarrito();
}

function addToCart(item) {
  const cart = getCart();
  if (item.tipo === 'curso') {
    const yaEsta = cart.find(i => i.tipo === 'curso' && i.curso_id === item.curso_id);
    if (yaEsta) {
      mostrarToastCarrito(`${item.nombre} ya está en tu carrito`);
      return;
    }
    cart.push(item);
  } else {
    const existente = cart.find(i => i.tipo !== 'curso' && i.producto_id === item.producto_id && i.opcion_id === item.opcion_id);
    if (existente) {
      existente.cantidad += item.cantidad;
    } else {
      cart.push(item);
    }
  }
  saveCart(cart);
}

function removeFromCart(index) {
  const cart = getCart();
  cart.splice(index, 1);
  saveCart(cart);
}

function updateCartQty(index, cantidad) {
  const cart = getCart();
  if (cantidad <= 0) { cart.splice(index, 1); } else { cart[index].cantidad = cantidad; }
  saveCart(cart);
}

function getCartCount() {
  return getCart().reduce((sum, i) => sum + i.cantidad, 0);
}

function getCartTotal() {
  return getCart().reduce((sum, i) => sum + i.cantidad * i.precio_unitario, 0);
}

function actualizarContadorCarrito() {
  document.querySelectorAll('.cart-icon-count').forEach(function (el) {
    const count = getCartCount();
    el.textContent = count;
    el.style.display = count > 0 ? 'inline-flex' : 'none';
  });
}

function mostrarToastCarrito(nombre) {
  const toast = document.createElement('div');
  toast.textContent = `✓ ${nombre} agregado al carrito`;
  toast.style.cssText = 'position:fixed; bottom:24px; left:50%; transform:translateX(-50%); background:var(--ink); color:#fff; padding:14px 24px; border-radius:6px; font-size:13px; z-index:999; box-shadow:0 4px 16px rgba(0,0,0,.2);';
  document.body.appendChild(toast);
  setTimeout(function () { toast.remove(); }, 2500);
}

function cartItemRowHTML(item, index) {
  const esCurso = item.tipo === 'curso';
  return `
    <div class="sum-item" style="align-items:flex-start;">
      <div>
        <div style="font-weight:500; margin-bottom:4px;">${item.nombre}</div>
        ${esCurso ? '<span class="cart-item-size">📄 Curso digital</span>' : ''}
        ${item.opcion_nombre ? `<span class="cart-item-size">${item.opcion_nombre}</span>` : ''}
        ${esCurso ? '' : `
        <div class="cart-item-qty-row">
          <button type="button" class="cart-qty-btn" onclick="cambiarCantidadCarrito(${index}, -1)">−</button>
          <span class="cart-qty-value">${item.cantidad}</span>
          <button type="button" class="cart-qty-btn" onclick="cambiarCantidadCarrito(${index}, 1)">+</button>
        </div>`}
      </div>
      <div style="text-align:right;">
        <div style="font-weight:600;">$${(item.precio_unitario * item.cantidad).toFixed(0)} MXN</div>
        <button type="button" class="cart-remove-btn" onclick="quitarDelCarrito(${index})">Quitar</button>
      </div>
    </div>`;
}

function renderCheckoutCart() {
  const cont = document.getElementById('checkout-cart-items');
  if (!cont) return;
  const cart = getCart();
  if (!cart.length) {
    cont.innerHTML = '<p style="color:var(--grey); font-size:13px; text-align:center; padding:20px 0;">Tu carrito está vacío. <a href="catalogo.html">Ver catálogo →</a></p>';
  } else {
    cont.innerHTML = cart.map(cartItemRowHTML).join('');
  }
  const totalEl = document.getElementById('checkout-total');
  if (totalEl) totalEl.textContent = `$${getCartTotal().toFixed(0)} MXN`;
  actualizarPanelesCheckout(cart);
}

function actualizarPanelesCheckout(cart) {
  const panelFisico = document.getElementById('panel-entrega-fisica');
  const panelDigital = document.getElementById('panel-cursos-digital');
  if (!panelFisico || !panelDigital) return;

  const productos = cart.filter(function (item) { return item.tipo !== 'curso'; });
  const cursos = cart.filter(function (item) { return item.tipo === 'curso'; });

  panelFisico.style.display = productos.length ? 'block' : 'none';
  panelDigital.style.display = cursos.length ? 'block' : 'none';

  const nota = document.getElementById('cursos-digital-nota');
  if (nota && cursos.length) {
    const nombres = cursos.map(function (c) { return `"${c.nombre}"`; }).join(', ');
    nota.textContent = `📄 ${nombres} no requiere${cursos.length > 1 ? 'n' : ''} sucursal ni fecha — el acceso se activa automáticamente al confirmar el pago, en "Mis cursos" y por correo.`;
  }
}

function cambiarCantidadCarrito(index, delta) {
  const cart = getCart();
  updateCartQty(index, cart[index].cantidad + delta);
  renderCheckoutCart();
}

function quitarDelCarrito(index) {
  removeFromCart(index);
  renderCheckoutCart();
}

async function fetchProductos(tipo) {
  const url = tipo ? `${API_BASE_URL}/api/productos/?tipo=${tipo}` : `${API_BASE_URL}/api/productos/`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('No se pudieron cargar los productos');
  return res.json();
}

async function fetchCursos() {
  const res = await fetch(`${API_BASE_URL}/api/cursos/`);
  if (!res.ok) throw new Error('No se pudieron cargar los cursos');
  return res.json();
}

async function fetchSucursales() {
  const res = await fetch(`${API_BASE_URL}/api/sucursales/`);
  if (!res.ok) throw new Error('No se pudieron cargar las sucursales');
  return res.json();
}

function sucursalPanelHTML(s) {
  return `
    <div class="panel">
      <h3>${s.nombre}</h3>
      <p style="color:var(--grey); font-size:13.5px;">${s.direccion}<br>${s.horario || ''}</p>
    </div>`;
}

async function initSucursalesPaneles(containerId) {
  const cont = document.getElementById(containerId);
  if (!cont) return;
  try {
    const sucursales = await fetchSucursales();
    cont.innerHTML = sucursales.map(sucursalPanelHTML).join('');
  } catch {
    cont.innerHTML = '<p style="color:var(--grey);">No se pudieron cargar las sucursales.</p>';
  }
}

function sucursalOptionHTML(s) {
  return `<option value="${s.id}">${s.nombre}</option>`;
}

async function initSucursalSelect(selectId) {
  const select = document.getElementById(selectId);
  if (!select) return;
  try {
    const sucursales = await fetchSucursales();
    select.innerHTML = sucursales.map(sucursalOptionHTML).join('');
  } catch {
    select.innerHTML = '<option>No se pudieron cargar</option>';
  }
}

function sucursalRowHTML(s, index) {
  return `<div class="sucursal-row ${index === 0 ? 'sel' : ''}" data-id="${s.id}"><span>${s.nombre} — ${s.direccion}</span><span>${index === 0 ? '✓' : ''}</span></div>`;
}

function wireSucursalRows(container) {
  container.querySelectorAll('.sucursal-row').forEach(function (row) {
    row.addEventListener('click', function () {
      container.querySelectorAll('.sucursal-row').forEach(function (r) {
        r.classList.remove('sel');
        r.querySelector('span:last-child').textContent = '';
      });
      row.classList.add('sel');
      row.querySelector('span:last-child').textContent = '✓';
    });
  });
}

async function initSucursalRows(containerId) {
  const cont = document.getElementById(containerId);
  if (!cont) return;
  try {
    const sucursales = await fetchSucursales();
    cont.innerHTML = sucursales.map(sucursalRowHTML).join('');
    wireSucursalRows(cont);
  } catch {
    cont.innerHTML = '<p style="color:var(--grey);">No se pudieron cargar las sucursales.</p>';
  }
}

function sucursalFooterLinkHTML(s) {
  return `<a href="nosotros.html">${s.nombre}</a>`;
}

async function initSucursalesFooter(containerId) {
  const cont = document.getElementById(containerId);
  if (!cont) return;
  try {
    const sucursales = await fetchSucursales();
    cont.innerHTML = sucursales.map(sucursalFooterLinkHTML).join('');
  } catch {
    cont.innerHTML = '<a href="nosotros.html">Ver sucursales</a>';
  }
}

function productCardHTML(p) {
  const esFijo = p.tipo === 'fijo';
  const precio = esFijo ? `$${Number(p.precio_base).toFixed(0)} MXN` : `Desde $${Number(p.precio_base).toFixed(0)} MXN`;
  const tamanos = (p.opciones || []).filter(o => o.tipo_opcion === 'tamaño');
  const linkAttrs = esFijo
    ? `href="#" data-quickview data-id="${p.id}" data-price-num="${p.precio_base}" data-title="${p.nombre}" data-price="${precio}" data-desc="${p.descripcion || ''}" data-photo="${p.foto_url || ''}" data-opciones="${encodeURIComponent(JSON.stringify(tamanos))}"`
    : `href="cotizacion.html?producto=${p.id}"`;
  const linkText = esFijo ? 'Ver más →' : 'Cotizar →';
  const photoClass = esFijo ? 'card-photo' : 'card-photo alt';
  const badge = esFijo ? '' : '<span class="badge">Personalizable</span>';
  return `
    <div class="card" data-category="${esFijo ? 'fijo' : 'personalizado'}">
      <div class="${photoClass}" style="${p.foto_url ? `background-image:url('${p.foto_url}'); background-size:cover; background-position:center;` : ''}">${p.foto_url ? '' : badge + 'FOTO — ' + p.nombre}</div>
      <h4>${p.nombre}</h4>
      <div class="price">${precio}</div>
      <a class="link" ${linkAttrs}>${linkText}</a>
    </div>`;
}

function courseCardHTML(c) {
  const precioHTML = c.tiene_descuento
    ? `<span class="price-old">$${Number(c.precio_original).toFixed(0)} MXN</span><span class="price-new">$${Number(c.precio_final).toFixed(0)} MXN</span>`
    : `$${Number(c.precio_final).toFixed(0)} MXN`;
  const badge = c.tiene_descuento ? '<span class="discount-badge">Oferta</span>' : '';
  return `
    <div class="card">
      <div class="card-photo" style="position:relative; ${c.portada_url ? `background-image:url('${c.portada_url}'); background-size:cover; background-position:center;` : ''}">${badge}${c.portada_url ? '' : 'Portada — ' + c.nombre}</div>
      <h4>${c.nombre}</h4>
      <div class="price">${precioHTML} · PDF</div>
      <a class="link" href="#" data-courseview
         data-title="${c.nombre}"
         data-price="${c.tiene_descuento ? '$' + Number(c.precio_final).toFixed(0) + ' MXN (antes $' + Number(c.precio_original).toFixed(0) + ')' : '$' + Number(c.precio_final).toFixed(0) + ' MXN'}"
         data-price-num="${c.precio_final}"
         data-desc="${c.descripcion || ''}"
         data-photo="${c.portada_url || ''}"
         data-id="${c.id}">Ver más →</a>
    </div>`;
}

/* ---------- Autenticación ---------- */
function getToken() {
  return localStorage.getItem('niza_token');
}

function saveSession(token, usuario) {
  localStorage.setItem('niza_token', token);
  localStorage.setItem('niza_usuario', JSON.stringify(usuario));
}

function clearSession() {
  localStorage.removeItem('niza_token');
  localStorage.removeItem('niza_usuario');
}

function getStoredUser() {
  const raw = localStorage.getItem('niza_usuario');
  return raw ? JSON.parse(raw) : null;
}

async function nizaLogin(email, password) {
  const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'No se pudo iniciar sesión');
  saveSession(data.access_token, data.usuario);
  return data;
}

async function nizaRegistro({ nombre, email, telefono, password }) {
  const res = await fetch(`${API_BASE_URL}/api/auth/registro`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nombre, email, telefono, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'No se pudo crear la cuenta');
  saveSession(data.access_token, data.usuario);
  return data;
}

function nizaLogout() {
  clearSession();
  window.location.href = 'index.html';
}

/** fetch() que agrega automáticamente el token de sesión, para endpoints protegidos. */
async function authFetch(url, options = {}) {
  const token = getToken();
  const headers = Object.assign({}, options.headers, token ? { Authorization: `Bearer ${token}` } : {});
  return fetch(url, Object.assign({}, options, { headers }));
}

/** Ajusta el ícono de cuenta en la navegación según haya o no sesión activa. */
function actualizarNavSesion() {
  const link = document.getElementById('account-link');
  const adminPill = document.getElementById('admin-pill-link');
  const usuario = getStoredUser();

  if (link) {
    if (usuario) {
      link.href = 'cuenta.html';
      link.title = usuario.nombre;
    } else {
      link.href = 'login.html';
      link.title = 'Iniciar sesión';
    }
  }
  if (adminPill) {
    adminPill.style.display = (usuario && usuario.rol === 'admin') ? '' : 'none';
  }
}

/** Protege las páginas del panel admin: si no hay sesión de admin, redirige a login. */
async function requireAdmin() {
  const token = getToken();
  if (!token) { window.location.href = 'login.html'; return; }
  try {
    const res = await authFetch(`${API_BASE_URL}/api/auth/me`);
    if (!res.ok) throw new Error();
    const usuario = await res.json();
    if (usuario.rol !== 'admin') { window.location.href = 'index.html'; return; }
  } catch {
    clearSession();
    window.location.href = 'login.html';
  }
}

function wireContactoForm() {
  var form = document.getElementById('form-contacto');
  if (!form) return;
  var feedback = document.getElementById('contacto-feedback');

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    var boton = form.querySelector('button[type="submit"]');
    var datos = {
      nombre: document.getElementById('contacto-nombre').value,
      correo: document.getElementById('contacto-correo').value,
      mensaje: document.getElementById('contacto-mensaje').value,
    };

    boton.disabled = true;
    feedback.className = 'form-feedback show';
    feedback.textContent = 'Enviando...';

    try {
      const res = await fetch(`${API_BASE_URL}/contacto/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datos),
      });
      if (!res.ok) throw new Error('Error al enviar');
      feedback.className = 'form-feedback show success';
      feedback.textContent = '¡Mensaje enviado! Te contactaremos pronto.';
      form.reset();
    } catch (err) {
      feedback.className = 'form-feedback show error';
      feedback.textContent = 'Hubo un error al enviar tu mensaje. Intenta de nuevo.';
    } finally {
      boton.disabled = false;
    }
  });
}


async function initCatalogoGrid() {
  const grid = document.getElementById('catalog-grid');
  if (!grid) return;
  try {
    const productos = await fetchProductos();
    grid.innerHTML = productos.map(productCardHTML).join('');
    // El modal de vista rápida se conecta a los links recién insertados
    wireQuickViewLinks();
  } catch (err) {
    grid.innerHTML = `<p style="grid-column:1/-1; text-align:center; color:var(--grey);">
      No se pudo conectar con el servidor (${err.message}). Verifica que el backend esté corriendo en ${API_BASE_URL}.
    </p>`;
  }
}

async function initCatalogoGridHome() {
  const grid = document.getElementById('catalog-grid-home');
  if (!grid) return;
  try {
    const productos = await fetchProductos();
    grid.innerHTML = productos.slice(0, 3).map(productCardHTML).join('');
    wireQuickViewLinks();
  } catch (err) {
    grid.innerHTML = `<p style="grid-column:1/-1; text-align:center; color:var(--grey);">
      No se pudo conectar con el servidor (${err.message}).
    </p>`;
  }
}

async function crearPedidoDesdeCarrito() {
  const cart = getCart();
  if (!cart.length) { alert('Tu carrito está vacío.'); return; }

  const productos = cart.filter(function (item) { return item.tipo !== 'curso'; });
  const cursos = cart.filter(function (item) { return item.tipo === 'curso'; });
  const soloDigital = productos.length === 0;

  let tipoEntrega = 'digital';
  let sucursalId = null;
  let fechaEntrega = new Date().toISOString().slice(0, 10); // fecha_entrega es obligatoria en el modelo, aunque sea pedido digital

  if (!soloDigital) {
    const tipoEntregaEl = document.querySelector('#tipo-entrega-options .opt.selected');
    tipoEntrega = tipoEntregaEl ? tipoEntregaEl.dataset.entrega : 'recoger';
    fechaEntrega = document.getElementById('checkout-fecha').value;

    if (!fechaEntrega) { alert('Selecciona una fecha de entrega.'); return; }

    if (tipoEntrega === 'recoger') {
      const filaSel = document.querySelector('#checkout-sucursal-rows .sucursal-row.sel');
      sucursalId = filaSel ? filaSel.dataset.id : null;
      if (!sucursalId) { alert('Selecciona una sucursal.'); return; }
    }
  }

  const datos = {
    sucursal_id: sucursalId,
    tipo_entrega: tipoEntrega,
    direccion_id: null,
    fecha_entrega: fechaEntrega,
    items: productos.map(function (item) {
      return {
        producto_id: item.producto_id,
        opcion_id: item.opcion_id || null,
        cantidad: item.cantidad,
        precio_unitario: item.precio_unitario,
      };
    }),
    cursos: cursos.map(function (item) { return item.curso_id; }),
  };

  const boton = document.getElementById('btn-pagar');
  boton.disabled = true;
  boton.textContent = 'Procesando...';

  try {
    const res = await authFetch(`${API_BASE_URL}/api/pedidos/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datos),
    });
    if (!res.ok) throw new Error('No se pudo crear el pedido');
    const pedido = await res.json();

    const prefRes = await authFetch(`${API_BASE_URL}/api/pagos/crear-preferencia/${pedido.id}`, {
      method: 'POST',
    });
    if (!prefRes.ok) throw new Error('No se pudo generar el pago');
    const preferencia = await prefRes.json();

    localStorage.removeItem(CART_KEY);
    window.location.href = preferencia.init_point;
  } catch (err) {
    alert('Hubo un error al procesar tu pedido. Verifica que hayas iniciado sesión.');
    boton.disabled = false;
    boton.textContent = 'Pagar con Mercado Pago';
  }
}

/* ---------- Carga dinámica de cursos ---------- */
async function initCursosGrid() {
  const grid = document.getElementById('cursos-grid');
  if (!grid) return;
  try {
    const cursos = await fetchCursos();
    grid.innerHTML = cursos.map(courseCardHTML).join('');
    wireCourseViewLinks();
  } catch (err) {
    grid.innerHTML = `<p style="grid-column:1/-1; text-align:center; color:var(--grey);">
      No se pudo conectar con el servidor (${err.message}). Verifica que el backend esté corriendo en ${API_BASE_URL}.
    </p>`;
  }
}

/* ---------- Cambiar whatsapp de contacto ---------- */
async function initWhatsappContactoLink() {
  const link = document.getElementById('wa-contacto-link');
  if (!link) return;
  try {
    const res = await fetch(`${API_BASE_URL}/api/configuracion/whatsapp_contacto`);
    if (!res.ok) return;
    const data = await res.json();
    const numeroLimpio = data.valor.replace(/\D/g, '');
    link.href = `https://wa.me/${numeroLimpio}`;
  } catch {
    // Si falla, el link se queda en "#" — no rompe la página
  }
}

/* ---------- Carga dinámica de cursos (home, solo 3) ---------- */
async function initCursosBandHome() {
  const grid = document.getElementById('courses-grid-home');
  if (!grid) return;
  try {
    const cursos = await fetchCursos();
    grid.innerHTML = cursos.slice(0, 3).map(homeCourseCardHTML).join('');
  } catch (err) {
    grid.innerHTML = `<p style="grid-column:1/-1; color:#D8CBB0; text-align:center;">No se pudieron cargar los cursos.</p>`;
  }
}

function homeCourseCardHTML(c) {
  const precioHTML = c.tiene_descuento
    ? `<span class="price-old" style="color:#B8A488;">$${Number(c.precio_original).toFixed(0)} MXN</span> $${Number(c.precio_final).toFixed(0)} MXN`
    : `$${Number(c.precio_final).toFixed(0)} MXN`;
  return `
    <a class="course-card" href="cursos.html">
      <div class="course-photo" style="${c.portada_url ? `background-image:url('${c.portada_url}'); background-size:cover; background-position:center;` : ''}"><span class="pdf-badge">PDF</span>${c.portada_url ? '' : 'Portada del curso'}</div>
      <div class="course-body"><h5>${c.nombre}</h5><div class="cprice">${precioHTML}</div></div>
    </a>`;
}

/* ---------- Filtros de catálogo (Todos / Catálogo fijo / Personalizados) ---------- */
function wireCatalogFilters() {
  var filters = document.querySelectorAll('.filter[data-filter]');
  if (!filters.length) return;
  filters.forEach(function (btn) {
    btn.addEventListener('click', function () {
      filters.forEach(function (f) { f.classList.remove('active'); });
      btn.classList.add('active');
      var value = btn.getAttribute('data-filter');
      document.querySelectorAll('.grid .card[data-category]').forEach(function (card) {
        var show = value === 'todos' || card.getAttribute('data-category') === value;
        card.style.display = show ? '' : 'none';
      });
    });
  });
}

/* ---------- Modal de vista rápida ("Ver más" en catálogo fijo) ---------- */
function wireQuickViewLinks() {
  var quickView = document.getElementById('quickView');
  if (!quickView) return;
  document.querySelectorAll('[data-quickview]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      document.getElementById('qvTitle').textContent = link.dataset.title;
      document.getElementById('qvPrice').textContent = link.dataset.price;
      document.getElementById('qvDesc').textContent = link.dataset.desc;
      var qvPhoto = document.getElementById('qvPhoto');
      if (link.dataset.photo) {
        qvPhoto.style.backgroundImage = `url('${link.dataset.photo}')`;
        qvPhoto.style.backgroundSize = 'cover';
        qvPhoto.style.backgroundPosition = 'center';
        qvPhoto.textContent = '';
      } else {
        qvPhoto.style.backgroundImage = '';
        qvPhoto.textContent = 'FOTO';
      }

      quickView.dataset.productoId = link.dataset.id;
      quickView.dataset.precioNum = link.dataset.priceNum;
      quickView.dataset.nombre = link.dataset.title;

      var qtyValue = quickView.querySelector('.qty-value');
      if (qtyValue) qtyValue.textContent = '1';

      var opciones = [];
      try { opciones = JSON.parse(decodeURIComponent(link.dataset.opciones || '%5B%5D')); } catch (err) {}
      renderQuickViewTamanos(opciones);

      quickView.classList.add('open');
    });
  });
}

function renderQuickViewTamanos(opciones) {
  var wrap = document.getElementById('qvTamanoWrap');
  var cont = document.getElementById('qvTamanoOptions');
  if (!wrap || !cont) return;
  if (!opciones.length) {
    wrap.style.display = 'none';
    return;
  }
  wrap.style.display = 'block';
  cont.innerHTML = opciones.map(function (o, i) {
    return `<div class="opt ${i === 0 ? 'selected' : ''}" data-opcion-id="${o.id}">${o.nombre}</div>`;
  }).join('');
  cont.querySelectorAll('.opt').forEach(function (opt) {
    opt.addEventListener('click', function () {
      cont.querySelectorAll('.opt').forEach(function (o) { o.classList.remove('selected'); });
      opt.classList.add('selected');
    });
  });
}

function wireQuickViewModalClose() {
  var quickView = document.getElementById('quickView');
  if (!quickView) return;
  var closeBtn = quickView.querySelector('.modal-close');
  if (closeBtn) closeBtn.addEventListener('click', function () { quickView.classList.remove('open'); });
  quickView.addEventListener('click', function (e) {
    if (e.target === quickView) quickView.classList.remove('open');
  });
}

/* ---------- Modal de vista rápida (cursos) ---------- */
function wireCourseViewLinks() {
  var courseView = document.getElementById('courseView');
  if (!courseView) return;
  document.querySelectorAll('[data-courseview]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      document.getElementById('cvTitle').textContent = link.dataset.title;
      document.getElementById('cvPrice').textContent = link.dataset.price;
      document.getElementById('cvDesc').textContent = link.dataset.desc;
      var cvPhoto = document.getElementById('cvPhoto');
      if (link.dataset.photo) {
        cvPhoto.style.backgroundImage = `url('${link.dataset.photo}')`;
        cvPhoto.style.backgroundSize = 'cover';
        cvPhoto.style.backgroundPosition = 'center';
        cvPhoto.textContent = '';
      } else {
        cvPhoto.style.backgroundImage = '';
        cvPhoto.textContent = 'Portada';
      }
      courseView.dataset.cursoId = link.dataset.id;
      courseView.dataset.nombre = link.dataset.title;
      courseView.dataset.precioNum = link.dataset.priceNum;
      courseView.classList.add('open');
    });
  });
}

function wireCourseViewModalClose() {
  var courseView = document.getElementById('courseView');
  if (!courseView) return;
  var closeBtn = courseView.querySelector('.modal-close');
  if (closeBtn) closeBtn.addEventListener('click', function () { courseView.classList.remove('open'); });
  courseView.addEventListener('click', function (e) {
    if (e.target === courseView) courseView.classList.remove('open');
  });
}

async function subirArchivo(archivo, tipo) {
  const formData = new FormData();
  formData.append('archivo', archivo);
  const res = await authFetch(`${API_BASE_URL}/api/uploads/${tipo}`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Error al subir el archivo');
  const data = await res.json();
  return data.url;
}

document.addEventListener('DOMContentLoaded', function () {
  // ... todo el resto sigue igual, sin la función adentro ...
});

document.addEventListener('DOMContentLoaded', function () {

  var tipoEntregaOptions = document.getElementById('tipo-entrega-options');
  if (tipoEntregaOptions) {
    tipoEntregaOptions.querySelectorAll('.opt').forEach(function (opt) {
      opt.addEventListener('click', function () {
        tipoEntregaOptions.querySelectorAll('.opt').forEach(function (o) { o.classList.remove('selected'); });
        opt.classList.add('selected');
        var esDelivery = opt.dataset.entrega === 'delivery';
        document.getElementById('delivery-direccion-wrap').style.display = esDelivery ? 'block' : 'none';
        document.getElementById('checkout-sucursal-rows').style.display = esDelivery ? 'none' : 'block';
      });
    });
  }


  var btnPagar = document.getElementById('btn-pagar');
  if (btnPagar) {
    btnPagar.addEventListener('click', crearPedidoDesdeCarrito);
  }

  actualizarContadorCarrito();

  var qvAddBtn = document.getElementById('qvAddToCart');
  if (qvAddBtn) {
    qvAddBtn.addEventListener('click', function () {
      var quickView = document.getElementById('quickView');
      var qtyEl = quickView.querySelector('.qty-value');
      var cantidad = qtyEl ? parseInt(qtyEl.textContent, 10) : 1;
      var tamanoSeleccionado = quickView.querySelector('#qvTamanoOptions .opt.selected');

      addToCart({
        producto_id: quickView.dataset.productoId,
        nombre: quickView.dataset.nombre,
        precio_unitario: parseFloat(quickView.dataset.precioNum),
        cantidad: cantidad,
        opcion_id: tamanoSeleccionado ? tamanoSeleccionado.dataset.opcionId : null,
        opcion_nombre: tamanoSeleccionado ? tamanoSeleccionado.textContent : null,
      });

      quickView.classList.remove('open');
      mostrarToastCarrito(quickView.dataset.nombre);
    });
  }

  var cvAddBtn = document.getElementById('cvAddToCart');
  if (cvAddBtn) {
    cvAddBtn.addEventListener('click', function () {
      var courseView = document.getElementById('courseView');
      addToCart({
        tipo: 'curso',
        curso_id: courseView.dataset.cursoId,
        nombre: courseView.dataset.nombre,
        precio_unitario: parseFloat(courseView.dataset.precioNum),
        cantidad: 1,
      });
      courseView.classList.remove('open');
      mostrarToastCarrito(courseView.dataset.nombre);
    });
  }

  /* ---------- Menú móvil (hamburguesa) ---------- */
  var menuToggle = document.querySelector('.menu-toggle');
  var navLinks = document.querySelector('.nav-links');
  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', function () {
      navLinks.classList.toggle('open');
    });
  }

  wireCatalogFilters();
  wireQuickViewLinks();
  wireQuickViewModalClose();
  wireCourseViewModalClose();
  actualizarNavSesion();

  /* ---------- Carga de datos reales desde el backend ---------- */
  initCatalogoGrid();
  initCatalogoGridHome();
  initCursosGrid();
  wireContactoForm();
  initCursosBandHome();
  initSucursalesPaneles('nosotros-sucursales');
  initSucursalesPaneles('contacto-sucursales');
  initSucursalSelect('cotiza-sucursal-select');
  initSucursalRows('checkout-sucursal-rows');
  initWhatsappContactoLink();
  initSucursalesFooter('footer-sucursales');
  renderCheckoutCart();

  /* ---------- Selector de opciones (tamaño, sabor, etc.) ---------- */
  document.querySelectorAll('.options').forEach(function (group) {
    group.querySelectorAll('.opt').forEach(function (opt) {
      opt.addEventListener('click', function () {
        group.querySelectorAll('.opt').forEach(function (o) { o.classList.remove('selected'); });
        opt.classList.add('selected');
      });
    });
  });

  /* ---------- Selector de sucursal (checkout) ---------- */
  document.querySelectorAll('.sucursal-row').forEach(function (row) {
    row.addEventListener('click', function () {
      var parent = row.parentElement;
      parent.querySelectorAll('.sucursal-row').forEach(function (r) { r.classList.remove('sel'); });
      row.classList.add('sel');
    });
  });

  /* ---------- Cantidad +/- (detalle de producto) ---------- */
  document.querySelectorAll('.qty-box').forEach(function (box) {
    var minus = box.querySelector('.qty-minus');
    var plus = box.querySelector('.qty-plus');
    var value = box.querySelector('.qty-value');
    if (!minus || !plus || !value) return;
    minus.addEventListener('click', function () {
      var v = parseInt(value.textContent, 10);
      if (v > 1) value.textContent = v - 1;
    });
    plus.addEventListener('click', function () {
      value.textContent = parseInt(value.textContent, 10) + 1;
    });
  });

  /* ---------- Validación de fecha mínima (formulario de cotización) ----------
     En producción, DIAS_MINIMOS vendría de la tabla `configuracion`
     (clave: dias_minimos_anticipacion) consultada al backend. */
  var fechaInput = document.getElementById('fecha-deseada');
  var fechaWarn = document.getElementById('fecha-warning');
  var diasTexto = document.getElementById('dias-minimos-texto');
  if (fechaInput && fechaWarn) {
    var DIAS_MINIMOS = 3; // valor de respaldo mientras carga el real
    fetch(`${API_BASE_URL}/api/configuracion/dias_minimos_anticipacion`)
      .then(function (res) { return res.ok ? res.json() : null; })
      .then(function (data) {
        if (data) {
          DIAS_MINIMOS = parseInt(data.valor, 10);
          if (diasTexto) diasTexto.textContent = DIAS_MINIMOS;
        }
      })
      .catch(function () {});

    fechaInput.addEventListener('change', function () {
      var hoy = new Date();
      var elegida = new Date(fechaInput.value);
      var diffDias = (elegida - hoy) / (1000 * 60 * 60 * 24);
      fechaWarn.classList.toggle('show', diffDias < DIAS_MINIMOS);
    });
  }

  /* ---------- Formulario de cotización: mostrar WhatsApp al enviar ---------- */
var quoteForm = document.getElementById('quote-form');
  var afterSubmit = document.getElementById('after-submit');
  if (quoteForm && afterSubmit) {
    quoteForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      var boton = quoteForm.querySelector('button[type="submit"]');
      var params = new URLSearchParams(window.location.search);

      var datos = {
        producto_id: params.get('producto'),
        nombre_cliente: document.getElementById('cotiza-nombre').value,
        sucursal_id: document.getElementById('cotiza-sucursal-select').value,
        tamano: quoteForm.querySelector('.field:nth-of-type(1) select').value,
        sabor: document.getElementById('cotiza-sabor').value,
        relleno: quoteForm.querySelector('#cotiza-relleno')
          ? document.getElementById('cotiza-relleno').value
          : null,
        decoracion_texto: document.getElementById('cotiza-decoracion').value,
        foto_referencia_url: document.getElementById('cotiza-foto-url') ? document.getElementById('cotiza-foto-url').value || null : null,
        mensaje_pastel: document.getElementById('cotiza-mensaje').value,
        fecha_deseada: document.getElementById('fecha-deseada').value,
        email_cliente: document.getElementById('cotiza-correo').value,
        telefono_cliente: document.getElementById('cotiza-telefono').value,
      };

      boton.disabled = true;
      boton.textContent = 'Enviando...';

      try {
        const res = await authFetch(`${API_BASE_URL}/api/cotizaciones/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(datos),
        });
        if (!res.ok) throw new Error('Error al enviar');
        afterSubmit.classList.add('show');
        afterSubmit.scrollIntoView({ behavior: 'smooth' });
        quoteForm.reset();
        const fotoResult = document.getElementById('cotiza-foto-result');
        const fotoTrigger = document.getElementById('cotiza-foto-trigger');
        if (fotoResult && fotoTrigger) {
          fotoResult.style.display = 'none';
          fotoTrigger.style.display = 'flex';
          document.getElementById('cotiza-foto-url').value = '';
        }
      } catch (err) {
        alert('Hubo un error al enviar tu solicitud. Intenta de nuevo.');
      } finally {
        boton.disabled = false;
        boton.textContent = 'Enviar solicitud';
      }
    });
  }

});

