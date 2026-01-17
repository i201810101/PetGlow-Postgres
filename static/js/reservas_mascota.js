// static/js/reservas_mascota.js - Manejo de información de mascota en reservas

// ================= FUNCIONES PARA CARGAR DATOS DE MASCOTA =================

function cargarDatosMascota() {
    const idMascota = document.getElementById('id_mascota').value;
    
    if (!idMascota) {
        // Ocultar paneles si no hay mascota seleccionada
        document.getElementById('info-mascota-container')?.classList.add('d-none');
        document.getElementById('historial-cortes-container')?.classList.add('d-none');
        return;
    }
    
    // Mostrar indicador de carga
    const infoContainer = document.getElementById('info-mascota-container');
    const historialContainer = document.getElementById('historial-cortes-container');
    
    if (infoContainer) {
        infoContainer.classList.remove('d-none');
        // Mostrar loader
        document.querySelectorAll('.editable-field').forEach(el => {
            el.textContent = 'Cargando...';
        });
    }
    if (historialContainer) historialContainer.classList.remove('d-none');
    
    if (document.getElementById('mascota-raza')) {
        document.getElementById('mascota-raza').textContent = 'Cargando...';
    }
    if (document.getElementById('historial-cortes-content')) {
        document.getElementById('historial-cortes-content').innerHTML = '<p class="text-muted"><i class="fas fa-spinner fa-spin me-1"></i>Cargando historial...</p>';
    }
    
    // Llamar a la API para obtener datos de la mascota
    fetch(`/api/mascota/${idMascota}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const mascota = data.mascota;
                const historial = data.historial_cortes || [];
                
                console.log('Datos recibidos:', mascota); // Para debugging
                
                // Actualizar información básica
                actualizarInfoMascota(mascota);
                
                // Actualizar información del dueño
                actualizarInfoCliente(mascota);
                
                // Actualizar historial de cortes
                actualizarHistorialCortes(historial);
                
                // Llenar el modal con datos actuales
                llenarModalActualizacion(idMascota, mascota);
                
            } else {
                mostrarError(`Error del servidor: ${data.error || 'Error desconocido'}`);
            }
        })
        .catch(error => {
            console.error('Error en fetch:', error);
            
            // Mostrar error específico para problemas de conexión
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                mostrarError('Error de conexión. Verifica tu conexión a internet e intenta nuevamente.');
            } else {
                mostrarError('Error al cargar datos de la mascota. Verifica tu conexión.');
            }
            
            // Mostrar datos por defecto
            document.querySelectorAll('.editable-field').forEach(el => {
                if (el.textContent === 'Cargando...') {
                    el.textContent = 'Error al cargar';
                }
            });
        });
}

function actualizarInfoMascota(mascota) {
    console.log('Actualizando info mascota:', mascota); // Para debugging
    
    // Mapeo de campos - ajusta según tu base de datos
    const camposMascota = {
        'mascota-raza': mascota.raza || mascota.Raza || 'No especificado',
        'mascota-color': mascota.color || mascota.Color || 'No especificado',
        'mascota-corte': mascota.corte || mascota.tipo_corte || mascota.TipoCorte || 'No especificado',
        'mascota-tamano': (mascota.tamano || mascota.Tamano || 'No especificado').toLowerCase(),
        'mascota-peso': mascota.peso || mascota.Peso || 'No registrado',
        'mascota-caracteristicas': mascota.caracteristicas || mascota.Caracteristicas || 'Sin características registradas',
        'mascota-alergias': mascota.alergias || mascota.Alergias || 'Sin alergias registradas',
        'mascota-edad': calcularEdad(mascota)
    };
    
    // Actualizar cada elemento
    Object.keys(camposMascota).forEach(id => {
        const elemento = document.getElementById(id);
        if (elemento) {
            // Formatear tamaño
            let valor = camposMascota[id];
            if (id === 'mascota-tamano') {
                valor = valor.charAt(0).toUpperCase() + valor.slice(1);
            }
            
            // Formatear peso
            if (id === 'mascota-peso' && valor !== 'No registrado') {
                valor = `${valor} kg`;
            }
            
            elemento.textContent = valor;
        }
    });
}

function calcularEdad(mascota) {
    // Primero intentar con campos calculados
    if (mascota.edad_anios !== undefined && mascota.edad_meses !== undefined) {
        let texto = `${mascota.edad_anios} años`;
        if (mascota.edad_meses > 0) {
            texto += `, ${mascota.edad_meses} meses`;
        }
        return texto;
    }
    
    // Si no hay fecha de nacimiento
    if (!mascota.fecha_nacimiento) {
        return 'No registrada';
    }
    
    // Calcular a partir de fecha de nacimiento
    try {
        const nacimiento = new Date(mascota.fecha_nacimiento);
        const hoy = new Date();
        
        let años = hoy.getFullYear() - nacimiento.getFullYear();
        let meses = hoy.getMonth() - nacimiento.getMonth();
        
        if (meses < 0) {
            años--;
            meses += 12;
        }
        
        let texto = `${años} años`;
        if (meses > 0) {
            texto += `, ${meses} meses`;
        }
        
        return texto;
    } catch (e) {
        console.error('Error calculando edad:', e);
        return 'No registrada';
    }
}

function actualizarInfoCliente(mascota) {
    console.log('Actualizando info cliente:', mascota); // Para debugging
    
    const clienteNombre = document.getElementById('cliente-nombre');
    const clienteTelefono = document.getElementById('cliente-telefono');
    
    if (clienteNombre) {
        // Verificar diferentes nombres de campos
        const nombre = mascota.cliente_nombre || mascota.nombre_cliente || mascota.NombreCliente;
        const apellido = mascota.cliente_apellido || mascota.apellido_cliente || mascota.ApellidoCliente;
        
        if (nombre && apellido) {
            clienteNombre.textContent = `${nombre} ${apellido}`;
        } else if (mascota.cliente) {
            clienteNombre.textContent = mascota.cliente;
        } else {
            clienteNombre.textContent = 'No registrado';
        }
    }
    
    if (clienteTelefono) {
        // Verificar diferentes nombres de campo para teléfono
        const telefono = mascota.cliente_telefono || mascota.telefono_cliente || mascota.TelefonoCliente || mascota.telefono;
        clienteTelefono.textContent = telefono || 'No registrado';
    }
}

function actualizarHistorialCortes(historial) {
    const historialContent = document.getElementById('historial-cortes-content');
    if (!historialContent) return;
    
    console.log('Historial recibido:', historial);
    
    if (historial && historial.length > 0) {
        let html = '';
        
        historial.forEach(corte => {
            const tipoCorte = corte.tipo_corte || 'Corte general';
            const fecha = corte.fecha_formateada || 'Fecha no disponible';
            const descripcion = corte.descripcion || corte.notas || '';
            
            html += `
            <div class="historial-corte-item mb-2 pb-2 border-bottom">
                <div class="d-flex justify-content-between align-items-start">
                    <strong class="text-primary">${tipoCorte}</strong>
                    <small class="text-muted">${fecha}</small>
                </div>
                ${descripcion ? `<div class="text-muted mt-1 small">${descripcion}</div>` : ''}
            </div>`;
        });
        
        historialContent.innerHTML = html;
        
    } else {
        historialContent.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-cut fa-2x text-muted mb-3"></i>
                <p class="text-muted mb-0">No hay registros de cortes</p>
                <small class="text-muted">Los cortes anteriores aparecerán aquí</small>
            </div>
        `;
    }
}
function llenarModalActualizacion(idMascota, mascota) {
    console.log('Llenando modal con datos:', mascota); // Para debugging
    
    // Mapear nombres de campos
    const campoMap = {
        'mascota_id_actualizar': 'id_mascota',
        'raza_actualizar': mascota.raza || mascota.Raza,
        'color_actualizar': mascota.color || mascota.Color,
        'corte_actualizar': mascota.corte || mascota.tipo_corte || mascota.TipoCorte,
        'tamano_actualizar': mascota.tamano || mascota.Tamano,
        'peso_actualizar': mascota.peso || mascota.Peso,
        'caracteristicas_actualizar': mascota.caracteristicas || mascota.Caracteristicas,
        'alergias_actualizar': mascota.alergias || mascota.Alergias
    };
    
    Object.keys(campoMap).forEach(id => {
        const elemento = document.getElementById(id);
        if (elemento) {
            if (id === 'mascota_id_actualizar') {
                elemento.value = idMascota;
            } else {
                elemento.value = campoMap[id] || '';
            }
        }
    });
}

