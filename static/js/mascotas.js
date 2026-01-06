// static/js/mascotas.js - CRUD completo para mascotas

// Variables globales
let mascotaAEliminar = null;

// Función para buscar mascotas
function buscarMascotas() {
    const busqueda = document.getElementById('buscador-mascotas')?.value.toLowerCase() || '';
    const filtroEspecie = document.getElementById('filtro-especie')?.value || '';
    const filtroCliente = document.getElementById('filtro-cliente')?.value || '';
    const filas = document.querySelectorAll('#cuerpo-tabla-mascotas tr');
    let encontrados = 0;
    
    filas.forEach(fila => {
        if (fila.id === 'sin-resultados') return;
        
        const nombre = fila.getAttribute('data-nombre') || '';
        const especie = fila.getAttribute('data-especie') || '';
        const raza = fila.getAttribute('data-raza') || '';
        const tamano = fila.getAttribute('data-tamano') || '';
        const cliente = fila.getAttribute('data-cliente') || '';
        
        // Aplicar filtros
        let pasaFiltroEspecie = true;
        if (filtroEspecie && especie !== filtroEspecie) {
            pasaFiltroEspecie = false;
        }
        
        let pasaFiltroCliente = true;
        if (filtroCliente) {
            const idCliente = fila.querySelector('a[href*="ver_cliente"]')?.getAttribute('href')?.match(/\/ver\/(\d+)/)?.[1];
            if (idCliente !== filtroCliente) {
                pasaFiltroCliente = false;
            }
        }
        
        // Aplicar búsqueda
        let pasaBusqueda = true;
        if (busqueda) {
            pasaBusqueda = nombre.includes(busqueda) || 
                          raza.includes(busqueda) || 
                          cliente.includes(busqueda);
        }
        
        // Mostrar/ocultar fila
        if (pasaFiltroEspecie && pasaFiltroCliente && pasaBusqueda) {
            fila.style.display = '';
            encontrados++;
        } else {
            fila.style.display = 'none';
        }
    });
    
    // Actualizar contador
    const totalElement = document.getElementById('total-mascotas');
    if (totalElement) {
        totalElement.textContent = encontrados;
    }
    
    // Mostrar mensaje si no hay resultados
    const cuerpoTabla = document.getElementById('cuerpo-tabla-mascotas');
    if (encontrados === 0 && filas.length > 0) {
        if (!document.getElementById('sin-resultados')) {
            const mensaje = document.createElement('tr');
            mensaje.id = 'sin-resultados';
            mensaje.innerHTML = `
                <td colspan="8" class="text-center py-4">
                    <i class="fas fa-search fa-2x text-muted mb-3"></i>
                    <p class="text-muted">No se encontraron mascotas con los criterios de búsqueda</p>
                    <button class="btn btn-sm btn-outline-secondary" id="btn-limpiar-filtros">
                        <i class="fas fa-times me-1"></i>Limpiar filtros
                    </button>
                </td>
            `;
            cuerpoTabla.appendChild(mensaje);
            
            document.getElementById('btn-limpiar-filtros').addEventListener('click', function() {
                document.getElementById('buscador-mascotas').value = '';
                document.getElementById('filtro-especie').value = '';
                document.getElementById('filtro-cliente').value = '';
                buscarMascotas();
            });
        }
    } else {
        const mensaje = document.getElementById('sin-resultados');
        if (mensaje) mensaje.remove();
    }
}

