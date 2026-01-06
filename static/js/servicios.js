// static/js/servicios.js - CRUD completo para servicios

// Variables globales
let servicioAEliminar = null;

// Función para buscar servicios
function buscarServicios() {
    const busqueda = document.getElementById('buscador-servicios')?.value.toLowerCase() || '';
    const filtroCategoria = document.getElementById('filtro-categoria')?.value || '';
    const filas = document.querySelectorAll('#cuerpo-tabla-servicios tr');
    let encontrados = 0;
    
    filas.forEach(fila => {
        if (fila.id === 'sin-resultados') return;
        
        const nombre = fila.getAttribute('data-nombre') || '';
        const codigo = fila.getAttribute('data-codigo') || '';
        const categoria = fila.getAttribute('data-categoria') || '';
        
        // Aplicar filtros
        let pasaFiltroCategoria = true;
        if (filtroCategoria && categoria !== filtroCategoria) {
            pasaFiltroCategoria = false;
        }
        
        // Aplicar búsqueda
        let pasaBusqueda = true;
        if (busqueda) {
            pasaBusqueda = nombre.includes(busqueda) || codigo.includes(busqueda);
        }
        
        // Mostrar/ocultar fila
        if (pasaFiltroCategoria && pasaBusqueda) {
            fila.style.display = '';
            encontrados++;
        } else {
            fila.style.display = 'none';
        }
    });
    
    // Actualizar contador
    const totalElement = document.getElementById('total-servicios');
    if (totalElement) {
        totalElement.textContent = encontrados;
    }
    
    // Mostrar mensaje si no hay resultados
    const cuerpoTabla = document.getElementById('cuerpo-tabla-servicios');
    if (encontrados === 0 && filas.length > 0) {
        if (!document.getElementById('sin-resultados')) {
            const mensaje = document.createElement('tr');
            mensaje.id = 'sin-resultados';
            mensaje.innerHTML = `
                <td colspan="8" class="text-center py-4">
                    <i class="fas fa-search fa-2x text-muted mb-3"></i>
                    <p class="text-muted">No se encontraron servicios con los criterios de búsqueda</p>
                    <button class="btn btn-sm btn-outline-secondary" id="btn-limpiar-filtros">
                        <i class="fas fa-times me-1"></i>Limpiar filtros
                    </button>
                </td>
            `;
            cuerpoTabla.appendChild(mensaje);
            
            document.getElementById('btn-limpiar-filtros').addEventListener('click', function() {
                document.getElementById('buscador-servicios').value = '';
                document.getElementById('filtro-categoria').value = '';
                buscarServicios();
            });
        }
    } else {
        const mensaje = document.getElementById('sin-resultados');
        if (mensaje) mensaje.remove();
    }
}

// Función para mostrar modal de confirmación
function mostrarModalEliminacion(servicioId, nombreServicio) {
    servicioAEliminar = servicioId;
    const nombreElement = document.getElementById('nombre-servicio-eliminar');
    if (nombreElement) {
        nombreElement.textContent = nombreServicio;
    }
    
    const modalElement = document.getElementById('modal-confirmar-eliminacion');
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        
        const checkbox = document.getElementById('confirmar-eliminacion');
        const btnConfirmar = document.getElementById('btn-confirmar-eliminacion');
        
        if (checkbox && btnConfirmar) {
            checkbox.checked = false;
            btnConfirmar.disabled = true;
        }
    }
}

// Función para validar formulario de servicio
function validarFormularioServicio() {
    const form = event.target;
    const codigo = form.querySelector('#codigo');
    const nombre = form.querySelector('#nombre');
    const categoria = form.querySelector('#categoria');
    const duracion = form.querySelector('#duracion_min');
    const costo = form.querySelector('#costo');
    const precio = form.querySelector('#precio');
    let errores = [];
    
    // Validar código
    if (!codigo.value.trim()) {
        errores.push('El código es obligatorio');
        codigo.classList.add('is-invalid');
    } else if (codigo.value.trim().length < 3) {
        errores.push('El código debe tener al menos 3 caracteres');
        codigo.classList.add('is-invalid');
    } else {
        codigo.classList.remove('is-invalid');
        codigo.classList.add('is-valid');
    }
    
    // Validar nombre
    if (!nombre.value.trim()) {
        errores.push('El nombre es obligatorio');
        nombre.classList.add('is-invalid');
    } else if (nombre.value.trim().length < 3) {
        errores.push('El nombre debe tener al menos 3 caracteres');
        nombre.classList.add('is-invalid');
    } else {
        nombre.classList.remove('is-invalid');
        nombre.classList.add('is-valid');
    }
    
    // Validar categoría
    if (!categoria.value) {
        errores.push('Debes seleccionar una categoría');
        categoria.classList.add('is-invalid');
    } else {
        categoria.classList.remove('is-invalid');
        categoria.classList.add('is-valid');
    }
    
    // Validar duración
    const duracionValue = parseInt(duracion.value);
    if (!duracion.value || isNaN(duracionValue) || duracionValue < 15 || duracionValue > 300) {
        errores.push('La duración debe estar entre 15 y 300 minutos');
        duracion.classList.add('is-invalid');
    } else {
        duracion.classList.remove('is-invalid');
        duracion.classList.add('is-valid');
    }
    
    // Validar costo
    const costoValue = parseFloat(costo.value);
    if (!costo.value || isNaN(costoValue) || costoValue < 0) {
        errores.push('El costo debe ser un número mayor o igual a 0');
        costo.classList.add('is-invalid');
    } else {
        costo.classList.remove('is-invalid');
        costo.classList.add('is-valid');
    }
    
    // Validar precio
    const precioValue = parseFloat(precio.value);
    if (!precio.value || isNaN(precioValue) || precioValue <= 0) {
        errores.push('El precio debe ser un número mayor a 0');
        precio.classList.add('is-invalid');
    } else if (precioValue <= costoValue) {
        errores.push('El precio debe ser mayor al costo');
        precio.classList.add('is-invalid');
    } else {
        precio.classList.remove('is-invalid');
        precio.classList.add('is-valid');
    }
    
    // Mostrar errores si los hay
    if (errores.length > 0) {
        mostrarNotificacionPersonalizada('Corrige los siguientes errores:', 'error', errores);
        event.preventDefault();
        return false;
    }
    
    return true;
}

