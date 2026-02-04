// static/js/comunes.js - Versión mejorada

// Función para inicializar animaciones
function inicializarAnimaciones() {
    // Agregar clase de animación a elementos con data-animate
    const elementosAnimables = document.querySelectorAll('[data-animate]');
    elementosAnimables.forEach((el, index) => {
        setTimeout(() => {
            el.classList.add('animate-fade-in');
        }, index * 100);
    });
}

// Notificaciones mejoradas
function mostrarNotificacion(mensaje, tipo = 'success', duracion = 5000) {
    const tipos = {
        'success': { class: 'alert-success', icon: 'check-circle' },
        'error': { class: 'alert-danger', icon: 'exclamation-triangle' },
        'warning': { class: 'alert-warning', icon: 'exclamation-circle' },
        'info': { class: 'alert-info', icon: 'info-circle' }
    };
    
    const config = tipos[tipo] || tipos.success;
    
    // Crear contenedor si no existe
    let contenedor = document.getElementById('notificaciones-globales');
    if (!contenedor) {
        contenedor = document.createElement('div');
        contenedor.id = 'notificaciones-globales';
        contenedor.className = 'notification-container';
        document.body.appendChild(contenedor);
    }
    
    // Crear notificación
    const notificacion = document.createElement('div');
    notificacion.className = `notification alert-${tipo}`;
    notificacion.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${config.icon} fa-lg me-3 text-${tipo}"></i>
            <div class="flex-grow-1">
                <strong class="d-block mb-1">${tipo === 'success' ? 'Éxito' : 
                                             tipo === 'error' ? 'Error' : 
                                             tipo === 'warning' ? 'Advertencia' : 'Información'}</strong>
                <span class="text-muted">${mensaje}</span>
            </div>
            <button type="button" class="btn-close ms-3" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;
    
    contenedor.appendChild(notificacion);
    
    // Auto-remover después de la duración
    setTimeout(() => {
        if (notificacion.parentElement) {
            notificacion.style.opacity = '0';
            notificacion.style.transform = 'translateX(100%)';
            setTimeout(() => notificacion.remove(), 300);
        }
    }, duracion);
}

// Inicialización mejorada
document.addEventListener('DOMContentLoaded', function() {
    console.log('PetGlow Professional iniciado');
    
    // Inicializar animaciones
    inicializarAnimaciones();
    
    // Inicializar tooltips de Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Inicializar popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Agregar efectos hover a las tarjetas
    document.querySelectorAll('.stat-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Cargar datos iniciales (puedes personalizar esto)
    cargarDatosIniciales();
});

// Función para cargar datos adicionales
function cargarDatosIniciales() {
    // Puedes agregar llamadas AJAX aquí para datos en tiempo real
    console.log('Cargando datos iniciales...');
    
    // Actualizar la hora cada minuto
    setInterval(actualizarHora, 60000);
}

// Función para actualizar la hora en tiempo real
function actualizarHora() {
    const ahora = new Date();
    const horaActualizada = ahora.toLocaleTimeString('es-PE', {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    const elementosHora = document.querySelectorAll('.hora-actual');
    elementosHora.forEach(el => {
        el.textContent = horaActualizada;
    });
}

// Función para alternar sidebar en móviles
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('show');
}

// Validación de formularios mejorada
function validarFormulario(formulario) {
    let valido = true;
    const campos = formulario.querySelectorAll('[required]');
    
    campos.forEach(campo => {
        if (!campo.value.trim()) {
            campo.classList.add('is-invalid');
            valido = false;
        } else {
            campo.classList.remove('is-invalid');
            campo.classList.add('is-valid');
        }
    });
    
    return valido;
}

// Exportar funciones globales si es necesario
window.mostrarNotificacion = mostrarNotificacion;
window.validarFormulario = validarFormulario;
window.toggleSidebar = toggleSidebar;