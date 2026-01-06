// static/js/clientes.js - Versión completa corregida

// Variables globales
let clienteAEliminar = null;

// Función para validar email
function validarEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Función para buscar clientes
function buscarClientes() {
    const busqueda = document.getElementById('buscador-clientes')?.value.toLowerCase() || '';
    const filtro = document.getElementById('filtro-estado')?.value || 'todos';
    const filas = document.querySelectorAll('#cuerpo-tabla-clientes tr');
    let encontrados = 0;
    
    filas.forEach(fila => {
        if (fila.id === 'sin-resultados') return;
        
        const dni = fila.getAttribute('data-dni') || '';
        const nombre = fila.getAttribute('data-nombre') || '';
        const apellido = fila.getAttribute('data-apellido') || '';
        const telefono = fila.getAttribute('data-telefono') || '';
        const email = fila.getAttribute('data-email') || '';
        
        // Aplicar filtro de DNI
        let pasaFiltro = true;
        if (filtro === 'con-dni' && !dni) pasaFiltro = false;
        if (filtro === 'sin-dni' && dni) pasaFiltro = false;
        
        // Aplicar búsqueda
        let pasaBusqueda = true;
        if (busqueda) {
            pasaBusqueda = nombre.includes(busqueda) || 
                          apellido.includes(busqueda) || 
                          telefono.includes(busqueda) || 
                          email.includes(busqueda) ||
                          dni.includes(busqueda);
        }
        
        // Mostrar/ocultar fila
        if (pasaFiltro && pasaBusqueda) {
            fila.style.display = '';
            encontrados++;
        } else {
            fila.style.display = 'none';
        }
    });
    
    // Actualizar contador
    const totalElement = document.getElementById('total-clientes');
    if (totalElement) {
        totalElement.textContent = encontrados;
    }
    
    // Mostrar mensaje si no hay resultados
    const cuerpoTabla = document.getElementById('cuerpo-tabla-clientes');
    if (encontrados === 0 && filas.length > 0) {
        if (!document.getElementById('sin-resultados')) {
            const mensaje = document.createElement('tr');
            mensaje.id = 'sin-resultados';
            mensaje.innerHTML = `
                <td colspan="8" class="text-center py-4">
                    <i class="fas fa-search fa-2x text-muted mb-3"></i>
                    <p class="text-muted">No se encontraron clientes con los criterios de búsqueda</p>
                    <button class="btn btn-sm btn-outline-secondary" id="btn-limpiar-filtros">
                        <i class="fas fa-times me-1"></i>Limpiar filtros
                    </button>
                </td>
            `;
            cuerpoTabla.appendChild(mensaje);
            
            // Agregar evento al botón de limpiar
            document.getElementById('btn-limpiar-filtros').addEventListener('click', function() {
                if (document.getElementById('buscador-clientes')) {
                    document.getElementById('buscador-clientes').value = '';
                }
                if (document.getElementById('filtro-estado')) {
                    document.getElementById('filtro-estado').value = 'todos';
                }
                buscarClientes();
            });
        }
    } else {
        const mensaje = document.getElementById('sin-resultados');
        if (mensaje) mensaje.remove();
    }
}

// Función para mostrar modal de confirmación
function mostrarModalEliminacion(clienteId, nombreCliente) {
    clienteAEliminar = clienteId;
    const nombreElement = document.getElementById('nombre-cliente-eliminar');
    if (nombreElement) {
        nombreElement.textContent = nombreCliente;
    }
    
    const modalElement = document.getElementById('modal-confirmar-eliminacion');
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        
        // Resetear checkbox
        const checkbox = document.getElementById('confirmar-eliminacion');
        const btnConfirmar = document.getElementById('btn-confirmar-eliminacion');
        
        if (checkbox && btnConfirmar) {
            checkbox.checked = false;
            btnConfirmar.disabled = true;
        }
    }
}

// Función mejorada para validar campo individual
function validarCampoIndividual(campo) {
    const valor = campo.value.trim();
    
    // Agregar clase para identificar que es validado por JS
    campo.classList.add('js-validated');
    
    // Remover estados previos
    campo.classList.remove('is-invalid', 'is-valid');
    const errorId = campo.id + '-error';
    document.getElementById(errorId)?.remove();
    
    // Si está vacío y no es requerido, está bien
    if (!valor && !campo.hasAttribute('required')) {
        return true;
    }
    
    let valido = true;
    let mensajeError = '';
    
    switch(campo.id) {
        case 'dni':
            if (valor) {
                if (!/^\d{8}$/.test(valor) && !/^\d{9}$/.test(valor)) {
                    valido = false;
                    mensajeError = 'DNI debe tener 8 dígitos o Carnet de Extranjería 9 dígitos';
                }
            }
            break;
            
        case 'telefono':
            if (!valor) {
                valido = false;
                mensajeError = 'El teléfono es obligatorio';
            } else if (!/^9\d{8}$/.test(valor.replace(/\D/g, ''))) {
                valido = false;
                mensajeError = 'Teléfono peruano: 9 dígitos, empezando con 9';
            }
            break;
            
        case 'email':
            if (valor && !validarEmail(valor)) {
                valido = false;
                mensajeError = 'Por favor ingresa un email válido';
            }
            break;
            
        case 'nombre':
            if (!valor) {
                valido = false;
                mensajeError = 'El nombre es obligatorio';
            } else if (!/^[A-Za-zÁÉÍÓÚáéíóúñÑ\s]{2,50}$/.test(valor)) {
                valido = false;
                mensajeError = 'Solo letras (2-50 caracteres)';
            }
            break;
            
        case 'apellido':
            if (!valor) {
                valido = false;
                mensajeError = 'El apellido es obligatorio';
            } else if (!/^[A-Za-zÁÉÍÓÚáéíóúñÑ\s]{2,50}$/.test(valor)) {
                valido = false;
                mensajeError = 'Solo letras (2-50 caracteres)';
            }
            break;
    }
    
    // Actualizar estado visual
    if (valido && valor) {
        campo.classList.add('is-valid');
    } else if (!valido) {
        campo.classList.add('is-invalid');
        // Mostrar mensaje de error
        const errorDiv = document.createElement('div');
        errorDiv.id = errorId;
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = mensajeError;
        campo.parentNode.appendChild(errorDiv);
    }
    
    return valido;
}