// Función para mostrar notificaciones
function mostrarNotificacionPersonalizada(titulo, tipo, mensajes) {
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

// Función para eliminar servicio
function eliminarServicio(servicioId) {
    if (!servicioId || servicioId <= 0) {
        mostrarNotificacionPersonalizada('Error', 'error', 'ID de servicio no válido');
        return;
    }
    
    fetch(`/servicios/eliminar/${servicioId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            mostrarNotificacionPersonalizada('Éxito', 'success', data.message);
            setTimeout(() => {
                window.location.href = '/servicios';
            }, 1500);
        } else {
            mostrarNotificacionPersonalizada('Error', 'error', data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarNotificacionPersonalizada('Error', 'error', 'Error al eliminar el servicio');
    });
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('Servicios JS cargado correctamente');
    
    // Inicializar buscador
    const buscador = document.getElementById('buscador-servicios');
    const filtroCategoria = document.getElementById('filtro-categoria');
    const btnLimpiar = document.getElementById('btn-limpiar-busqueda');
    
    if (buscador) {
        buscador.addEventListener('input', buscarServicios);
        buscador.addEventListener('keyup', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                buscarServicios();
            }
        });
    }
    
    if (filtroCategoria) {
        filtroCategoria.addEventListener('change', buscarServicios);
    }
    
    if (btnLimpiar) {
        btnLimpiar.addEventListener('click', function() {
            if (buscador) {
                buscador.value = '';
                buscarServicios();
            }
        });
    }
    
    // Agregar eventos a botones de eliminar
    document.querySelectorAll('.eliminar-servicio, .eliminar-servicio-detalle').forEach(boton => {
        boton.addEventListener('click', function() {
            const servicioId = this.getAttribute('data-id');
            const nombreServicio = this.getAttribute('data-nombre');
            mostrarModalEliminacion(servicioId, nombreServicio);
        });
    });
    
    // Evento para checkbox de confirmación
    const checkboxConfirmar = document.getElementById('confirmar-eliminacion');
    const btnConfirmar = document.getElementById('btn-confirmar-eliminacion');
    
    if (checkboxConfirmar && btnConfirmar) {
        checkboxConfirmar.addEventListener('change', function() {
            btnConfirmar.disabled = !this.checked;
        });
    }
    
    // Evento para botón de confirmar eliminación
    if (btnConfirmar) {
        btnConfirmar.addEventListener('click', function() {
            if (servicioAEliminar) {
                eliminarServicio(servicioAEliminar);
                const modalElement = document.getElementById('modal-confirmar-eliminacion');
                if (modalElement) {
                    const modal = bootstrap.Modal.getInstance(modalElement);
                    if (modal) {
                        modal.hide();
                    }
                }
            }
        });
    }
    
    // Agregar validación a formularios de servicio
    const forms = document.querySelectorAll('form[action*="servicio"]');
    forms.forEach(form => {
        form.addEventListener('submit', validarFormularioServicio);
        
        // Validación en tiempo real
        const campos = form.querySelectorAll('input[required], select[required]');
        campos.forEach(campo => {
            campo.addEventListener('blur', function() {
                if (this.value.trim()) {
                    validarCampoIndividual(this);
                }
            });
            
            campo.addEventListener('input', function() {
                this.classList.remove('is-invalid', 'is-valid');
                const errorId = this.id + '-error';
                document.getElementById(errorId)?.remove();
            });
        });
    });
    
    // Ejecutar búsqueda inicial
    if (document.getElementById('cuerpo-tabla-servicios')) {
        buscarServicios();
    }
});

// Función para validar campo individual
function validarCampoIndividual(campo) {
    const valor = campo.value.trim();
    
    switch(campo.id) {
        case 'codigo':
            if (!valor) {
                campo.classList.add('is-invalid');
                return false;
            } else if (valor.length < 3) {
                campo.classList.add('is-invalid');
                return false;
            }
            break;
            
        case 'nombre':
            if (!valor) {
                campo.classList.add('is-invalid');
                return false;
            } else if (valor.length < 3) {
                campo.classList.add('is-invalid');
                return false;
            }
            break;
            
        case 'categoria':
            if (!valor) {
                campo.classList.add('is-invalid');
                return false;
            }
            break;
            
        case 'duracion_min':
            const duracionValue = parseInt(valor);
            if (!valor || isNaN(duracionValue) || duracionValue < 15 || duracionValue > 300) {
                campo.classList.add('is-invalid');
                return false;
            }
            break;
            
        case 'costo':
            const costoValue = parseFloat(valor);
            if (!valor || isNaN(costoValue) || costoValue < 0) {
                campo.classList.add('is-invalid');
                return false;
            }
            break;
            
        case 'precio':
            const precioValue = parseFloat(valor);
            if (!valor || isNaN(precioValue) || precioValue <= 0) {
                campo.classList.add('is-invalid');
                return false;
            }
            break;
    }
    
    if (valor && !campo.classList.contains('is-invalid')) {
        campo.classList.add('is-valid');
    }
    
    return true;
}