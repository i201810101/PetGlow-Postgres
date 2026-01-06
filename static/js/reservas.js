// static/js/reservas.js - CRUD completo para reservas

// Variables globales
let reservaAEliminar = null;
let reservaCambioEstado = { id: null, estado: null };

// Función para buscar reservas
function buscarReservas() {
    const busqueda = document.getElementById('buscador-reservas')?.value.toLowerCase() || '';
    const filtroEstado = document.getElementById('filtro-estado')?.value || '';
    const filtroFecha = document.getElementById('filtro-fecha')?.value || '';
    const filas = document.querySelectorAll('#cuerpo-tabla-reservas tr');
    
    let encontrados = 0;
    let hoy = 0;
    let pendientes = 0;
    let completadas = 0;
    let canceladas = 0;
    const fechaHoy = new Date().toISOString().split('T')[0];
    
    filas.forEach(fila => {
        if (fila.id === 'sin-resultados') return;
        
        const codigo = fila.getAttribute('data-codigo') || '';
        const mascota = fila.getAttribute('data-mascota') || '';
        const cliente = fila.getAttribute('data-cliente') || '';
        const estado = fila.getAttribute('data-estado') || '';
        const fecha = fila.getAttribute('data-fecha') || '';
        
        // Aplicar filtros
        let pasaFiltroEstado = true;
        if (filtroEstado && estado !== filtroEstado) {
            pasaFiltroEstado = false;
        }
        
        let pasaFiltroFecha = true;
        if (filtroFecha && fecha !== filtroFecha) {
            pasaFiltroFecha = false;
        }
        
        // Aplicar búsqueda
        let pasaBusqueda = true;
        if (busqueda) {
            pasaBusqueda = codigo.includes(busqueda) || 
                          mascota.includes(busqueda) || 
                          cliente.includes(busqueda);
        }
        
        // Mostrar/ocultar fila
        if (pasaFiltroEstado && pasaFiltroFecha && pasaBusqueda) {
            fila.style.display = '';
            encontrados++;
            
            // Contar estadísticas
            if (estado === 'pendiente') pendientes++;
            if (estado === 'completada') completadas++;
            if (estado === 'cancelada') canceladas++;
            if (fecha === fechaHoy) hoy++;
        } else {
            fila.style.display = 'none';
        }
    });
    
    // Actualizar contadores
    document.getElementById('total-reservas').textContent = encontrados;
    document.getElementById('total-hoy').textContent = hoy;
    document.getElementById('total-pendientes').textContent = pendientes;
    document.getElementById('total-completadas').textContent = completadas;
    document.getElementById('total-canceladas').textContent = canceladas;
    
    // Mostrar mensaje si no hay resultados
    const cuerpoTabla = document.getElementById('cuerpo-tabla-reservas');
    if (encontrados === 0 && filas.length > 0) {
        if (!document.getElementById('sin-resultados')) {
            const mensaje = document.createElement('tr');
            mensaje.id = 'sin-resultados';
            mensaje.innerHTML = `
                <td colspan="8" class="text-center py-4">
                    <i class="fas fa-search fa-2x text-muted mb-3"></i>
                    <p class="text-muted">No se encontraron reservas con los criterios de búsqueda</p>
                    <button class="btn btn-sm btn-outline-secondary" id="btn-limpiar-filtros">
                        <i class="fas fa-times me-1"></i>Limpiar filtros
                    </button>
                </td>
            `;
            cuerpoTabla.appendChild(mensaje);
            
            document.getElementById('btn-limpiar-filtros').addEventListener('click', function() {
                document.getElementById('buscador-reservas').value = '';
                document.getElementById('filtro-estado').value = '';
                document.getElementById('filtro-fecha').value = '';
                buscarReservas();
            });
        }
    } else {
        const mensaje = document.getElementById('sin-resultados');
        if (mensaje) mensaje.remove();
    }
}

