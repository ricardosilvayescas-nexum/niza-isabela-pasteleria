const API_BASE = "http://127.0.0.1:8000";

document.getElementById("form-contacto").addEventListener("submit", async (e) => {
  e.preventDefault();

  const feedback = document.getElementById("contacto-feedback");
  const boton = e.target.querySelector("button[type='submit']");

  const datos = {
    nombre: document.getElementById("contacto-nombre").value,
    correo: document.getElementById("contacto-correo").value,
    mensaje: document.getElementById("contacto-mensaje").value,
  };

  boton.disabled = true;
  feedback.textContent = "Enviando...";
  feedback.style.color = "inherit";

  try {
    const res = await fetch(`${API_BASE}/contacto/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datos),
    });

    if (!res.ok) throw new Error("Error al enviar");

    feedback.textContent = "¡Mensaje enviado! Te contactaremos pronto.";
    feedback.style.color = "green";
    e.target.reset();
  } catch (err) {
    feedback.textContent = "Hubo un error al enviar tu mensaje. Intenta de nuevo.";
    feedback.style.color = "red";
  } finally {
    boton.disabled = false;
  }
});