// Función para mostrar modal de confirmación
function mostrarModalEliminacion(mascotaId, nombreMascota) {
    mascotaAEliminar = mascotaId;
    const nombreElement = document.getElementById('nombre-mascota-eliminar');
    if (nombreElement) {
        nombreElement.textContent = nombreMascota;
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

// Función para validar formulario de mascota
function validarFormularioMascota() {
    const form = event.target;
    const nombre = form.querySelector('#nombre');
    const idCliente = form.querySelector('#id_cliente');
    const especie = form.querySelector('#especie');
    const peso = form.querySelector('#peso');
    let errores = [];
    
    // Validar nombre
    if (!nombre.value.trim()) {
        errores.push('El nombre de la mascota es obligatorio');
        nombre.classList.add('is-invalid');
    } else if (nombre.value.trim().length < 2) {
        errores.push('El nombre debe tener al menos 2 caracteres');
        nombre.classList.add('is-invalid');
    } else {
        nombre.classList.remove('is-invalid');
        nombre.classList.add('is-valid');
    }
    
    // Validar dueño
    if (!idCliente.value) {
        errores.push('Debes seleccionar un dueño');
        idCliente.classList.add('is-invalid');
    } else {
        idCliente.classList.remove('is-invalid');
        idCliente.classList.add('is-valid');
    }
    
    // Validar especie
    if (!especie.value) {
        errores.push('Debes seleccionar una especie');
        especie.classList.add('is-invalid');
    } else {
        especie.classList.remove('is-invalid');
        especie.classList.add('is-valid');
    }
    
    // Validar peso (si tiene valor)
    if (peso && peso.value.trim()) {
        const pesoValue = parseFloat(peso.value);
        if (isNaN(pesoValue) || pesoValue <= 0 || pesoValue > 200) {
            errores.push('El peso debe ser un número entre 0.1 y 200 kg');
            peso.classList.add('is-invalid');
        } else {
            peso.classList.remove('is-invalid');
            peso.classList.add('is-valid');
        }
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

// Función para eliminar mascota
function eliminarMascota(mascotaId) {
    if (!mascotaId || mascotaId <= 0) {
        mostrarNotificacionPersonalizada('Error', 'error', 'ID de mascota no válido');
        return;
    }
    
    fetch(`/mascotas/eliminar/${mascotaId}`, {
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
                window.location.href = '/mascotas';
            }, 1500);
        } else {
            mostrarNotificacionPersonalizada('Error', 'error', data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarNotificacionPersonalizada('Error', 'error', 'Error al eliminar la mascota');
    });
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('Mascotas JS cargado correctamente');
    
    // Inicializar buscador
    const buscador = document.getElementById('buscador-mascotas');
    const filtroEspecie = document.getElementById('filtro-especie');
    const filtroCliente = document.getElementById('filtro-cliente');
    const btnLimpiar = document.getElementById('btn-limpiar-busqueda');
    
    if (buscador) {
        buscador.addEventListener('input', buscarMascotas);
        buscador.addEventListener('keyup', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                buscarMascotas();
            }
        });
    }
    
    if (filtroEspecie) {
        filtroEspecie.addEventListener('change', buscarMascotas);
    }
    
    if (filtroCliente) {
        filtroCliente.addEventListener('change', buscarMascotas);
    }
    
    if (btnLimpiar) {
        btnLimpiar.addEventListener('click', function() {
            if (buscador) {
                buscador.value = '';
                buscarMascotas();
            }
        });
    }
    
    // Agregar eventos a botones de eliminar
    document.querySelectorAll('.eliminar-mascota, .eliminar-mascota-detalle').forEach(boton => {
        boton.addEventListener('click', function() {
            const mascotaId = this.getAttribute('data-id');
            const nombreMascota = this.getAttribute('data-nombre');
            mostrarModalEliminacion(mascotaId, nombreMascota);
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
            if (mascotaAEliminar) {
                eliminarMascota(mascotaAEliminar);
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
    
    // Agregar validación a formularios de mascota
    const forms = document.querySelectorAll('form[action*="mascota"]');
    forms.forEach(form => {
        form.addEventListener('submit', validarFormularioMascota);
        
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
    if (document.getElementById('cuerpo-tabla-mascotas')) {
        buscarMascotas();
    }
});

// Función para validar campo individual
function validarCampoIndividual(campo) {
    const valor = campo.value.trim();
    
    switch(campo.id) {
        case 'nombre':
            if (!valor) {
                campo.classList.add('is-invalid');
                return false;
            } else if (valor.length < 2) {
                campo.classList.add('is-invalid');
                return false;
            }
            break;
            
        case 'id_cliente':
        case 'especie':
            if (!valor) {
                campo.classList.add('is-invalid');
                return false;
            }
            break;
            
        case 'peso':
            if (valor) {
                const pesoValue = parseFloat(valor);
                if (isNaN(pesoValue) || pesoValue <= 0 || pesoValue > 200) {
                    campo.classList.add('is-invalid');
                    return false;
                }
            }
            break;
    }
    
    if (valor && !campo.classList.contains('is-invalid')) {
        campo.classList.add('is-valid');
    }
    
    return true;
}