// ================= FUNCIONES PARA ACTUALIZAR DATOS =================

function mostrarModalActualizarMascota() {
    const modalElement = document.getElementById('modalActualizarMascota');
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        
        // Enfocar el primer campo
        setTimeout(() => {
            const primerCampo = document.getElementById('raza_actualizar');
            if (primerCampo) primerCampo.focus();
        }, 300);
    }
}

function enviarActualizacionMascota(e) {
    e.preventDefault();
    
    const form = document.getElementById('form-actualizar-mascota');
    if (!form) {
        mostrarError('No se encontró el formulario de actualización');
        return;
    }
    
    const formData = new FormData(form);
    const mascotaId = formData.get('mascota_id');
    
    if (!mascotaId) {
        mostrarError('ID de mascota no válido');
        return;
    }
    
    // Validar campos requeridos
    const raza = formData.get('raza')?.trim();
    const color = formData.get('color')?.trim();
    
    if (!raza || !color) {
        mostrarError('Los campos Raza y Color son obligatorios');
        return;
    }
    
    // Mostrar indicador de carga
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Guardando...';
    submitBtn.disabled = true;
    
    console.log('Enviando datos:', Object.fromEntries(formData.entries())); // Para debugging
    
    // IMPORTANTE: Usar la ruta correcta que tienes en tu backend
    fetch(`/mascotas/actualizar-datos/${mascotaId}`, {
        method: 'POST',
        body: formData,
        headers: {
            'Accept': 'application/json',
        }
    })
    .then(response => {
        console.log('Respuesta recibida, status:', response.status);
        
        if (!response.ok) {
            // Si la respuesta no es OK, intentar leer el mensaje de error
            return response.text().then(text => {
                throw new Error(`Error ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Datos recibidos del servidor:', data);
        
        if (data.success) {
            // Cerrar modal
            const modalElement = document.getElementById('modalActualizarMascota');
            if (modalElement) {
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) modal.hide();
            }
            
            // Recargar datos de la mascota
            cargarDatosMascota();
            
            // Mostrar mensaje de éxito
            mostrarExito(data.message || 'Datos actualizados correctamente');
            
            // Opcional: actualizar el select de mascotas si es necesario
            setTimeout(() => {
                const selectMascota = document.getElementById('id_mascota');
                if (selectMascota) {
                    // Disparar evento para recargar todo
                    selectMascota.dispatchEvent(new Event('change'));
                }
            }, 500);
            
        } else {
            mostrarError('Error del servidor: ' + (data.error || 'Error desconocido'));
        }
    })
    .catch(error => {
        console.error('Error en la petición:', error);
        
        // Manejo específico de errores de conexión
        let mensajeError = 'Error al actualizar datos. ';
        
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            mensajeError += 'Verifica tu conexión a internet.';
        } else if (error.message.includes('404')) {
            mensajeError += 'La ruta no fue encontrada en el servidor.';
        } else if (error.message.includes('500')) {
            mensajeError += 'Error interno del servidor.';
        } else {
            mensajeError += error.message;
        }
        
        mostrarError(mensajeError);
    })
    .finally(() => {
        // Restaurar botón
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

// ================= FUNCIONES DE UTILIDAD =================

function mostrarExito(mensaje) {
    // Usar función existente o crear una nueva
    if (typeof mostrarNotificacion === 'function') {
        mostrarNotificacion('Éxito', 'success', mensaje);
    } else {
        // Crear notificación básica
        crearNotificacion('success', mensaje);
    }
}

function mostrarError(mensaje) {
    console.error('Error mostrado al usuario:', mensaje);
    
    if (typeof mostrarNotificacion === 'function') {
        mostrarNotificacion('Error', 'error', mensaje);
    } else {
        // Crear notificación básica
        crearNotificacion('danger', mensaje);
    }
}

function crearNotificacion(tipo, mensaje) {
    // Crear elemento de alerta
    const alerta = document.createElement('div');
    alerta.className = `alert alert-${tipo} alert-dismissible fade show`;
    alerta.style.cssText = 'position:fixed; top:20px; right:20px; z-index:9999; min-width:300px; max-width:400px;';
    alerta.innerHTML = `
        <strong>${tipo === 'success' ? 'Éxito' : 'Error'}:</strong> ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Agregar al documento
    document.body.appendChild(alerta);
    
    // Auto-eliminar después de 5 segundos
    setTimeout(() => {
        if (alerta.parentNode) {
            alerta.remove();
        }
    }, 5000);
}

// ================= INICIALIZACIÓN =================

function inicializarReservasMascota() {
    console.log('Inicializando reservas mascota...');
    
    // Configurar evento para select de mascota
    const selectMascota = document.getElementById('id_mascota');
    if (selectMascota) {
        selectMascota.addEventListener('change', function() {
            console.log('Mascota seleccionada:', this.value);
            cargarDatosMascota();
        });
        
        // Cargar datos si ya hay una mascota seleccionada (para edición)
        if (selectMascota.value) {
            console.log('Cargando datos iniciales para mascota:', selectMascota.value);
            setTimeout(() => cargarDatosMascota(), 100);
        }
    }
    
    // Configurar formulario de actualización
    const formActualizar = document.getElementById('form-actualizar-mascota');
    if (formActualizar) {
        formActualizar.addEventListener('submit', enviarActualizacionMascota);
    }
    
    // Configurar botón para abrir modal (eliminar onclick inline)
    const btnModal = document.querySelector('[onclick*="mostrarModalActualizarMascota"]');
    if (btnModal) {
        btnModal.removeAttribute('onclick');
        btnModal.addEventListener('click', function(e) {
            e.preventDefault();
            mostrarModalActualizarMascota();
        });
    }
    
    // Configurar validación en tiempo real para campos requeridos
    const camposRequeridos = ['raza_actualizar', 'color_actualizar'];
    camposRequeridos.forEach(id => {
        const campo = document.getElementById(id);
        if (campo) {
            campo.addEventListener('blur', function() {
                if (!this.value.trim()) {
                    this.classList.add('is-invalid');
                } else {
                    this.classList.remove('is-invalid');
                }
            });
        }
    });
}

// Inicializar cuando el DOM esté cargado
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM cargado, inicializando...');
    inicializarReservasMascota();
    
    // Inicializar tooltips si existen
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(el => new bootstrap.Tooltip(el));
    }
});