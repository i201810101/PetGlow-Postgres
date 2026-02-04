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
            
            if (data.existe && data.usuario) {
                infoUsuarioDiv.innerHTML = `
                    <div class="card border-info">
                        <div class="card-body">
                            <h6 class="card-title">
                                <i class="fas fa-user-circle me-2 text-info"></i>Información del Usuario
                            </h6>
                            <div class="row">
                                <div class="col-6">
                                    <p class="mb-1"><strong>Username:</strong></p>
                                    <p class="mb-1"><strong>Rol:</strong></p>
                                    <p class="mb-1"><strong>Último login:</strong></p>
                                    <p class="mb-0"><strong>Estado:</strong></p>
                                </div>
                                <div class="col-6">
                                    <p class="mb-1">${data.usuario.username}</p>
                                    <p class="mb-1">
                                        <span class="badge bg-info">${data.usuario.rol}</span>
                                    </p>
                                    <p class="mb-1">${data.usuario.ultimo_login || 'Nunca'}</p>
                                    <p class="mb-0">
                                        ${data.usuario.activo ? 
                                            '<span class="badge bg-success">Activo</span>' : 
                                            '<span class="badge bg-secondary">Inactivo</span>'
                                        }
                                    </p>
                                </div>
                            </div>
                            <div class="mt-3">
                                <button class="btn btn-sm btn-outline-warning" onclick="editarUsuario(${data.usuario.id_usuario})">
                                    <i class="fas fa-edit me-1"></i>Editar Usuario
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                infoUsuarioDiv.innerHTML = `
                    <div class="card border-warning">
                        <div class="card-body text-center">
                            <i class="fas fa-user-slash fa-2x text-warning mb-3"></i>
                            <h6 class="card-title text-warning">Sin Usuario</h6>
                            <p class="card-text">Este empleado no tiene usuario para el sistema.</p>
                            <button class="btn btn-sm btn-success" onclick="crearUsuario(${idEmpleado})">
                                <i class="fas fa-plus me-1"></i>Crear Usuario
                            </button>
                        </div>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error cargando usuario:', error);
            infoUsuarioDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error al cargar información del usuario
                </div>
            `;
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

// Función para crear usuario con modal
window.crearUsuario = function(idEmpleado) {
    // Guardar ID del empleado
    document.getElementById('crear_usuario_id_empleado').value = idEmpleado;
    
    // Resetear formulario
    const form = document.getElementById('formCrearUsuario');
    form.reset();
    form.classList.remove('was-validated');
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('modalCrearUsuario'));
    modal.show();
}

// Función para editar usuario con modal
window.editarUsuario = function(idUsuario) {
    // Cargar datos del usuario
    fetch(`/api/usuarios/${idUsuario}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const usuario = data.usuario;
                
                // Rellenar formulario
                document.getElementById('editar_usuario_id').value = usuario.id_usuario;
                document.getElementById('editar_usuario_id_empleado').value = usuario.id_empleado;
                document.getElementById('editar_usuario_username').value = usuario.username;
                document.getElementById('editar_usuario_rol').value = usuario.rol;
                document.getElementById('editar_usuario_activo').checked = usuario.activo;
                
                // Limpiar campo de contraseña
                document.getElementById('editar_usuario_password').value = '';
                
                // Mostrar nombre del empleado si está disponible
                const nombreEmpleado = document.getElementById('empleado_usuario_nombre');
                if (nombreEmpleado && usuario.nombre && usuario.apellido) {
                    nombreEmpleado.textContent = `${usuario.nombre} ${usuario.apellido}`;
                }
                
                // Mostrar modal
                const modal = new bootstrap.Modal(document.getElementById('modalEditarUsuarioEmpleado'));
                modal.show();
            } else {
                throw new Error(data.error || 'Error al cargar usuario');
            }
        })
        .catch(error => {
            console.error('Error cargando usuario:', error);
            mostrarNotificacionModal('❌ Error: ' + error.message, 'error');
        });
}
// ==================== MANEJO DE MODALES DE USUARIO ====================

