// ==================== GESTIÓN DE USUARIOS ====================

document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    let usuarioAEliminar = null;
    let paginaActual = 1;
    const usuariosPorPagina = 10;
    
    // Elementos del DOM
    const buscadorUsuarios = document.getElementById('buscador-usuarios');
    const filtroRol = document.getElementById('filtro-rol');
    const filtroEstado = document.getElementById('filtro-estado');
    const tbodyUsuarios = document.getElementById('tbody-usuarios');
    const totalUsuarios = document.getElementById('total-usuarios');
    const paginacion = document.getElementById('paginacion-usuarios');
    
    // Modales y formularios
    const formNuevoUsuario = document.getElementById('form-nuevo-usuario');
    const formEditarUsuario = document.getElementById('form-editar-usuario');
    const btnConfirmarEliminar = document.getElementById('btn-confirmar-eliminar');
    const usuarioAEliminarSpan = document.getElementById('usuario-a-eliminar');
    
    // ==================== EVENT LISTENERS ====================
    
    // Búsqueda y filtros
    if (buscadorUsuarios) buscadorUsuarios.addEventListener('input', buscarUsuarios);
    if (filtroRol) filtroRol.addEventListener('change', buscarUsuarios);
    if (filtroEstado) filtroEstado.addEventListener('change', buscarUsuarios);
    
    // Formulario nuevo usuario
    if (formNuevoUsuario) {
        formNuevoUsuario.addEventListener('submit', guardarNuevoUsuario);
    }
    
    // Formulario editar usuario
    if (formEditarUsuario) {
        formEditarUsuario.addEventListener('submit', actualizarUsuario);
    }
    
    // Confirmar eliminación
    if (btnConfirmarEliminar) {
        btnConfirmarEliminar.addEventListener('click', eliminarUsuario);
    }
    
    // Toggle para mostrar/ocultar contraseña
    document.querySelectorAll('.password-toggle').forEach(toggle => {
        toggle.addEventListener('click', function() {
            const input = this.parentElement.querySelector('input');
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
    
    // Generador de contraseña
    const btnGenerarPassword = document.getElementById('btn-generar-password');
    if (btnGenerarPassword) {
        btnGenerarPassword.addEventListener('click', generarPassword);
    }
    
    // ==================== FUNCIONES PRINCIPALES ====================
    
    function buscarUsuarios() {
        const busqueda = buscadorUsuarios ? buscadorUsuarios.value.toLowerCase() : '';
        const rolFiltro = filtroRol ? filtroRol.value : 'todos';
        const estadoFiltro = filtroEstado ? filtroEstado.value : 'todos';
        
        const filas = document.querySelectorAll('#tbody-usuarios tr');
        let encontrados = 0;
        
        filas.forEach(fila => {
            if (fila.classList.contains('fila-vacia')) return;
            
            const username = fila.getAttribute('data-username') || '';
            const nombre = fila.getAttribute('data-nombre') || '';
            const apellido = fila.getAttribute('data-apellido') || '';
            const rol = fila.getAttribute('data-rol') || '';
            const estado = fila.getAttribute('data-estado') || '';
            
            // Aplicar filtros
            const pasaFiltroRol = rolFiltro === 'todos' || rol === rolFiltro;
            const pasaFiltroEstado = estadoFiltro === 'todos' || estado === estadoFiltro;
            const pasaBusqueda = !busqueda || 
                username.toLowerCase().includes(busqueda) ||
                nombre.toLowerCase().includes(busqueda) ||
                apellido.toLowerCase().includes(busqueda);
            
            if (pasaFiltroRol && pasaFiltroEstado && pasaBusqueda) {
                fila.style.display = '';
                encontrados++;
            } else {
                fila.style.display = 'none';
            }
        });
        
        // Actualizar contador
        if (totalUsuarios) {
            totalUsuarios.textContent = encontrados;
        }
        
        // Manejar sin resultados
        manejarSinResultados(encontrados, filas.length);
        
        // Configurar paginación
        configurarPaginacion();
    }
    
    function manejarSinResultados(encontrados, totalFilas) {
        const cuerpoTabla = document.getElementById('tbody-usuarios');
        let mensaje = document.getElementById('sin-resultados');
        
        if (encontrados === 0 && totalFilas > 0) {
            if (!mensaje) {
                mensaje = document.createElement('tr');
                mensaje.id = 'sin-resultados';
                mensaje.className = 'fila-vacia';
                mensaje.innerHTML = `
                    <td colspan="7" class="text-center py-5">
                        <div class="py-4">
                            <i class="fas fa-search fa-3x text-muted mb-3"></i>
                            <h5 class="text-muted mb-3">No se encontraron usuarios</h5>
                            <button class="btn btn-outline-primary" id="btn-limpiar-filtros">
                                <i class="fas fa-times me-1"></i>Limpiar filtros
                            </button>
                        </div>
                    </td>
                `;
                cuerpoTabla.appendChild(mensaje);
                
                document.getElementById('btn-limpiar-filtros').addEventListener('click', limpiarFiltros);
            }
        } else if (mensaje) {
            mensaje.remove();
        }
    }
    
    function limpiarFiltros() {
        if (buscadorUsuarios) buscadorUsuarios.value = '';
        if (filtroRol) filtroRol.value = 'todos';
        if (filtroEstado) filtroEstado.value = 'todos';
        buscarUsuarios();
    }
    
    function configurarPaginacion() {
        const filasVisibles = Array.from(document.querySelectorAll('#tbody-usuarios tr'))
            .filter(fila => fila.style.display !== 'none' && !fila.classList.contains('fila-vacia'));
        
        const totalFilas = filasVisibles.length;
        
        if (!paginacion || totalFilas <= usuariosPorPagina) {
            if (paginacion) paginacion.innerHTML = '';
            mostrarTodasLasFilas(filasVisibles);
            return;
        }
        
        const totalPaginas = Math.ceil(totalFilas / usuariosPorPagina);
        paginacion.innerHTML = '';
        
        // Botón anterior
        const liPrev = document.createElement('li');
        liPrev.className = `page-item ${paginaActual === 1 ? 'disabled' : ''}`;
        liPrev.innerHTML = `
            <a class="page-link" href="#" aria-label="Anterior">
                <span aria-hidden="true">&laquo;</span>
            </a>
        `;
        liPrev.querySelector('a').addEventListener('click', (e) => {
            e.preventDefault();
            if (paginaActual > 1) cambiarPagina(paginaActual - 1, filasVisibles);
        });
        paginacion.appendChild(liPrev);
        
        // Números de página
        for (let i = 1; i <= totalPaginas; i++) {
            const li = document.createElement('li');
            li.className = `page-item ${i === paginaActual ? 'active' : ''}`;
            li.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            li.querySelector('a').addEventListener('click', (e) => {
                e.preventDefault();
                cambiarPagina(i, filasVisibles);
            });
            paginacion.appendChild(li);
        }
        
        // Botón siguiente
        const liNext = document.createElement('li');
        liNext.className = `page-item ${paginaActual === totalPaginas ? 'disabled' : ''}`;
        liNext.innerHTML = `
            <a class="page-link" href="#" aria-label="Siguiente">
                <span aria-hidden="true">&raquo;</span>
            </a>
        `;
        liNext.querySelector('a').addEventListener('click', (e) => {
            e.preventDefault();
            if (paginaActual < totalPaginas) cambiarPagina(paginaActual + 1, filasVisibles);
        });
        paginacion.appendChild(liNext);
        
        mostrarPagina(paginaActual, filasVisibles);
    }
    
    function cambiarPagina(pagina, filasVisibles) {
        paginaActual = pagina;
        mostrarPagina(pagina, filasVisibles);
    }
    
    function mostrarPagina(pagina, filasVisibles) {
        const inicio = (pagina - 1) * usuariosPorPagina;
        const fin = Math.min(inicio + usuariosPorPagina, filasVisibles.length);
        
        // Ocultar todas las filas
        document.querySelectorAll('#tbody-usuarios tr').forEach(fila => {
            if (!fila.classList.contains('fila-vacia')) {
                fila.style.display = 'none';
            }
        });
        
        // Mostrar filas de la página actual
        for (let i = inicio; i < fin; i++) {
            if (filasVisibles[i]) {
                filasVisibles[i].style.display = '';
            }
        }
        
        // Actualizar números de página
        const paginaInfo = document.getElementById('pagina-info');
        if (paginaInfo) {
            paginaInfo.textContent = `Mostrando ${inicio + 1}-${fin} de ${filasVisibles.length}`;
        }
    }
    
    function mostrarTodasLasFilas(filasVisibles) {
        filasVisibles.forEach(fila => fila.style.display = '');
        const paginaInfo = document.getElementById('pagina-info');
        if (paginaInfo) {
            paginaInfo.textContent = `Mostrando todos los ${filasVisibles.length} usuarios`;
        }
    }
    
    // ==================== FUNCIONES PARA FORMULARIOS ====================
    
    function guardarNuevoUsuario(e) {
        e.preventDefault();
        
        if (!formNuevoUsuario.checkValidity()) {
            formNuevoUsuario.classList.add('was-validated');
            return;
        }
        
        // Mostrar carga
        const submitBtn = formNuevoUsuario.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Guardando...';
        submitBtn.disabled = true;
        
        // Recoger datos del formulario
        const formData = new FormData(formNuevoUsuario);
        const datos = {
            username: formData.get('username'),
            password: formData.get('password'),
            id_empleado: formData.get('id_empleado'),
            rol: formData.get('rol'),
            activo: formData.get('activo') === 'on'
        };
        
        // Enviar datos
        fetch('/api/usuarios', {
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
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalNuevoUsuario'));
                modal.hide();
                formNuevoUsuario.reset();
                formNuevoUsuario.classList.remove('was-validated');
                
                // Recargar página
                window.location.reload();
                
                // Mostrar notificación
                mostrarNotificacion('✅ Usuario creado exitosamente', 'success');
            } else {
                throw new Error(data.error || 'Error al crear usuario');
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
    
    function actualizarUsuario(e) {
        e.preventDefault();
        
        if (!formEditarUsuario.checkValidity()) {
            formEditarUsuario.classList.add('was-validated');
            return;
        }
        
        // Mostrar carga
        const submitBtn = formEditarUsuario.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Actualizando...';
        submitBtn.disabled = true;
        
        // Recoger datos del formulario
        const formData = new FormData(formEditarUsuario);
        const datos = {
            username: formData.get('username'),
            rol: formData.get('rol'),
            activo: formData.get('activo') === 'on'
        };
        
        // Agregar contraseña solo si se proporcionó una nueva
        const nuevaPassword = formData.get('password');
        if (nuevaPassword && nuevaPassword.trim() !== '') {
            datos.password = nuevaPassword;
        }
        
        const idUsuario = formData.get('id_usuario');
        
        // Enviar datos
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
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalEditarUsuario'));
                modal.hide();
                
                // Recargar página
                window.location.reload();
                
                // Mostrar notificación
                mostrarNotificacion('✅ Usuario actualizado exitosamente', 'success');
            } else {
                throw new Error(data.error || 'Error al actualizar usuario');
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
    
    // ==================== FUNCIONES PARA MODALES ====================
    
    window.mostrarModalEliminar = function(id, username) {
        usuarioAEliminar = id;
        usuarioAEliminarSpan.textContent = username;
        const modal = new bootstrap.Modal(document.getElementById('modalEliminarUsuario'));
        modal.show();
    }
    
    function eliminarUsuario() {
        if (!usuarioAEliminar) return;
        
        // Mostrar carga
        const btn = document.getElementById('btn-confirmar-eliminar');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Eliminando...';
        btn.disabled = true;
        
        fetch(`/api/usuarios/${usuarioAEliminar}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Cerrar modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalEliminarUsuario'));
                modal.hide();
                
                // Recargar página
                window.location.reload();
                
                // Mostrar notificación
                mostrarNotificacion('✅ Usuario eliminado exitosamente', 'success');
                
                // Resetear variable
                usuarioAEliminar = null;
            } else {
                throw new Error(data.error || 'Error al eliminar usuario');
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
    
    // ==================== FUNCIONES AUXILIARES ====================
    
    function generarPassword() {
        const longitud = 12;
        const caracteres = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
        let password = '';
        
        for (let i = 0; i < longitud; i++) {
            password += caracteres.charAt(Math.floor(Math.random() * caracteres.length));
        }
        
        // Actualizar campo de contraseña
        const passwordInput = document.getElementById('password');
        if (passwordInput) {
            passwordInput.value = password;
            passwordInput.type = 'text';
            
            // Actualizar icono del toggle
            const toggleIcon = document.querySelector('.password-toggle i');
            if (toggleIcon) {
                toggleIcon.classList.remove('fa-eye');
                toggleIcon.classList.add('fa-eye-slash');
            }
        }
        
        // Mostrar mensaje
        mostrarNotificacion('🔑 Contraseña generada', 'success', 'La contraseña se ha generado automáticamente');
    }
    
    function mostrarNotificacion(titulo, tipo, mensaje) {
    // Eliminar notificaciones previas
    document.querySelectorAll('.notificacion-usuario').forEach(n => n.remove());
    
    const tipos = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };
    
    const alerta = document.createElement('div');
    alerta.className = `alert ${tipos[tipo]} alert-dismissible fade show notificacion-usuario`;
    alerta.style.cssText = 'position:fixed; top:80px; right:20px; z-index:1050; min-width:300px; max-width:400px';
    
    alerta.innerHTML = `
        <strong>${titulo}</strong>
        ${mensaje ? `<p class="mb-0 mt-2">${mensaje}</p>` : ''}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alerta);
    
    setTimeout(() => {
        if (alerta.parentNode) {
            alerta.remove();
        }
    }, 5000);
}
    
    // ==================== INICIALIZACIÓN ====================
    
    // Ejecutar búsqueda inicial
    buscarUsuarios();
    
    // Inicializar tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => 
        new bootstrap.Tooltip(tooltipTriggerEl, { container: 'body' })
    );
});

// ==================== FUNCIONES GLOBALES ====================

// Función para abrir modal de edición
// ==================== FUNCIONES GLOBALES ====================

// Función para abrir modal de edición
window.editarUsuario = function(id) {
    console.log(`Editando usuario ID: ${id}`);
    
    // Mostrar indicador de carga
    const modalElement = document.getElementById('modalEditarUsuario');
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    }
    
    // Cargar datos del usuario
    fetch(`/api/usuarios/${id}`)
        .then(response => {
            console.log('Respuesta status:', response.status);
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Datos recibidos:', data);
            
            // Verificar si hay error en la respuesta
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Tu API devuelve el usuario directamente, no dentro de {success: true, usuario: {...}}
            const usuario = data;
            
            // Llenar formulario
            const idUsuarioInput = document.getElementById('editar_id_usuario');
            const usernameInput = document.getElementById('editar_username');
            const rolInput = document.getElementById('editar_rol');
            const activoInput = document.getElementById('editar_activo');
            
            if (idUsuarioInput) idUsuarioInput.value = usuario.id_usuario;
            if (usernameInput) usernameInput.value = usuario.username || '';
            if (rolInput) rolInput.value = usuario.rol || '';
            
            // Manejar campo activo (puede ser boolean, integer o string)
            let activoValor = false;
            if (usuario.activo !== undefined && usuario.activo !== null) {
                activoValor = usuario.activo === true || usuario.activo === 1 || usuario.activo === '1';
            }
            
            if (activoInput) {
                activoInput.checked = activoValor;
            }
            
            // Limpiar contraseña
            const passwordInput = document.getElementById('editar_password');
            if (passwordInput) passwordInput.value = '';
            
            // Mostrar información del empleado si existe
            const infoEmpleado = document.getElementById('info-empleado');
            if (infoEmpleado) {
                if (usuario.nombre && usuario.apellido) {
                    infoEmpleado.innerHTML = `
                        <div class="alert alert-info mb-3">
                            <h6><i class="fas fa-user-tie me-2"></i>Empleado Asociado</h6>
                            <p class="mb-1"><strong>Nombre:</strong> ${usuario.nombre} ${usuario.apellido}</p>
                            ${usuario.dni ? `<p class="mb-1"><strong>DNI:</strong> ${usuario.dni}</p>` : ''}
                            ${usuario.email ? `<p class="mb-0"><strong>Email:</strong> ${usuario.email}</p>` : ''}
                        </div>
                    `;
                } else if (usuario.empleado_nombre && usuario.empleado_apellido) {
                    // Si los datos vienen con prefijo empleado_
                    infoEmpleado.innerHTML = `
                        <div class="alert alert-info mb-3">
                            <h6><i class="fas fa-user-tie me-2"></i>Empleado Asociado</h6>
                            <p class="mb-1"><strong>Nombre:</strong> ${usuario.empleado_nombre} ${usuario.empleado_apellido}</p>
                            ${usuario.dni ? `<p class="mb-1"><strong>DNI:</strong> ${usuario.dni}</p>` : ''}
                            ${usuario.email ? `<p class="mb-0"><strong>Email:</strong> ${usuario.email}</p>` : ''}
                        </div>
                    `;
                } else {
                    infoEmpleado.innerHTML = `
                        <div class="alert alert-warning mb-3">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Este usuario no está asociado a ningún empleado
                        </div>
                    `;
                }
            }
            
            // Cargar historial de login
            cargarHistorialLogin(id);
        })
        .catch(error => {
            console.error('Error cargando usuario:', error);
            
            // Cerrar modal si está abierto
            const modalInstance = bootstrap.Modal.getInstance(document.getElementById('modalEditarUsuario'));
            if (modalInstance) {
                modalInstance.hide();
            }
            
            // Mostrar alerta de error
            mostrarNotificacion('❌ Error al cargar usuario', 'error', error.message);
        });
}

// Función para cargar historial de login
function cargarHistorialLogin(idUsuario) {
    const contenedor = document.getElementById('historial-login');
    if (!contenedor) return;
    
    contenedor.innerHTML = '<p class="text-muted text-center py-3"><i class="fas fa-spinner fa-spin me-2"></i>Cargando historial...</p>';
    
    // Si no tienes endpoint específico para historial, usa datos básicos
    fetch(`/api/usuarios/${idUsuario}`)
        .then(response => response.json())
        .then(usuario => {
            let html = '';
            
            // Mostrar información básica de login
            if (usuario.ultimo_login) {
                const ultimoLogin = new Date(usuario.ultimo_login);
                const fechaStr = ultimoLogin.toLocaleDateString('es-ES');
                const horaStr = ultimoLogin.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
                
                html = `
                    <div class="alert alert-light border">
                        <h6 class="mb-2"><i class="fas fa-sign-in-alt me-2"></i>Información de Acceso</h6>
                        <p class="mb-1"><strong>Fecha Creación:</strong> ${usuario.fecha_creacion ? new Date(usuario.fecha_creacion).toLocaleDateString('es-ES') : 'No disponible'}</p>
                        <p class="mb-1"><strong>Último Login:</strong> ${fechaStr} ${horaStr}</p>
                        ${usuario.activo ? '<p class="mb-0"><strong>Estado:</strong> <span class="badge bg-success">Activo</span></p>' : '<p class="mb-0"><strong>Estado:</strong> <span class="badge bg-secondary">Inactivo</span></p>'}
                    </div>
                `;
            } else {
                html = `
                    <div class="alert alert-light border">
                        <h6 class="mb-2"><i class="fas fa-sign-in-alt me-2"></i>Información de Acceso</h6>
                        <p class="mb-1"><strong>Fecha Creación:</strong> ${usuario.fecha_creacion ? new Date(usuario.fecha_creacion).toLocaleDateString('es-ES') : 'No disponible'}</p>
                        <p class="mb-0"><strong>Último Login:</strong> <span class="text-muted">Nunca ha iniciado sesión</span></p>
                    </div>
                `;
            }
            
            contenedor.innerHTML = html;
        })
        .catch(error => {
            console.error('Error cargando historial:', error);
            contenedor.innerHTML = `
                <div class="alert alert-light border">
                    <h6 class="mb-2"><i class="fas fa-exclamation-triangle me-2"></i>Información de Acceso</h6>
                    <p class="text-muted mb-0">No se pudo cargar el historial de acceso</p>
                </div>
            `;
        });
}
// Exponer funciones al scope global
window.mostrarModalEliminar = mostrarModalEliminar;
window.editarUsuario = editarUsuario;
