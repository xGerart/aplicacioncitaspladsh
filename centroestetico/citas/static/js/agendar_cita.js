document.addEventListener('DOMContentLoaded', function() {
    const paso1 = document.getElementById('paso1');
    const paso2 = document.getElementById('paso2');
    const paso3 = document.getElementById('paso3');
    const paso4 = document.getElementById('paso4');
    const continuarPaso2 = document.getElementById('continuarPaso2');
    const continuarPaso3 = document.getElementById('continuarPaso3');
    const volverPaso1 = document.getElementById('volverPaso1');
    const volverPaso2 = document.getElementById('volverPaso2');
    const volverPaso3 = document.getElementById('volverPaso3');
    const servicioIdInput = document.getElementById('servicio_id');
    const empleadoSelect = document.getElementById('id_empleado');
    const fechaInput = document.getElementById('id_fecha');
    const horaInicioInput = document.getElementById('id_hora_inicio');
    const bloquesContainer = document.getElementById('bloquesHorarios');
    const servicioButtons = document.querySelectorAll('.seleccionar-servicio');
    const hoy = new Date();
    const yyyy = hoy.getFullYear();
    const mm = String(hoy.getMonth() + 1).padStart(2, '0');
    const dd = String(hoy.getDate()).padStart(2, '0');
    const fechaMinima = `${yyyy}-${mm}-${dd}`;
    fechaInput.setAttribute('min', fechaMinima);

    servicioButtons.forEach(button => {
        button.addEventListener('click', function() {
            const servicioId = this.getAttribute('data-servicio-id');
            servicioIdInput.value = servicioId;
            paso1.style.display = 'none';
            paso2.style.display = 'block';
            cargarEmpleados(servicioId);
        });
    });

    continuarPaso2.addEventListener('click', function() {
        if (empleadoSelect.value) {
            paso2.style.display = 'none';
            paso3.style.display = 'block';
        } else {
            alert('Por favor, selecciona un empleado.');
        }
    });

    continuarPaso3.addEventListener('click', function() {
        if (fechaInput.value) {
            paso3.style.display = 'none';
            paso4.style.display = 'block';
            cargarBloquesHorarios();
        } else {
            alert('Por favor, selecciona una fecha.');
        }
    });

    volverPaso1.addEventListener('click', function() {
        paso2.style.display = 'none';
        paso1.style.display = 'block';
        window.location.reload();
    });

    volverPaso2.addEventListener('click', function() {
        paso3.style.display = 'none';
        paso2.style.display = 'block';
        window.location.reload();
    });

    volverPaso3.addEventListener('click', function() {
        paso4.style.display = 'none';
        paso3.style.display = 'block';
        window.location.reload();
    });

    function cargarEmpleados(servicioId) {
        fetch(`/citas/get_empleados_disponibles/?servicio=${servicioId}`)
            .then(response => response.json())
            .then(data => {
                empleadoSelect.innerHTML = '<option value="">Selecciona un empleado</option>';
                data.empleados.forEach(empleado => {
                    const option = document.createElement('option');
                    option.value = empleado.id;
                    option.textContent = empleado.nombre;
                    empleadoSelect.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Hubo un problema al cargar los empleados. Por favor, intenta de nuevo.');
            });
    }

    function cargarBloquesHorarios() {
        const empleadoId = empleadoSelect.value;
        const servicioId = document.getElementById('servicio_id').value;
        const fecha = fechaInput.value;
        
        fetch(`/citas/get_bloques_disponibles/?empleado=${empleadoId}&servicio=${servicioId}&fecha=${fecha}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                bloquesContainer.innerHTML = '';
                if (data.error) {
                    throw new Error(data.error);
                }
                if (data.mensaje) {
                    const mensajeElement = document.createElement('p');
                    mensajeElement.textContent = data.mensaje;
                    mensajeElement.classList.add('alert', 'alert-info');
                    bloquesContainer.appendChild(mensajeElement);
                } else if (data.bloques.length === 0) {
                    const mensajeElement = document.createElement('p');
                    mensajeElement.textContent = 'No hay horarios disponibles para este día.';
                    mensajeElement.classList.add('alert', 'alert-info');
                    bloquesContainer.appendChild(mensajeElement);
                } else {
                    data.bloques.forEach(bloque => {
                        const button = document.createElement('button');
                        button.type = 'button';
                        button.classList.add('btn', 'btn-outline-primary', 'm-1');
                        button.textContent = `${bloque.inicio} - ${bloque.fin}`;
                        if (empleadoId === '0') {
                            button.textContent += ` (${bloque.empleado_nombre})`;
                        }
                        button.onclick = function() {
                            horaInicioInput.value = bloque.inicio;
                            document.getElementById('id_empleado').value = bloque.empleado_id;
                            bloquesContainer.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
                            button.classList.add('active');
                        };
                        bloquesContainer.appendChild(button);
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                bloquesContainer.innerHTML = '';
                const mensajeError = document.createElement('p');
                mensajeError.textContent = `Error: ${error.message}. Por favor, intenta de nuevo.`;
                mensajeError.classList.add('alert', 'alert-danger');
                bloquesContainer.appendChild(mensajeError);
            });
    }
    fechaInput.addEventListener('change', cargarBloquesHorarios);
    
});