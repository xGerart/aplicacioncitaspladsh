document.addEventListener('DOMContentLoaded', function() {
    const pasos = [
        document.getElementById('paso1'),
        document.getElementById('paso2'),
        document.getElementById('paso3'),
        document.getElementById('paso4')
    ];
    const botones = {
        continuar: [null, document.getElementById('continuarPaso2'), document.getElementById('continuarPaso3')],
        volver: [null, document.getElementById('volverPaso1'), document.getElementById('volverPaso2'), document.getElementById('volverPaso3')]
    };
    const servicioIdInput = document.getElementById('servicio_id');
    const empleadoSelect = document.getElementById('id_empleado');
    const fechaInput = document.getElementById('id_fecha');
    const horaInicioInput = document.getElementById('id_hora_inicio');
    const bloquesContainer = document.getElementById('bloquesHorarios');
    const servicioButtons = document.querySelectorAll('.seleccionar-servicio');
    const progressBar = document.querySelector('.progress-bar');
    const horarioCierre = document.getElementById('horario_cierre').value;

    // Configurar fecha mínima y máxima
    function actualizarFechaMinima() {
        fetch('/get_current_time/')
            .then(response => response.json())
            .then(data => {
                const hoy = data.current_time.split(' ')[0];  // Obtiene solo la fecha
                fechaInput.min = hoy;
                
                if (!fechaInput.value) {
                    fechaInput.value = hoy;
                }
                
                console.log('Fecha mínima actualizada:', hoy);
            })
            .catch(error => {
                console.error('Error al obtener la hora actual:', error);
            });
    }

    actualizarFechaMinima();
    fechaInput.addEventListener('focus', actualizarFechaMinima);

    function actualizarProgressBar(paso) {
        const porcentaje = paso * 25;
        progressBar.style.width = `${porcentaje}%`;
        progressBar.setAttribute('aria-valuenow', porcentaje);
        progressBar.textContent = `Paso ${paso}`;
    }

    function mostrarPaso(pasoActual) {
        pasos.forEach((paso, index) => {
            paso.style.display = index === pasoActual - 1 ? 'block' : 'none';
        });
        actualizarProgressBar(pasoActual);
    }

    function mostrarAlerta(mensaje, tipo) {
        const alertaExistente = document.querySelector('.alert');
        if (alertaExistente) alertaExistente.remove();
        const alerta = document.createElement('div');
        alerta.className = `alert alert-${tipo} alert-dismissible fade show mt-3`;
        alerta.innerHTML = `
            ${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        bloquesContainer.insertAdjacentElement('beforebegin', alerta);
    }

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
                mostrarAlerta('Hubo un problema al cargar los empleados. Por favor, intenta de nuevo.', 'danger');
            });
    }

    function cargarBloquesHorarios() {
        const empleadoId = empleadoSelect.value;
        const servicioId = servicioIdInput.value;
        const fecha = fechaInput.value;
        
        fetch('/get_current_time/')
            .then(response => response.json())
            .then(data => {
                const horaActual = data.current_time;
                
                fetch(`/citas/get_bloques_disponibles/?empleado=${empleadoId}&servicio=${servicioId}&fecha=${fecha}&hora_actual=${horaActual}`)
                    .then(response => {
                        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                        return response.json();
                    })
                    .then(data => {
                        bloquesContainer.innerHTML = '';
                        if (data.error) throw new Error(data.error);
                        if (data.mensaje) {
                            mostrarAlerta(data.mensaje, 'info');
                        } else if (data.bloques && data.bloques.length > 0) {
                            const bloquesGrid = document.createElement('div');
                            bloquesGrid.className = 'bloques-horarios-grid';
                            data.bloques.forEach(bloque => {
                                const button = document.createElement('button');
                                button.type = 'button';
                                button.className = 'btn btn-outline-primary bloque-horario';
                                button.textContent = bloque.inicio;
                                if (empleadoId === '0') {
                                    button.title = bloque.empleado_nombre;
                                }
                                button.onclick = function() {
                                    horaInicioInput.value = bloque.inicio;
                                    document.getElementById('id_empleado').value = bloque.empleado_id;
                                    bloquesGrid.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
                                    button.classList.add('active');
                                };
                                bloquesGrid.appendChild(button);
                            });
                            bloquesContainer.appendChild(bloquesGrid);
                        } else {
                            mostrarAlerta('No hay horarios disponibles para este día.', 'info');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        mostrarAlerta(`Error: ${error.message}. Por favor, intenta de nuevo.`, 'danger');
                    });
            })
            .catch(error => {
                console.error('Error al obtener la hora actual:', error);
                mostrarAlerta('Error al cargar los horarios. Por favor, intenta de nuevo.', 'danger');
            });
    }

    servicioButtons.forEach(button => {
        button.addEventListener('click', function() {
            const servicioId = this.getAttribute('data-servicio-id');
            if (servicioIdInput) {
                servicioIdInput.value = servicioId;
                mostrarPaso(2);
                cargarEmpleados(servicioId);
            } else {
                mostrarAlerta('Hubo un problema al seleccionar el servicio. Por favor, recarga la página e intenta de nuevo.', 'danger');
            }
        });
    });

    botones.continuar.forEach((boton, index) => {
        if (boton) {
            boton.addEventListener('click', function() {
                const pasoActual = index + 1;
                if (pasoActual === 2 && !empleadoSelect.value) {
                    mostrarAlerta('Por favor, selecciona un empleado.', 'warning');
                } else if (pasoActual === 3 && !fechaInput.value) {
                    mostrarAlerta('Por favor, selecciona una fecha.', 'warning');
                } else {
                    mostrarPaso(pasoActual + 1);
                    if (pasoActual === 3) cargarBloquesHorarios();
                }
            });
        }
    });

    botones.volver.forEach((boton, index) => {
        if (boton) {
            boton.addEventListener('click', () => mostrarPaso(index));
        }
    });

    fechaInput.addEventListener('change', cargarBloquesHorarios);
    
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
});