// Función para validar formulario de cliente
function validarFormularioCliente(event) {
    event.preventDefault();
    
    const form = event.target;
    const campos = form.querySelectorAll('input[required], input#dni, input#email');
    let errores = [];
    let valido = true;
    
    // Validar todos los campos
    campos.forEach(campo => {
        if (!validarCampoIndividual(campo)) {
            valido = false;
            const errorId = campo.id + '-error';
            const errorElement = document.getElementById(errorId);
            if (errorElement) {
                errores.push(errorElement.textContent);
            }
        }
    });
    
    // Mostrar errores si los hay
    if (!valido) {
        mostrarNotificacionPersonalizada('Corrige los siguientes errores:', 'error', errores);
        // Enfocar el primer campo con error
        const primerError = form.querySelector('.is-invalid');
        if (primerError) {
            primerError.focus();
        }
        return false;
    }
    
    // Si todo está bien, enviar el formulario
    form.submit();
    return true;
}

// Función mejorada para mostrar notificaciones
function mostrarNotificacionPersonalizada(titulo, tipo, mensajes) {
    // Eliminar notificaciones previas
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
        const mensajesUnicos = [...new Set(mensajes)]; // Remover duplicados
        mensajesUnicos.forEach(mensaje => {
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
    
    // Auto-remover después de 8 segundos para errores, 5 para éxito
    setTimeout(() => {
        if (alerta.parentNode) {
            alerta.remove();
        }
    }, tipo === 'error' ? 8000 : 5000);
}

// Función para exportar clientes
function exportarClientes() {
    mostrarNotificacionPersonalizada('Exportación', 'info', 'La función de exportación estará disponible próximamente.');
}

// Función para eliminar cliente (llamada desde el modal)
function eliminarCliente(clienteId) {
    if (!clienteId || clienteId <= 0) {
        mostrarNotificacionPersonalizada('Error', 'error', 'ID de cliente no válido');
        return;
    }
    
    fetch(`/clientes/eliminar/${clienteId}`, {
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
            // Recargar la página después de 1.5 segundos
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            mostrarNotificacionPersonalizada('Error', 'error', data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarNotificacionPersonalizada('Error', 'error', 'Error al eliminar el cliente');
    });
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('Clientes JS cargado correctamente');
    
    // Inicializar buscador (solo si existe en la página)
    const buscador = document.getElementById('buscador-clientes');
    const filtroEstado = document.getElementById('filtro-estado');
    const btnLimpiar = document.getElementById('btn-limpiar-busqueda');
    
    if (buscador) {
        buscador.addEventListener('input', buscarClientes);
        buscador.addEventListener('keyup', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                buscarClientes();
            }
        });
    }
    
    if (filtroEstado) {
        filtroEstado.addEventListener('change', buscarClientes);
    }
    
    if (btnLimpiar) {
        btnLimpiar.addEventListener('click', function() {
            if (buscador) {
                buscador.value = '';
                buscarClientes();
            }
        });
    }
    
    // Agregar eventos a botones de eliminar
    document.querySelectorAll('.eliminar-cliente').forEach(boton => {
        boton.addEventListener('click', function() {
            const clienteId = this.getAttribute('data-id');
            const nombreCliente = this.getAttribute('data-nombre');
            mostrarModalEliminacion(clienteId, nombreCliente);
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
            if (clienteAEliminar) {
                eliminarCliente(clienteAEliminar);
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
    
    // Evento para botón de exportar
    const btnExportar = document.getElementById('btn-exportar');
    if (btnExportar) {
        btnExportar.addEventListener('click', exportarClientes);
    }
    
    // Inicializar validación en tiempo real para formularios
    const forms = document.querySelectorAll('form[action*="cliente"]');
    forms.forEach(form => {
        // Validación en tiempo real
        const campos = form.querySelectorAll('input[required], input#dni, input#email');
        campos.forEach(campo => {
            // Validar al salir del campo
            campo.addEventListener('blur', function() {
                validarCampoIndividual(this);
            });
            
            // Limpiar validación al escribir
            campo.addEventListener('input', function() {
                this.classList.remove('is-invalid', 'is-valid');
                const errorId = this.id + '-error';
                document.getElementById(errorId)?.remove();
            });
        });
        
        // Validar formulario al enviar
        form.addEventListener('submit', validarFormularioCliente);
    });
    
    // Ejecutar búsqueda inicial para aplicar filtros si los hay
    if (document.getElementById('cuerpo-tabla-clientes')) {
        buscarClientes();
    }
});