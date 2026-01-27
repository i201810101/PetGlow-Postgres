/* static/js/empleados.js */

document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    let empleadosData = [];
    let empleadoAEliminar = null;
    let paginaActual = 1;
    const empleadosPorPagina = 10;
    
    // Elementos del DOM
    const filtroEstado = document.getElementById('filtroEstado');
    const filtroEspecialidad = document.getElementById('filtroEspecialidad');
    const filtroBusqueda = document.getElementById('filtroBusqueda');
    const btnBuscar = document.getElementById('btnBuscar');
    const tbodyEmpleados = document.getElementById('tbodyEmpleados');
    const totalEmpleados = document.getElementById('totalEmpleados');
    const paginacion = document.getElementById('paginacion');
    
    // Modales y formularios
    const formNuevoEmpleado = document.getElementById('formNuevoEmpleado');
    const formEditarEmpleado = document.getElementById('formEditarEmpleado');
    const crearUsuarioCheckbox = document.getElementById('crear_usuario');
    const datosUsuarioDiv = document.getElementById('datos_usuario');
    const btnConfirmarEliminar = document.getElementById('btnConfirmarEliminar');
    const empleadoAEliminarSpan = document.getElementById('empleado_a_eliminar');
    
    // Inicializar la aplicación
    cargarEmpleados();
    
    // ==================== EVENT LISTENERS ====================
    
    // Filtros
    if (filtroEstado) filtroEstado.addEventListener('change', filtrarEmpleados);
    if (filtroEspecialidad) filtroEspecialidad.addEventListener('change', filtrarEmpleados);
    if (btnBuscar) btnBuscar.addEventListener('click', filtrarEmpleados);
    if (filtroBusqueda) filtroBusqueda.addEventListener('keyup', function(e) {
        if (e.key === 'Enter') filtrarEmpleados();
    });
    
    // Checkbox para crear usuario
    if (crearUsuarioCheckbox) {
        crearUsuarioCheckbox.addEventListener('change', function() {
            datosUsuarioDiv.style.display = this.checked ? 'block' : 'none';
            const inputs = datosUsuarioDiv.querySelectorAll('input, select');
            inputs.forEach(input => {
                if (this.checked) {
                    input.required = true;
                } else {
                    input.required = false;
                }
            });
        });
    }
    
    // Formulario nuevo empleado
    if (formNuevoEmpleado) {
        formNuevoEmpleado.addEventListener('submit', guardarNuevoEmpleado);
    }
    
    // Formulario editar empleado
    if (formEditarEmpleado) {
        formEditarEmpleado.addEventListener('submit', actualizarEmpleado);
    }
    
    // Confirmar eliminación
    if (btnConfirmarEliminar) {
        btnConfirmarEliminar.addEventListener('click', eliminarEmpleado);
    }
    
    // Ver password
    const verPasswordBtn = document.getElementById('verPassword');
    if (verPasswordBtn) {
        verPasswordBtn.addEventListener('click', function() {
            const passwordInput = document.getElementById('nuevo_password');
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                this.innerHTML = '<i class="fas fa-eye-slash"></i>';
            } else {
                passwordInput.type = 'password';
                this.innerHTML = '<i class="fas fa-eye"></i>';
            }
        });
    }
    
    // ==================== FUNCIONES PRINCIPALES ====================
    
    function cargarEmpleados() {
        mostrarCarga(true);
        
        fetch('/api/empleados')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error en la respuesta del servidor');
                }
                return response.json();
            })
            // Debe ser:
            .then(data => {
                empleadosData = data;
                mostrarEmpleados();  // <-- Esta función ya aplica filtros
                mostrarCarga(false);
            })
            .catch(error => {
                console.error('Error cargando empleados:', error);
                mostrarNotificacion('Error al cargar empleados: ' + error.message, 'error');
                mostrarCarga(false);
            });
    }
    
    function mostrarCarga(mostrar) {
        const tbody = document.getElementById('tbodyEmpleados');
        if (mostrar) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Cargando...</span>
                        </div>
                        <p class="mt-2 text-muted">Cargando empleados...</p>
                    </td>
                </tr>
            `;
        }
    }
    
    function mostrarEmpleados() {
        // Filtrar y paginar
        const empleadosFiltrados = filtrarEmpleadosArray(empleadosData);
        const empleadosPaginados = paginarEmpleados(empleadosFiltrados);
        
        // Actualizar contador
        totalEmpleados.textContent = empleadosFiltrados.length;
        
        // Limpiar tabla
        tbodyEmpleados.innerHTML = '';
        
        // Mostrar empleados
        if (empleadosPaginados.length === 0) {
            tbodyEmpleados.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-4">
                        <i class="fas fa-user-slash fa-2x text-muted mb-3"></i>
                        <p class="text-muted">No se encontraron empleados</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        empleadosPaginados.forEach(empleado => {
            const tr = document.createElement('tr');
            tr.className = 'fade-in';
            
            // Badge para estado
            const estadoBadge = empleado.activo ? 
                '<span class="badge bg-success">Activo</span>' : 
                '<span class="badge bg-secondary">Inactivo</span>';
            
            // Badge para especialidad
            // En la función mostrarEmpleados(), reemplaza esta parte:
let especialidadBadge = '';
switch(empleado.especialidad) {
    case 'baño':
        especialidadBadge = '<span class="badge badge-baño">Baño</span>';
        break;
    case 'corte':
        especialidadBadge = '<span class="badge badge-corte">Corte</span>';
        break;
    case 'ambos':
        especialidadBadge = '<span class="badge badge-ambos">Ambos</span>';
        break;
    case 'ventas':
        especialidadBadge = '<span class="badge badge-ventas">Ventas</span>';
        break;
    default:
        especialidadBadge = `<span class="badge bg-secondary">${empleado.especialidad || 'No definida'}</span>`;
}
            
            tr.innerHTML = `
                <td>${empleado.id_empleado}</td>
                <td>${empleado.dni}</td>
                <td>${empleado.nombre} ${empleado.apellido}</td>
                <td>${empleado.telefono || '-'}</td>
                <td>${empleado.email}</td>
                <td>${especialidadBadge}</td>
                <td>${estadoBadge}</td>
                <td>
                    <button class="btn btn-sm btn-warning btn-action" onclick="editarEmpleado(${empleado.id_empleado})" title="Editar" ${!empleado.activo ? 'disabled' : ''}>
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger btn-action" onclick="confirmarEliminarEmpleado(${empleado.id_empleado}, '${empleado.nombre} ${empleado.apellido}')" title="Desactivar" ${!empleado.activo ? 'disabled' : ''}>
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </td>
            `;
            
            tbodyEmpleados.appendChild(tr);
        });
        
        // Actualizar paginación
        actualizarPaginacion(empleadosFiltrados.length);
    }
    
    function filtrarEmpleadosArray(empleados) {
        let filtrados = [...empleados];
        
        // Filtrar por estado
        const estadoFiltro = filtroEstado ? filtroEstado.value : 'todos';
        if (estadoFiltro !== 'todos') {
            const activo = estadoFiltro === 'activo';
            filtrados = filtrados.filter(e => e.activo === activo);
        }
        
        // Filtrar por especialidad
        const especialidadFiltro = filtroEspecialidad ? filtroEspecialidad.value : 'todos';
        if (especialidadFiltro !== 'todos') {
            filtrados = filtrados.filter(e => e.especialidad === especialidadFiltro);
        }
        
        // Filtrar por búsqueda
        const busqueda = filtroBusqueda ? filtroBusqueda.value.toLowerCase().trim() : '';
        if (busqueda) {
            filtrados = filtrados.filter(e => 
                e.dni.toLowerCase().includes(busqueda) ||
                e.nombre.toLowerCase().includes(busqueda) ||
                e.apellido.toLowerCase().includes(busqueda) ||
                e.email.toLowerCase().includes(busqueda) ||
                (e.telefono && e.telefono.includes(busqueda))
            );
        }
        
        return filtrados;
    }
    
    function filtrarEmpleados() {
        paginaActual = 1;
        mostrarEmpleados();
    }
    
    function paginarEmpleados(empleados) {
        const inicio = (paginaActual - 1) * empleadosPorPagina;
        const fin = inicio + empleadosPorPagina;
        return empleados.slice(inicio, fin);
    }
    
    function actualizarPaginacion(totalEmpleados) {
        const totalPaginas = Math.ceil(totalEmpleados / empleadosPorPagina);
        const ul = paginacion.querySelector('ul');
        ul.innerHTML = '';
        
        if (totalPaginas <= 1) return;
        
        // Botón anterior
        const liPrev = document.createElement('li');
        liPrev.className = `page-item ${paginaActual === 1 ? 'disabled' : ''}`;
        liPrev.innerHTML = `
            <a class="page-link" href="#" aria-label="Anterior" onclick="cambiarPagina(${paginaActual - 1})">
                <span aria-hidden="true">&laquo;</span>
            </a>
        `;
        ul.appendChild(liPrev);
        
        // Números de página
        for (let i = 1; i <= totalPaginas; i++) {
            const li = document.createElement('li');
            li.className = `page-item ${i === paginaActual ? 'active' : ''}`;
            li.innerHTML = `<a class="page-link" href="#" onclick="cambiarPagina(${i})">${i}</a>`;
            ul.appendChild(li);
        }
        
        // Botón siguiente
        const liNext = document.createElement('li');
        liNext.className = `page-item ${paginaActual === totalPaginas ? 'disabled' : ''}`;
        liNext.innerHTML = `
            <a class="page-link" href="#" aria-label="Siguiente" onclick="cambiarPagina(${paginaActual + 1})">
                <span aria-hidden="true">&raquo;</span>
            </a>
        `;
        ul.appendChild(liNext);
    }
    
    // ==================== FUNCIONES PARA LOS MODALES ====================
    
    function guardarNuevoEmpleado(e) {
        e.preventDefault();
        
        // Validar formulario
        if (!formNuevoEmpleado.checkValidity()) {
            formNuevoEmpleado.classList.add('was-validated');
            return;
        }
        
        // Mostrar carga
        const submitBtn = formNuevoEmpleado.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Guardando...';
        submitBtn.disabled = true;
        
        // Recoger datos del formulario
        const formData = new FormData(formNuevoEmpleado);
        const datos = {
            dni: formData.get('dni'),
            nombre: formData.get('nombre'),
            apellido: formData.get('apellido'),
            telefono: formData.get('telefono'),
            email: formData.get('email'),
            especialidad: formData.get('especialidad'),
            fecha_contratacion: formData.get('fecha_contratacion'),
            activo: formData.get('activo') === 'on'
        };
        
        // Datos del usuario si se crea
        if (crearUsuarioCheckbox.checked) {
            datos.usuario = {
                username: formData.get('username'),
                password: formData.get('password'),
                rol: formData.get('rol')
            };
        }
        
        // Enviar datos
        fetch('/api/empleados', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(datos)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Cerrar modal y resetear formulario
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalNuevoEmpleado'));
                modal.hide();
                formNuevoEmpleado.reset();
                formNuevoEmpleado.classList.remove('was-validated');
                datosUsuarioDiv.style.display = 'none';
                
                // Recargar empleados
                cargarEmpleados();
                
                // Mostrar notificación
                mostrarNotificacion('✅ Empleado creado exitosamente', 'success');
            } else {
                throw new Error(data.error || 'Error al crear empleado');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarNotificacion('❌ ' + error.message, 'error');
        })
        .finally(() => {
            // Restaurar botón
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        });
    }
    
    window.editarEmpleado = function(id) {
        // Mostrar carga en el modal
        const infoUsuarioDiv = document.getElementById('info_usuario');
        infoUsuarioDiv.innerHTML = '<p class="text-muted"><i class="fas fa-spinner fa-spin me-2"></i>Cargando información del empleado...</p>';
        
        // Cargar datos del empleado
        fetch(`/api/empleados/${id}`)
            .then(response => response.json())
            .then(empleado => {
                if (empleado.error) {
                    throw new Error(empleado.error);
                }
                
                // Llenar formulario
                document.getElementById('editar_id').value = empleado.id_empleado;
                document.getElementById('editar_dni').value = empleado.dni;
                document.getElementById('editar_nombre').value = empleado.nombre;
                document.getElementById('editar_apellido').value = empleado.apellido;
                document.getElementById('editar_telefono').value = empleado.telefono || '';
                document.getElementById('editar_email').value = empleado.email;
                document.getElementById('editar_especialidad').value = empleado.especialidad;
                
                // Formatear fecha para input type="date"
                if (empleado.fecha_contratacion) {
                    const fecha = new Date(empleado.fecha_contratacion);
                    document.getElementById('editar_fecha_contratacion').value = 
                        fecha.toISOString().split('T')[0];
                } else {
                    document.getElementById('editar_fecha_contratacion').value = '';
                }
                
                document.getElementById('editar_activo').checked = empleado.activo;
                
                // Cargar información del usuario
                cargarInfoUsuario(id);
                
                // Mostrar modal
                const modal = new bootstrap.Modal(document.getElementById('modalEditarEmpleado'));
                modal.show();
            })
            .catch(error => {
                console.error('Error cargando empleado:', error);
                mostrarNotificacion('❌ Error al cargar empleado: ' + error.message, 'error');
                infoUsuarioDiv.innerHTML = '<p class="text-danger">Error al cargar información</p>';
            });
    }
    
    function cargarInfoUsuario(idEmpleado) {
        const infoUsuarioDiv = document.getElementById('info_usuario');
        
        fetch(`/api/empleados/${idEmpleado}/usuario`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                if (data.existe) {
                    infoUsuarioDiv.innerHTML = `
                        <div class="alert alert-info">
                            <p><strong>Username:</strong> ${data.usuario.username}</p>
                            <p><strong>Rol:</strong> ${data.usuario.rol}</p>
                            <p><strong>Último login:</strong> ${data.usuario.ultimo_login || 'Nunca'}</p>
                            <p><strong>Estado:</strong> ${data.usuario.activo ? 'Activo' : 'Inactivo'}</p>
                            <button class="btn btn-sm btn-outline-warning" onclick="editarUsuario(${data.usuario.id_usuario})">
                                <i class="fas fa-key me-1"></i>Editar Usuario
                            </button>
                        </div>
                    `;
                } else {
                    infoUsuarioDiv.innerHTML = `
                        <div class="alert alert-warning">
                            <p>Este empleado no tiene usuario para el sistema.</p>
                            <button class="btn btn-sm btn-outline-success" onclick="crearUsuario(${idEmpleado})">
                                <i class="fas fa-plus me-1"></i>Crear Usuario
                            </button>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error cargando usuario:', error);
                infoUsuarioDiv.innerHTML = '<p class="text-danger">Error al cargar información del usuario</p>';
            });
    }
    
    function actualizarEmpleado(e) {
        e.preventDefault();
        
        // Validar formulario
        if (!formEditarEmpleado.checkValidity()) {
            formEditarEmpleado.classList.add('was-validated');
            return;
        }
        
        // Mostrar carga
        const submitBtn = formEditarEmpleado.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Actualizando...';
        submitBtn.disabled = true;
        
        // Recoger datos del formulario
        const formData = new FormData(formEditarEmpleado);
        const datos = {
            dni: formData.get('dni'),
            nombre: formData.get('nombre'),
            apellido: formData.get('apellido'),
            telefono: formData.get('telefono'),
            email: formData.get('email'),
            especialidad: formData.get('especialidad'),
            fecha_contratacion: formData.get('fecha_contratacion'),
            activo: formData.get('activo') === 'on'
        };
        
        const idEmpleado = formData.get('id_empleado');
        
        // Enviar datos
        fetch(`/api/empleados/${idEmpleado}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(datos)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Cerrar modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalEditarEmpleado'));
                modal.hide();
                
                // Recargar empleados
                cargarEmpleados();
                
                // Mostrar notificación
                mostrarNotificacion('✅ Empleado actualizado exitosamente', 'success');
            } else {
                throw new Error(data.error || 'Error al actualizar empleado');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarNotificacion('❌ ' + error.message, 'error');
        })
        .finally(() => {
            // Restaurar botón
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        });
    }
    
    window.confirmarEliminarEmpleado = function(id, nombreCompleto) {
        empleadoAEliminar = id;
        empleadoAEliminarSpan.textContent = nombreCompleto;
        const modal = new bootstrap.Modal(document.getElementById('modalConfirmarEliminar'));
        modal.show();
    }
    
    function eliminarEmpleado() {
        if (!empleadoAEliminar) return;
        
        // Mostrar carga
        const btn = document.getElementById('btnConfirmarEliminar');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Desactivando...';
        btn.disabled = true;
        
        fetch(`/api/empleados/${empleadoAEliminar}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Cerrar modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalConfirmarEliminar'));
                modal.hide();
                
                // Recargar empleados
                cargarEmpleados();
                
                // Mostrar notificación
                mostrarNotificacion('✅ Empleado desactivado exitosamente', 'success');
                
                // Resetear variable
                empleadoAEliminar = null;
            } else {
                throw new Error(data.error || 'Error al desactivar empleado');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarNotificacion('❌ ' + error.message, 'error');
        })
        .finally(() => {
            // Restaurar botón
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
    }
    
    // Función auxiliar para mostrar notificaciones
    function mostrarNotificacion(mensaje, tipo = 'info') {
        // Crear notificación
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${tipo} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        alertDiv.style.zIndex = '9999';
        alertDiv.style.minWidth = '300px';
        alertDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="flex-grow-1">${mensaje}</div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        document.body.appendChild(alertDiv);
        
        // Auto-eliminar después de 5 segundos
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
});

