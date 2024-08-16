document.addEventListener('DOMContentLoaded', function() {
    const paso1 = document.getElementById('paso1');
    const paso2 = document.getElementById('paso2');
    const paso3 = document.getElementById('paso3');
    const paso4 = document.getElementById('paso4');
    const continuarPaso1 = document.getElementById('continuarPaso1');
    const continuarPaso2 = document.getElementById('continuarPaso2');
    const continuarPaso3 = document.getElementById('continuarPaso3');
    const volverPaso1 = document.getElementById('volverPaso1');
    const volverPaso2 = document.getElementById('volverPaso2');
    const volverPaso3 = document.getElementById('volverPaso3');
    const servicioSelect = document.getElementById('id_servicio');
    const empleadoSelect = document.getElementById('id_empleado');
    const fechaInput = document.getElementById('id_fecha');
    const horaInicioInput = document.getElementById('id_hora_inicio');
    const bloquesContainer = document.getElementById('bloquesHorarios');

    continuarPaso1.addEventListener('click', function() {
        if (servicioSelect.value) {
            paso1.style.display = 'none';
            paso2.style.display = 'block';
            cargarEmpleados();
        } else {
            alert('Por favor, selecciona un servicio.');
        }
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
    });

    volverPaso2.addEventListener('click', function() {
        paso3.style.display = 'none';
        paso2.style.display = 'block';
    });

    volverPaso3.addEventListener('click', function() {
        paso4.style.display = 'none';
        paso3.style.display = 'block';
    });

    function cargarEmpleados() {
        const servicioId = servicioSelect.value;
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
        const fecha = fechaInput.value;
        
        fetch(`/citas/get_bloques_disponibles/?empleado=${empleadoId}&fecha=${fecha}`)
            .then(response => response.json())
            .then(data => {
                bloquesContainer.innerHTML = '';
                data.bloques.forEach(bloque => {
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.classList.add('btn', 'btn-outline-primary', 'm-1');
                    button.textContent = `${bloque.inicio} - ${bloque.fin}`;
                    button.onclick = function() {
                        horaInicioInput.value = bloque.inicio;
                        bloquesContainer.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
                        button.classList.add('active');
                    };
                    bloquesContainer.appendChild(button);
                });
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Hubo un problema al cargar los horarios disponibles. Por favor, intenta de nuevo.');
            });
    }

    servicioSelect.addEventListener('change', cargarEmpleados);
    fechaInput.addEventListener('change', cargarBloquesHorarios);
});