document.addEventListener('DOMContentLoaded', function() {
    // Configurar formulario para crear usuario
    const formCrearUsuario = document.getElementById('formCrearUsuario');
    if (formCrearUsuario) {
        formCrearUsuario.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (!this.checkValidity()) {
                this.classList.add('was-validated');
                return;
            }
            
            const idEmpleado = document.getElementById('crear_usuario_id_empleado').value;
            const datos = {
                username: document.getElementById('crear_usuario_username').value,
                password: document.getElementById('crear_usuario_password').value,
                rol: document.getElementById('crear_usuario_rol').value,
                activo: document.getElementById('crear_usuario_activo').checked
            };
            
            crearUsuarioAPI(idEmpleado, datos);
        });
    }
    
    // Configurar formulario para editar usuario
    const formEditarUsuarioEmpleado = document.getElementById('formEditarUsuarioEmpleado');
    if (formEditarUsuarioEmpleado) {
        formEditarUsuarioEmpleado.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (!this.checkValidity()) {
                this.classList.add('was-validated');
                return;
            }
            
            const idUsuario = document.getElementById('editar_usuario_id').value;
            const idEmpleado = document.getElementById('editar_usuario_id_empleado').value;
            
            const datos = {
                rol: document.getElementById('editar_usuario_rol').value,
                activo: document.getElementById('editar_usuario_activo').checked
            };
            
            // Agregar contraseña solo si se proporcionó
            const nuevaPassword = document.getElementById('editar_usuario_password').value;
            if (nuevaPassword && nuevaPassword.trim() !== '') {
                datos.password = nuevaPassword;
            }
            
            editarUsuarioAPI(idUsuario, datos, idEmpleado);
        });
    }
    
    // Generador de contraseña
    const btnGenerarPassword = document.getElementById('btnGenerarPassword');
    if (btnGenerarPassword) {
        btnGenerarPassword.addEventListener('click', function() {
            const password = generarPasswordSegura(12);
            document.getElementById('crear_usuario_password').value = password;
            
            // Mostrar contraseña temporalmente
            const input = document.getElementById('crear_usuario_password');
            input.type = 'text';
            
            // Cambiar icono
            const iconos = document.querySelectorAll('.password-toggle i');
            iconos.forEach(icon => {
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            });
            
            // Volver a ocultar después de 5 segundos
            setTimeout(() => {
                input.type = 'password';
                iconos.forEach(icon => {
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                });
            }, 5000);
        });
    }
    
    // Toggle para mostrar/ocultar contraseña
    document.querySelectorAll('.password-toggle').forEach(toggle => {
        toggle.addEventListener('click', function() {
            const input = this.closest('.input-group').querySelector('input');
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });
});

// Función para generar contraseña segura
function generarPasswordSegura(longitud = 12) {
    const caracteres = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
    let password = '';
    
    // Asegurar al menos una mayúscula, una minúscula, un número y un símbolo
    password += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[Math.floor(Math.random() * 26)];
    password += 'abcdefghijklmnopqrstuvwxyz'[Math.floor(Math.random() * 26)];
    password += '0123456789'[Math.floor(Math.random() * 10)];
    password += '!@#$%^&*'[Math.floor(Math.random() * 8)];
    
    // Completar el resto
    for (let i = password.length; i < longitud; i++) {
        password += caracteres.charAt(Math.floor(Math.random() * caracteres.length));
    }
    
    // Mezclar la contraseña
    return password.split('').sort(() => Math.random() - 0.5).join('');
}

// Función para crear usuario via API
function crearUsuarioAPI(idEmpleado, datos) {
    const btnSubmit = document.querySelector('#formCrearUsuario button[type="submit"]');
    const originalText = btnSubmit.innerHTML;
    
    btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Creando...';
    btnSubmit.disabled = true;
    
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
            // Cerrar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalCrearUsuario'));
            modal.hide();
            
            // Mostrar notificación
            mostrarNotificacionModal('✅ Usuario creado exitosamente', 'success');
            
            // Recargar información del usuario en el modal de empleado
            if (typeof cargarInfoUsuario === 'function') {
                cargarInfoUsuario(idEmpleado);
            }
        } else {
            throw new Error(data.error || 'Error al crear usuario');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarNotificacionModal('❌ ' + error.message, 'error');
    })
    .finally(() => {
        btnSubmit.innerHTML = originalText;
        btnSubmit.disabled = false;
    });
}

// Función para editar usuario via API
function editarUsuarioAPI(idUsuario, datos, idEmpleado) {
    const btnSubmit = document.querySelector('#formEditarUsuarioEmpleado button[type="submit"]');
    const originalText = btnSubmit.innerHTML;
    
    btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Actualizando...';
    btnSubmit.disabled = true;
    
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
            // Cerrar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalEditarUsuarioEmpleado'));
            modal.hide();
            
            // Mostrar notificación
            mostrarNotificacionModal('✅ Usuario actualizado exitosamente', 'success');
            
            // Recargar información del usuario en el modal de empleado
            if (typeof cargarInfoUsuario === 'function' && idEmpleado) {
                cargarInfoUsuario(idEmpleado);
            }
        } else {
            throw new Error(data.error || 'Error al actualizar usuario');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarNotificacionModal('❌ ' + error.message, 'error');
    })
    .finally(() => {
        btnSubmit.innerHTML = originalText;
        btnSubmit.disabled = false;
    });
}

// Función para mostrar notificaciones en modales
function mostrarNotificacionModal(mensaje, tipo = 'info') {
    // Crear notificación
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${tipo} alert-dismissible fade show position-fixed bottom-0 end-0 m-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${tipo === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
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
// Exponer funciones al scope global
window.verEmpleado = verEmpleado;
window.editarEmpleado = editarEmpleado;
window.confirmarEliminarEmpleado = confirmarEliminarEmpleado;
window.cambiarPagina = cambiarPagina;
window.imprimirDetalles = imprimirDetalles;
window.crearUsuario = crearUsuario;
window.editarUsuario = editarUsuario;