// ==================== FUNCIONES GLOBALES ====================

// Función para cambiar página
window.cambiarPagina = function(nuevaPagina) {
    window.paginaActual = nuevaPagina;
    // Disparar evento para recargar
    const event = new Event('DOMContentLoaded');
    document.dispatchEvent(event);
}

// Función para crear usuario
window.crearUsuario = function(idEmpleado) {
    const username = prompt('Ingrese el username para el empleado:');
    if (!username) return;
    
    const password = prompt('Ingrese la contraseña inicial (mínimo 6 caracteres):');
    if (!password || password.length < 6) {
        alert('La contraseña debe tener al menos 6 caracteres');
        return;
    }
    
    const rol = prompt('Ingrese el rol (admin, gerente, empleado, cajero):');
    if (!['admin', 'gerente', 'empleado', 'cajero'].includes(rol)) {
        alert('Rol inválido. Debe ser: admin, gerente, empleado o cajero');
        return;
    }
    
    const datos = {
        username: username,
        password: password,
        rol: rol
    };
    
    fetch(`/api/empleados/${idEmpleado}/usuario`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(datos)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('✅ Usuario creado exitosamente');
            // Recargar información del usuario
            if (typeof cargarInfoUsuario === 'function') {
                cargarInfoUsuario(idEmpleado);
            }
        } else {
            throw new Error(data.error || 'Error al crear usuario');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('❌ ' + error.message);
    });
}

