// static/js/reservas.js - CRUD completo para reservas

// Variables globales
let reservaCambioEstado = { id: null, estado: null };
let paginaActual = 1;
const registrosPorPagina = 10;

// ================= FUNCIONES PRINCIPALES =================

function buscarReservas() {
    const busqueda = document.getElementById('buscador-reservas')?.value.toLowerCase() || '';
    const filtroEstado = document.getElementById('filtro-estado')?.value || '';
    const filtroFecha = document.getElementById('filtro-fecha')?.value || '';
    const filas = document.querySelectorAll('#cuerpo-tabla-reservas .reserva-fila');
    
    let encontrados = 0, hoy = 0, pendientes = 0, completadas = 0;
    const fechaHoy = new Date().toISOString().split('T')[0];
    
    filas.forEach(fila => {
        if (fila.id === 'sin-resultados') return;
        
        const codigo = fila.getAttribute('data-codigo') || '';
        const mascota = fila.getAttribute('data-mascota') || '';
        const cliente = fila.getAttribute('data-cliente') || '';
        const estado = fila.getAttribute('data-estado') || '';
        const fecha = fila.getAttribute('data-fecha') || '';
        
        // Aplicar filtros
        const pasaFiltroEstado = !filtroEstado || estado === filtroEstado;
        const pasaFiltroFecha = !filtroFecha || fecha === filtroFecha;
        const pasaBusqueda = !busqueda || codigo.includes(busqueda) || 
                              mascota.includes(busqueda) || cliente.includes(busqueda);
        
        // Mostrar/ocultar fila
        if (pasaFiltroEstado && pasaFiltroFecha && pasaBusqueda) {
            fila.style.display = '';
            encontrados++;
            
            // Contar estadísticas
            if (estado === 'pendiente') pendientes++;
            if (estado === 'completada') completadas++;
            if (fecha === fechaHoy) hoy++;
        } else {
            fila.style.display = 'none';
        }
    });
    
    // Actualizar contadores
    updateCounter('total-reservas', encontrados);
    updateCounter('total-hoy', hoy);
    updateCounter('total-pendientes', pendientes);
    updateCounter('total-completadas', completadas);
    
    // Manejar resultados
    manejarSinResultados(encontrados, filas.length);
    // configurarPaginacion();
}

function mostrarModalCambioEstado(reservaId, codigoReserva, nuevoEstado) {
    reservaCambioEstado = { id: reservaId, estado: nuevoEstado };
    
    const estadoTextos = {
        'pendiente': 'Pendiente',
        'confirmada': 'Confirmada',
        'en_proceso': 'En Proceso',
        'completada': 'Completada',
        'cancelada': 'Cancelada',
        'no_show': 'No Show'
    };
    
    document.getElementById('codigo-reserva-cambio').textContent = codigoReserva;
    document.getElementById('nuevo-estado-texto').textContent = estadoTextos[nuevoEstado] || nuevoEstado;
    
    const mensajeConfirmacion = document.getElementById('mensaje-confirmacion');
    mensajeConfirmacion.innerHTML = nuevoEstado === 'cancelada' ? 
        '<div class="alert alert-warning"><i class="fas fa-exclamation-triangle me-2"></i><strong>Atención:</strong> Esta acción enviará una notificación al cliente.</div>' :
        '<p class="text-muted">Esta acción actualizará el estado de la reserva en el sistema.</p>';
    
    const modal = new bootstrap.Modal(document.getElementById('modal-cambio-estado'));
    modal.show();
}

