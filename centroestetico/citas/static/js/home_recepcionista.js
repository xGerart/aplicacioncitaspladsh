function cargarResumen() {
    console.log("Iniciando cargarResumen");
    fetch('/citas/resumen_recepcionista/')
      .then(response => {
        console.log("Respuesta recibida:", response);
        if (!response.ok) {
          throw new Error('Error en la respuesta del servidor: ' + response.status);
        }
        return response.json();
      })
      .then(data => {
        console.log("Datos recibidos:", data);
        document.getElementById('citasHoy').textContent = data.citas_hoy + " citas programadas";
        if (data.proxima_cita) {
          document.getElementById('proximaCita').innerHTML = 
            `<strong>${data.proxima_cita.cliente}</strong><br>
             ${data.proxima_cita.servicio}<br>
             <small class="text-muted">Hoy a las ${data.proxima_cita.hora}</small>`;
        } else {
          document.getElementById('proximaCita').textContent = "No hay citas próximas";
        }
      })
      .catch(error => {
        console.error('Error:', error);
        document.getElementById('citasHoy').textContent = "Error al cargar datos: " + error.message;
        document.getElementById('proximaCita').textContent = "Error al cargar datos: " + error.message;
      });
  }