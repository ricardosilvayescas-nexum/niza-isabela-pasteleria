-- ============================================================
-- seed.sql — Datos de ejemplo para probar el sitio de punta a punta
-- Ejecutar DESPUÉS de crear las tablas (script de 03-Base-de-Datos.md)
-- ============================================================

-- Sucursales
INSERT INTO sucursales (id, nombre, direccion, horario, telefono) VALUES
(NEWID(), 'Sucursal 1 — Centro', 'Av. Central 123, Amecameca, Edo. Méx.', 'Lun–Sáb 9:00–19:00', '5500000000'),
(NEWID(), 'Sucursal 2', 'Calle Secundaria 456, Amecameca, Edo. Méx.', 'Lun–Sáb 9:00–19:00', '5500000001');

-- Configuración inicial
-- Nota: 'dias_minimos_anticipacion' ya se insertó en el script de creación de tablas.
-- Si ya existe, este INSERT solo agrega el WhatsApp de contacto.
IF NOT EXISTS (SELECT 1 FROM configuracion WHERE clave = 'whatsapp_contacto')
    INSERT INTO configuracion (clave, valor) VALUES ('whatsapp_contacto', '+525500000000');

-- Productos de catálogo fijo
INSERT INTO productos (id, nombre, descripcion, tipo, precio_base, foto_url, activo) VALUES
(NEWID(), 'Pastel de Vainilla Clásico', 'Bizcocho de vainilla con betún de mantequilla. Ideal para 8–10 personas.', 'fijo', 450.00, '/img/vainilla.jpg', 1),
(NEWID(), 'Red Velvet', 'Bizcocho rojo aterciopelado con betún de queso crema. Ideal para 8–10 personas.', 'fijo', 520.00, '/img/red-velvet.jpg', 1),
(NEWID(), 'Pastel de Chocolate', 'Bizcocho de chocolate con ganache. Ideal para 8–10 personas.', 'fijo', 480.00, '/img/chocolate.jpg', 1),
(NEWID(), 'Caja de Postres Individuales', '6 piezas surtidas de mini postres.', 'fijo', 320.00, '/img/postres.jpg', 1);

-- Productos personalizables
INSERT INTO productos (id, nombre, descripcion, tipo, precio_base, foto_url, activo) VALUES
(NEWID(), 'Pastel a Medida', 'Diseñamos contigo cada detalle: tamaño, sabor, relleno y decoración.', 'personalizable', 600.00, '/img/a-medida.jpg', 1),
(NEWID(), 'Pastel Temático (XV años, boda, infantil)', 'Ideal para ocasiones especiales.', 'personalizable', 900.00, '/img/tematico.jpg', 1);

-- Cursos
INSERT INTO cursos (id, nombre, descripcion, precio, portada_url, archivo_pdf_url, activo) VALUES
(NEWID(), 'Fundamentos de Repostería Francesa', 'Técnicas base: masas, cremas y montaje de entremets. 42 páginas.', 350.00, '/img/curso-fundamentos.jpg', '/pdfs/fundamentos.pdf', 1),
(NEWID(), 'Decoración con Manga y Boquillas', 'Guía práctica de técnicas de decorado paso a paso. 30 páginas.', 280.00, '/img/curso-decoracion.jpg', '/pdfs/decoracion.pdf', 1),
(NEWID(), 'Pasteles para Ocasiones Especiales', 'Recetario completo para XV años, bodas y cumpleaños. 55 páginas.', 420.00, '/img/curso-ocasiones.jpg', '/pdfs/ocasiones.pdf', 1);