// Función para mostrar modal de cambio de estado
function mostrarModalCambioEstado(reservaId, codigoReserva, nuevoEstado) {
    reservaCambioEstado = { id: reservaId, estado: nuevoEstado };
    
    document.getElementById('codigo-reserva-cambio').textContent = codigoReserva;
    
    const estadoTextos = {
        'pendiente': 'Pendiente',
        'confirmada': 'Confirmada',
        'en_proceso': 'En Proceso',
        'completada': 'Completada',
        'cancelada': 'Cancelada',
        'no_show': 'No Show'
    };
    
    document.getElementById('nuevo-estado-texto').textContent = estadoTextos[nuevoEstado] || nuevoEstado;
    
    // Mensaje especial para cancelación
    const mensajeConfirmacion = document.getElementById('mensaje-confirmacion');
    if (nuevoEstado === 'cancelada') {
        mensajeConfirmacion.innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Atención:</strong> Esta acción enviará una notificación al cliente.
            </div>
        `;
    } else {
        mensajeConfirmacion.innerHTML = `
            <p class="text-muted">Esta acción actualizará el estado de la reserva en el sistema.</p>
        `;
    }
    
    const modalElement = document.getElementById('modal-cambio-estado');
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    }
}

// Función para cambiar estado de reserva
function cambiarEstadoReserva() {
    if (!reservaCambioEstado.id || !reservaCambioEstado.estado) {
        mostrarNotificacion('Error', 'error', 'Datos de reserva no válidos');
        return;
    }
    
    fetch(`/reservas/cambiar-estado/${reservaCambioEstado.id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ estado: reservaCambioEstado.estado })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            mostrarNotificacion('Éxito', 'success', data.message);
            // Cerrar modal
            const modalElement = document.getElementById('modal-cambio-estado');
            if (modalElement) {
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) modal.hide();
            }
            // Recargar después de 1.5 segundos
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            mostrarNotificacion('Error', 'error', data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarNotificacion('Error', 'error', 'Error al cambiar el estado de la reserva');
    });
}

// Función para validar formulario de reserva
function validarFormularioReserva() {
    const form = event.target;
    const idMascota = form.querySelector('#id_mascota');
    const idEmpleado = form.querySelector('#id_empleado');
    const fechaReserva = form.querySelector('#fecha_reserva');
    const horaReserva = form.querySelector('#hora_reserva');
    const serviciosCheckboxes = form.querySelectorAll('input[name="servicios[]"]:checked');
    
    let errores = [];
    
    // Validar mascota
    if (!idMascota.value) {
        errores.push('Debes seleccionar una mascota');
        idMascota.classList.add('is-invalid');
    } else {
        idMascota.classList.remove('is-invalid');
        idMascota.classList.add('is-valid');
    }
    
    // Validar empleado
    if (!idEmpleado.value) {
        errores.push('Debes seleccionar un empleado');
        idEmpleado.classList.add('is-invalid');
    } else {
        idEmpleado.classList.remove('is-invalid');
        idEmpleado.classList.add('is-valid');
    }
    
    // Validar fecha
    if (!fechaReserva.value) {
        errores.push('La fecha es obligatoria');
        fechaReserva.classList.add('is-invalid');
    } else {
        // Validar que no sea fecha pasada
        const fechaSeleccionada = new Date(fechaReserva.value);
        const hoy = new Date();
        hoy.setHours(0, 0, 0, 0);
        
        if (fechaSeleccionada < hoy) {
            errores.push('No se pueden crear reservas en fechas pasadas');
            fechaReserva.classList.add('is-invalid');
        } else {
            fechaReserva.classList.remove('is-invalid');
            fechaReserva.classList.add('is-valid');
        }
    }
    
    // Validar hora
    if (!horaReserva.value) {
        errores.push('La hora es obligatoria');
        horaReserva.classList.add('is-invalid');
    } else {
        horaReserva.classList.remove('is-invalid');
        horaReserva.classList.add('is-valid');
    }
    
    // Validar servicios
    if (serviciosCheckboxes.length === 0) {
        errores.push('Debes seleccionar al menos un servicio');
        document.getElementById('servicios-error').style.display = 'block';
    } else {
        document.getElementById('servicios-error').style.display = 'none';
    }
    
    // Mostrar errores si los hay
    if (errores.length > 0) {
        mostrarNotificacion('Corrige los siguientes errores:', 'error', errores);
        event.preventDefault();
        return false;
    }
    
    return true;
}

