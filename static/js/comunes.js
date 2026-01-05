// static/js/comunes.js

// Funciones comunes para toda la aplicación

// Mostrar/ocultar spinner de carga
function mostrarCargando(mostrar = true) {
    const spinner = document.getElementById('spinner-carga');
    if (spinner) {
        spinner.style.display = mostrar ? 'block' : 'none';
    }
}

// Mostrar notificación
function mostrarNotificacion(mensaje, tipo = 'success') {
    const tipos = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };
    
    const alerta = document.createElement('div');
    alerta.className = `alert ${tipos[tipo]} alert-dismissible fade show`;
    alerta.innerHTML = `
        ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const contenedor = document.getElementById('notificaciones') || document.body;
    contenedor.prepend(alerta);
    
    // Auto-remover después de 5 segundos
    setTimeout(() => {
        alerta.remove();
    }, 5000);
}

// Formatear número de teléfono
function formatearTelefono(telefono) {
    if (!telefono) return '';
    const numeros = telefono.replace(/\D/g, '');
    if (numeros.length === 9) {
        return `${numeros.slice(0, 3)}-${numeros.slice(3, 6)}-${numeros.slice(6)}`;
    }
    return telefono;
}

// Validar email
function validarEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Confirmación genérica
function confirmarAccion(mensaje, callback) {
    if (confirm(mensaje)) {
        if (typeof callback === 'function') {
            callback();
        }
    }
}

// Inicialización común
document.addEventListener('DOMContentLoaded', function() {
    console.log('PetGlow iniciado correctamente');
    
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
    
    // Aplicar formato a números de teléfono
    const telefonos = document.querySelectorAll('.telefono');
    telefonos.forEach(tel => {
        if (tel.textContent) {
            tel.textContent = formatearTelefono(tel.textContent);
        }
    });
});