function cambiarEstadoReserva() {
    if (!reservaCambioEstado.id || !reservaCambioEstado.estado) {
        mostrarNotificacion('Error', 'error', 'Datos de reserva no válidos');
        return;
    }
    
    fetch(`/reservas/cambiar-estado/${reservaCambioEstado.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ estado: reservaCambioEstado.estado })
    })
    .then(response => response.ok ? response.json() : Promise.reject('Error'))
    .then(data => {
        if (data.success) {
            mostrarNotificacion('Éxito', 'success', data.message);
            bootstrap.Modal.getInstance(document.getElementById('modal-cambio-estado')).hide();
            setTimeout(() => window.location.reload(), 1500);
        } else {
            mostrarNotificacion('Error', 'error', data.message);
        }
    })
    .catch(() => mostrarNotificacion('Error', 'error', 'Error al cambiar el estado'));
}

// ================= FUNCIONES PARA VALIDACIÓN DE NUEVA RESERVA =================

// Validar formulario completo de nueva reserva
function validarFormularioReserva() {
    let valido = true;
    
    // Validar mascota (sigue siendo obligatorio)
    const mascotaSelect = document.getElementById('id_mascota');
    if (!mascotaSelect || !mascotaSelect.value) {
        mostrarErrorCampo(mascotaSelect, 'Debes seleccionar una mascota');
        valido = false;
    } else {
        limpiarErrorCampo(mascotaSelect);
    }
    
    // NOTA: Empleado ahora es opcional, se remueve esta validación
    
    // Validar fecha
    const fechaInput = document.getElementById('fecha_reserva');
    if (!fechaInput || !fechaInput.value) {
        mostrarErrorCampo(fechaInput, 'La fecha es obligatoria');
        valido = false;
    } else {
        limpiarErrorCampo(fechaInput);
    }
    
    // Validar hora
    const horaInput = document.getElementById('hora_reserva');
    if (!horaInput || !horaInput.value) {
        mostrarErrorCampo(horaInput, 'La hora es obligatoria');
        valido = false;
    } else {
        limpiarErrorCampo(horaInput);
    }
    
    // Validar servicios
    const serviciosValidos = validarServicios();
    if (!serviciosValidos) {
        valido = false;
    }
    
    return valido;
}

// Validar que se haya seleccionado al menos un servicio
function validarServicios() {
    const checkboxes = document.querySelectorAll('.servicio-checkbox');
    if (checkboxes.length === 0) return true; // Si no hay checkboxes, no validar
    
    const seleccionados = Array.from(checkboxes).filter(cb => cb.checked);
    const errorElement = document.getElementById('servicios-error');
    
    if (seleccionados.length === 0) {
        if (errorElement) {
            errorElement.style.display = 'block';
        }
        return false;
    } else {
        if (errorElement) {
            errorElement.style.display = 'none';
        }
        return true;
    }
}

// Validar disponibilidad del empleado
function validarDisponibilidad() {
    const fecha = document.getElementById('fecha_reserva')?.value;
    const hora = document.getElementById('hora_reserva')?.value;
    const empleadoId = document.getElementById('id_empleado')?.value;
    const infoElement = document.getElementById('info-disponibilidad');
    
    if (!infoElement) return;
    
    if (!empleadoId || !fecha || !hora) {
        if (fecha && hora) {
            infoElement.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-check-circle me-2"></i>
                    <strong>Horario disponible</strong>
                    <div class="small">Completa los datos para ver disponibilidad</div>
                </div>
            `;
        } else {
            infoElement.innerHTML = '<p class="text-muted">Selecciona fecha y hora para ver disponibilidad</p>';
        }
        return;
    }
    
    // Mostrar carga
    infoElement.innerHTML = '<p class="text-info"><i class="fas fa-spinner fa-spin me-1"></i>Verificando disponibilidad...</p>';
    
    fetch(`/api/empleado/${empleadoId}/disponibilidad?fecha=${fecha}&hora=${hora}`)
        .then(response => response.json())
        .then(data => {
            if (data.disponible) {
                let mensajeExtra = '';
                if (data.mensaje && data.mensaje.includes('Administrador')) {
                    mensajeExtra = '<div class="small mt-1"><i class="fas fa-user-shield me-1"></i>Permite múltiples reservas simultáneas</div>';
                }
                
                infoElement.innerHTML = `
                    <div class="alert alert-success">
                        <i class="fas fa-check-circle me-2"></i>
                        <strong>${data.mensaje || 'Empleado disponible'}</strong>
                        ${mensajeExtra}
                    </div>
                `;
            } else {
                infoElement.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        <strong>Empleado no disponible</strong>
                        <div class="small">${data.mensaje || 'Ya tiene una reserva en este horario'}</div>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            infoElement.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    <strong>Error al verificar disponibilidad</strong>
                </div>
            `;
        });
}

// Funciones auxiliares para manejo de errores
function mostrarErrorCampo(elemento, mensaje) {
    if (!elemento) return;
    
    elemento.classList.add('is-invalid');
    const errorElement = document.getElementById(`${elemento.id}-error`);
    if (errorElement) {
        errorElement.textContent = mensaje;
        errorElement.style.display = 'block';
    }
}

function limpiarErrorCampo(elemento) {
    if (!elemento) return;
    
    elemento.classList.remove('is-invalid');
    const errorElement = document.getElementById(`${elemento.id}-error`);
    if (errorElement) {
        errorElement.style.display = 'none';
    }
}

// ================= PAGINACIÓN =================

/*function configurarPaginacion() {
    const filasVisibles = Array.from(document.querySelectorAll('.reserva-fila'))
        .filter(fila => fila.style.display !== 'none' && fila.id !== 'sin-resultados-filtro');
    
    const totalFilas = filasVisibles.length;
    const paginacionContainer = document.getElementById('paginacion-reservas')?.parentElement?.parentElement;
    
    if (!paginacionContainer) return;
    
    if (totalFilas <= registrosPorPagina) {
        paginacionContainer.classList.add('d-none');
        mostrarTodasLasFilas(filasVisibles);
        return;
    }
    
    paginacionContainer.classList.remove('d-none');
    const totalPaginas = Math.ceil(totalFilas / registrosPorPagina);
    const paginacion = document.getElementById('paginacion-reservas');
    
    if (!paginacion) return;
    
    paginacion.innerHTML = `
        <li class="page-item"><a class="page-link" href="#" id="pagina-anterior">&laquo;</a></li>
        ${Array.from({length: totalPaginas}, (_, i) => i + 1).map(pagina => `
            <li class="page-item ${pagina === paginaActual ? 'active' : ''}">
                <a class="page-link" href="#" data-pagina="${pagina}">${pagina}</a>
            </li>
        `).join('')}
        <li class="page-item"><a class="page-link" href="#" id="pagina-siguiente">&raquo;</a></li>
    `;
    
    mostrarPagina(paginaActual, filasVisibles);
}

function mostrarPagina(pagina, filasVisibles) {
    const inicio = (pagina - 1) * registrosPorPagina;
    const fin = Math.min(inicio + registrosPorPagina, filasVisibles.length);
    
    // Ocultar todas
    document.querySelectorAll('.reserva-fila').forEach(fila => {
        if (fila.id !== 'sin-resultados-filtro') fila.style.display = 'none';
    });
    
    // Mostrar página actual
    for (let i = inicio; i < fin && i < filasVisibles.length; i++) {
        filasVisibles[i].style.display = '';
    }
    
    // Actualizar texto
    const registrosMostrados = document.getElementById('registros-mostrados');
    const totalFiltradas = document.getElementById('total-filtradas');
    if (registrosMostrados) registrosMostrados.textContent = `${inicio + 1}-${fin}`;
    if (totalFiltradas) totalFiltradas.textContent = filasVisibles.length;
}

function cambiarPagina(pagina) {
    const filasVisibles = Array.from(document.querySelectorAll('.reserva-fila'))
        .filter(fila => fila.style.display !== 'none' && fila.id !== 'sin-resultados-filtro');
    
    const totalPaginas = Math.ceil(filasVisibles.length / registrosPorPagina);
    if (pagina < 1) pagina = 1;
    if (pagina > totalPaginas) pagina = totalPaginas;
    
    paginaActual = pagina;
    mostrarPagina(pagina, filasVisibles);
    
    // Actualizar botones activos
    document.querySelectorAll('.page-item').forEach(item => item.classList.remove('active'));
    document.querySelectorAll(`.page-link[data-pagina="${pagina}"]`).forEach(boton => {
        boton.parentElement.classList.add('active');
    });
}

function mostrarTodasLasFilas(filasVisibles) {
    filasVisibles.forEach(fila => fila.style.display = '');
    const registrosMostrados = document.getElementById('registros-mostrados');
    if (registrosMostrados) registrosMostrados.textContent = `1-${filasVisibles.length}`;
}
*/
// ================= UTILIDADES =================

function manejarSinResultados(encontrados, totalFilas) {
    const cuerpoTabla = document.getElementById('cuerpo-tabla-reservas');
    let mensaje = document.getElementById('sin-resultados-filtro');
    
    if (encontrados === 0 && totalFilas > 0) {
        if (!mensaje) {
            mensaje = document.createElement('tr');
            mensaje.id = 'sin-resultados-filtro';
            mensaje.innerHTML = `
                <td colspan="8" class="text-center py-5">
                    <div class="py-4">
                        <i class="fas fa-search fa-3x text-muted mb-3"></i>
                        <h5 class="text-muted mb-3">No se encontraron reservas</h5>
                        <button class="btn btn-outline-primary" id="btn-limpiar-filtros">
                            <i class="fas fa-times me-1"></i>Limpiar filtros
                        </button>
                    </div>
                </td>
            `;
            cuerpoTabla.appendChild(mensaje);
            
            document.getElementById('btn-limpiar-filtros').addEventListener('click', () => {
                document.getElementById('buscador-reservas').value = '';
                document.getElementById('filtro-estado').value = '';
                document.getElementById('filtro-fecha').value = '';
                buscarReservas();
            });
        }
    } else if (mensaje) {
        mensaje.remove();
    }
}

function updateCounter(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
}

function mostrarNotificacion(titulo, tipo, mensajes) {
    // Eliminar notificaciones previas
    document.querySelectorAll('.notificacion-personalizada').forEach(n => n.remove());
    
    const tipos = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };
    
    const alerta = document.createElement('div');
    alerta.className = `alert ${tipos[tipo]} alert-dismissible fade show notificacion-personalizada`;
    alerta.style.cssText = 'position:fixed; top:80px; right:20px; z-index:1050; min-width:300px; max-width:400px';
    
    let contenido = `<strong>${titulo}</strong>`;
    if (Array.isArray(mensajes)) {
        contenido += '<ul class="mb-0 mt-2" style="padding-left:20px;">' + 
                    mensajes.map(m => `<li style="margin-bottom:5px;">${m}</li>`).join('') + 
                    '</ul>';
    } else {
        contenido += `<p class="mb-0 mt-2">${mensajes}</p>`;
    }
    
    alerta.innerHTML = `${contenido}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    document.body.appendChild(alerta);
    
    setTimeout(() => alerta.parentNode && alerta.remove(), tipo === 'error' ? 8000 : 5000);
}

function inicializarTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => 
        new bootstrap.Tooltip(tooltipTriggerEl, { container: 'body' })
    );
}