// Función para editar usuario
window.editarUsuario = function(idUsuario) {
    const nuevoRol = prompt('Ingrese el nuevo rol (admin, gerente, empleado, cajero):');
    if (!nuevoRol || !['admin', 'gerente', 'empleado', 'cajero'].includes(nuevoRol)) {
        alert('Rol inválido. Debe ser: admin, gerente, empleado o cajero');
        return;
    }
    
    const resetPassword = confirm('¿Desea resetear la contraseña?');
    let datos = { rol: nuevoRol };
    
    if (resetPassword) {
        const nuevaPassword = prompt('Ingrese la nueva contraseña (dejar vacío para no cambiar):');
        if (nuevaPassword) {
            if (nuevaPassword.length < 6) {
                alert('La contraseña debe tener al menos 6 caracteres');
                return;
            }
            datos.password = nuevaPassword;
        }
    }
    
    fetch(`/api/usuarios/${idUsuario}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(datos)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('✅ Usuario actualizado exitosamente');
            // Recargar información del usuario
            const modalEditar = document.getElementById('modalEditarEmpleado');
            if (bootstrap.Modal.getInstance(modalEditar)) {
                const idInput = document.getElementById('editar_id');
                if (idInput && typeof cargarInfoUsuario === 'function') {
                    cargarInfoUsuario(parseInt(idInput.value));
                }
            }
        } else {
            throw new Error(data.error || 'Error al actualizar usuario');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('❌ ' + error.message);
    });
}

// Exponer funciones al scope global
window.verEmpleado = verEmpleado;
window.editarEmpleado = editarEmpleado;
window.confirmarEliminarEmpleado = confirmarEliminarEmpleado;
window.cambiarPagina = cambiarPagina;
window.imprimirDetalles = imprimirDetalles;
window.crearUsuario = crearUsuario;
window.editarUsuario = editarUsuario;