// Función para mostrar notificaciones
function mostrarNotificacion(titulo, tipo, mensajes) {
    const notificacionesPrevias = document.querySelectorAll('.notificacion-personalizada');
    notificacionesPrevias.forEach(n => n.remove());
    
    const tipos = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };
    
    const alerta = document.createElement('div');
    alerta.className = `alert ${tipos[tipo]} alert-dismissible fade show notificacion-personalizada`;
    alerta.style.position = 'fixed';
    alerta.style.top = '80px';
    alerta.style.right = '20px';
    alerta.style.zIndex = '1050';
    alerta.style.minWidth = '300px';
    alerta.style.maxWidth = '400px';
    
    let contenido = `<strong>${titulo}</strong>`;
    if (Array.isArray(mensajes)) {
        contenido += '<ul class="mb-0 mt-2" style="padding-left: 20px;">';
        mensajes.forEach(mensaje => {
            contenido += `<li style="margin-bottom: 5px;">${mensaje}</li>`;
        });
        contenido += '</ul>';
    } else {
        contenido += `<p class="mb-0 mt-2">${mensajes}</p>`;
    }
    
    alerta.innerHTML = `
        ${contenido}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alerta);
    
    setTimeout(() => {
        if (alerta.parentNode) {
            alerta.remove();
        }
    }, tipo === 'error' ? 8000 : 5000);
}

// Función para alternar entre vistas (lista/calendario)
function alternarVista(vista) {
    const vistaLista = document.getElementById('vista-lista');
    const vistaCalendario = document.getElementById('vista-calendario');
    const botonesVista = document.querySelectorAll('[data-vista]');
    
    botonesVista.forEach(boton => {
        boton.classList.remove('active');
        if (boton.getAttribute('data-vista') === vista) {
            boton.classList.add('active');
        }
    });
    
    if (vista === 'lista') {
        vistaLista.classList.remove('d-none');
        vistaCalendario.classList.add('d-none');
    } else {
        vistaLista.classList.add('d-none');
        vistaCalendario.classList.remove('d-none');
        inicializarCalendario();
    }
}

// Función para inicializar calendario (opcional)
function inicializarCalendario() {
    const calendarioEl = document.getElementById('calendario-reservas');
    if (!calendarioEl) return;
    
    // Limpiar calendario existente
    calendarioEl.innerHTML = '';
    
    // Obtener reservas de la tabla
    const eventos = [];
    const filas = document.querySelectorAll('#cuerpo-tabla-reservas tr');
    
    filas.forEach(fila => {
        if (fila.style.display === 'none') return;
        
        const id = fila.getAttribute('data-id');
        const codigo = fila.getAttribute('data-codigo');
        const mascota = fila.querySelector('td:nth-child(3) strong').textContent;
        const fecha = fila.getAttribute('data-fecha');
        const hora = fila.querySelector('td:nth-child(2) small').textContent;
        const estado = fila.getAttribute('data-estado');
        
        // Mapear estados a colores
        const colores = {
            'pendiente': '#ffc107',
            'confirmada': '#0dcaf0',
            'en_proceso': '#0d6efd',
            'completada': '#198754',
            'cancelada': '#dc3545',
            'no_show': '#6c757d'
        };
        
        const evento = {
            id: id,
            title: `${mascota} - ${codigo}`,
            start: `${fecha}T${hora}:00`,
            color: colores[estado] || '#6c757d',
            extendedProps: {
                codigo: codigo,
                estado: estado
            }
        };
        
        eventos.push(evento);
    });
    
    // Inicializar FullCalendar si está disponible
    if (typeof FullCalendar !== 'undefined') {
        const calendar = new FullCalendar.Calendar(calendarioEl, {
            initialView: 'dayGridMonth',
            locale: 'es',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            events: eventos,
            eventClick: function(info) {
                window.location.href = `/reservas/ver/${info.event.id}`;
            }
        });
        calendar.render();
    } else {
        calendarioEl.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                La vista de calendario requiere la librería FullCalendar.
                <a href="https://fullcalendar.io/" target="_blank">Instalar FullCalendar</a>
            </div>
        `;
    }
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('Reservas JS cargado correctamente');
    
    // Inicializar buscador
    const buscador = document.getElementById('buscador-reservas');
    const filtroEstado = document.getElementById('filtro-estado');
    const filtroFecha = document.getElementById('filtro-fecha');
    const btnLimpiar = document.getElementById('btn-limpiar-busqueda');
    
    if (buscador) {
        buscador.addEventListener('input', buscarReservas);
    }
    
    if (filtroEstado) {
        filtroEstado.addEventListener('change', buscarReservas);
    }
    
    if (filtroFecha) {
        filtroFecha.addEventListener('change', buscarReservas);
    }
    
    if (btnLimpiar) {
        btnLimpiar.addEventListener('click', function() {
            if (buscador) {
                buscador.value = '';
                buscarReservas();
            }
        });
    }
    
    // Botones de filtros rápidos
    document.querySelectorAll('[data-filtro]').forEach(boton => {
        boton.addEventListener('click', function(e) {
            e.preventDefault();
            const filtro = this.getAttribute('data-filtro');
            
            const hoy = new Date();
            switch(filtro) {
                case 'hoy':
                    document.getElementById('filtro-fecha').value = hoy.toISOString().split('T')[0];
                    break;
                case 'semana':
                    // Lógica para esta semana
                    break;
                case 'mes':
                    // Lógica para este mes
                    break;
                case 'pendientes':
                    document.getElementById('filtro-estado').value = 'pendiente';
                    break;
                case 'completadas':
                    document.getElementById('filtro-estado').value = 'completada';
                    break;
            }
            
            buscarReservas();
        });
    });
    
    // Botones de cambio de vista
    document.querySelectorAll('[data-vista]').forEach(boton => {
        boton.addEventListener('click', function() {
            const vista = this.getAttribute('data-vista');
            alternarVista(vista);
        });
    });
    
    // Botones de cambio de estado
    document.querySelectorAll('.cambiar-estado').forEach(boton => {
        boton.addEventListener('click', function(e) {
            e.preventDefault();
            const fila = this.closest('tr');
            const reservaId = fila.getAttribute('data-id');
            const codigoReserva = fila.querySelector('.badge.bg-dark').textContent;
            const nuevoEstado = this.getAttribute('data-estado');
            
            mostrarModalCambioEstado(reservaId, codigoReserva, nuevoEstado);
        });
    });
    
    // Confirmar cambio de estado
    const btnConfirmarCambio = document.getElementById('btn-confirmar-cambio');
    if (btnConfirmarCambio) {
        btnConfirmarCambio.addEventListener('click', cambiarEstadoReserva);
    }
    
    // Agregar validación a formularios de reserva
    const forms = document.querySelectorAll('form[action*="reserva"]');
    forms.forEach(form => {
        form.addEventListener('submit', validarFormularioReserva);
        
        // Validación en tiempo real para fechas
        const fechaInput = form.querySelector('#fecha_reserva');
        const horaInput = form.querySelector('#hora_reserva');
        
        if (fechaInput) {
            fechaInput.addEventListener('change', function() {
                const hoy = new Date();
                hoy.setHours(0, 0, 0, 0);
                const fechaSeleccionada = new Date(this.value);
                
                if (fechaSeleccionada < hoy) {
                    this.classList.add('is-invalid');
                    mostrarNotificacion('Error', 'error', 'No se pueden seleccionar fechas pasadas');
                } else {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            });
        }
        
        if (horaInput) {
            horaInput.addEventListener('change', function() {
                const hora = this.value;
                const [horas, minutos] = hora.split(':').map(Number);
                
                // Validar horario de atención (9:00 - 18:00)
                if (horas < 9 || horas > 18 || (horas === 18 && minutos > 0)) {
                    this.classList.add('is-invalid');
                    mostrarNotificacion('Error', 'error', 'Horario fuera de atención (9:00 AM - 6:00 PM)');
                } else {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            });
        }
    });
    
    // Ejecutar búsqueda inicial
    if (document.getElementById('cuerpo-tabla-reservas')) {
        buscarReservas();
    }
    
    // Inicializar validación en tiempo real para checkboxes de servicios
    const serviciosCheckboxes = document.querySelectorAll('.servicio-checkbox');
    serviciosCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const serviciosSeleccionados = document.querySelectorAll('.servicio-checkbox:checked');
            const errorElement = document.getElementById('servicios-error');
            
            if (serviciosSeleccionados.length === 0) {
                errorElement.style.display = 'block';
            } else {
                errorElement.style.display = 'none';
            }
        });
    });
});