// ================= INICIALIZACIÓN =================

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips
    inicializarTooltips();
    
    // Eventos de búsqueda
    ['input', 'change'].forEach(evento => {
        ['buscador-reservas', 'filtro-estado', 'filtro-fecha'].forEach(id => {
            document.getElementById(id)?.addEventListener(evento, buscarReservas);
        });
    });
    
    // Botón limpiar búsqueda
    document.getElementById('btn-limpiar-busqueda')?.addEventListener('click', () => {
        document.getElementById('buscador-reservas').value = '';
        buscarReservas();
    });
    
    // Botones de filtros rápidos
    document.querySelectorAll('[data-filtro]').forEach(boton => {
        boton.addEventListener('click', function(e) {
            e.preventDefault();
            const filtro = this.getAttribute('data-filtro');
            const hoy = new Date();
            
            if (filtro === 'hoy') {
                document.getElementById('filtro-fecha').value = hoy.toISOString().split('T')[0];
            } else if (filtro === 'pendientes') {
                document.getElementById('filtro-estado').value = 'pendiente';
            } else if (filtro === 'completadas') {
                document.getElementById('filtro-estado').value = 'completada';
            }
            
            buscarReservas();
        });
    });
    
    // Botón resetear filtros
    document.getElementById('btn-reset-filtros')?.addEventListener('click', () => {
        ['buscador-reservas', 'filtro-estado', 'filtro-fecha'].forEach(id => {
            document.getElementById(id).value = '';
        });
        buscarReservas();
    });
    
    // Botón limpiar todos los filtros
    document.getElementById('btn-limpiar-todo-filtros')?.addEventListener('click', function(e) {
        e.preventDefault();
        ['buscador-reservas', 'filtro-estado', 'filtro-fecha'].forEach(id => {
            document.getElementById(id).value = '';
        });
        buscarReservas();
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
    document.getElementById('btn-confirmar-cambio')?.addEventListener('click', cambiarEstadoReserva);
    
    // Paginación - eventos delegados
    /*
    document.addEventListener('click', function(e) {
        if (e.target.closest('#pagina-anterior')) {
            e.preventDefault();
            if (paginaActual > 1) cambiarPagina(paginaActual - 1);
        } else if (e.target.closest('#pagina-siguiente')) {
            e.preventDefault();
            const filasVisibles = Array.from(document.querySelectorAll('.reserva-fila'))
                .filter(fila => fila.style.display !== 'none' && fila.id !== 'sin-resultados-filtro');
            const totalPaginas = Math.ceil(filasVisibles.length / registrosPorPagina);
            if (paginaActual < totalPaginas) cambiarPagina(paginaActual + 1);
        } else if (e.target.closest('.page-link[data-pagina]')) {
            e.preventDefault();
            const pagina = parseInt(e.target.closest('.page-link[data-pagina]').getAttribute('data-pagina'));
            cambiarPagina(pagina);
        }
    }); */
    
    // ================= VALIDACIÓN DE FORMULARIO DE NUEVA RESERVA =================
    const formCrearReserva = document.getElementById('form-crear-reserva');
    if (formCrearReserva) {
        // Validación en tiempo real
        formCrearReserva.addEventListener('submit', function(e) {
            if (!validarFormularioReserva()) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
        
        // Validar disponibilidad cuando cambia fecha/hora/empleado
        const fechaInput = document.getElementById('fecha_reserva');
        const horaInput = document.getElementById('hora_reserva');
        const empleadoSelect = document.getElementById('id_empleado');
        
        if (fechaInput && horaInput) {
            fechaInput.addEventListener('change', validarDisponibilidad);
            horaInput.addEventListener('change', validarDisponibilidad);
        }
        
        if (empleadoSelect) {
            empleadoSelect.addEventListener('change', validarDisponibilidad);
        }
        
        // Validación de servicios
        const checkboxes = document.querySelectorAll('.servicio-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', validarServicios);
        });
        
        // Inicializar validación
        validarServicios();
        
        // Inicializar validación de disponibilidad si hay valores por defecto
        if (fechaInput && fechaInput.value && horaInput && horaInput.value) {
            setTimeout(validarDisponibilidad, 500);
        }
    }
    
    // Ejecutar búsqueda inicial en tabla de reservas
    if (document.getElementById('cuerpo-tabla-reservas')) {
        buscarReservas();
    }
});
// Función para mostrar mensajes en el calendario
function mostrarMensajeCalendario(mensaje) {
    const calendarEl = document.getElementById('calendario-reservas');
    if (calendarEl) {
        // Crear elemento de mensaje
        const mensajeDiv = document.createElement('div');
        mensajeDiv.className = 'alert alert-info mt-3';
        mensajeDiv.innerHTML = `
            <i class="fas fa-info-circle me-2"></i>
            ${mensaje}
            <button class="btn btn-sm btn-outline-primary ms-3" onclick="inicializarCalendario()">
                <i class="fas fa-redo me-1"></i> Reintentar
            </button>
        `;
        
        // Insertar después del calendario
        calendarEl.parentNode.insertBefore(mensajeDiv, calendarEl.nextSibling);
    }
}