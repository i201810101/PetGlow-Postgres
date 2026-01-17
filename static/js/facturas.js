// ============================================
// FACTURAS.JS
// Funcionalidades para módulo de facturación
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    let facturaId = null;
    let facturaTotal = 0;
    
    // Inicializar
    const initFacturas = () => {
        // Obtener datos de la factura de los meta tags
        const facturaMeta = document.querySelector('meta[name="factura-id"]');
        const totalMeta = document.querySelector('meta[name="factura-total"]');
        
        if (facturaMeta) {
            facturaId = parseInt(facturaMeta.getAttribute('content'));
        }
        
        if (totalMeta) {
            facturaTotal = parseFloat(totalMeta.getAttribute('content'));
        }
        
        console.log(`Factura ID: ${facturaId}, Total: ${facturaTotal}`);
        
        // Inicializar componentes
        initPagoCompleto();
        initPagoParcial();
        initAnularFactura();
        initImpresion();
        initValidaciones();
    };
    
    // ============================================
    // 1. PAGO COMPLETO
    // ============================================
    const initPagoCompleto = () => {
        const btnConfirmarPago = document.getElementById('btnConfirmarPago');
        if (!btnConfirmarPago) return;
        
        btnConfirmarPago.addEventListener('click', function() {
            const metodoPago = document.getElementById('metodoPagoModal').value;
            
            if (!confirmarAccion(`¿Confirmar pago completo de S/ ${facturaTotal.toFixed(2)} con ${getMetodoPagoTexto(metodoPago)}?`)) {
                return;
            }
            
            registrarPago({
                monto: facturaTotal,
                metodo_pago: metodoPago,
                es_parcial: false
            });
        });
    };
    
    // ============================================
    // 2. PAGO PARCIAL
    // ============================================
    const initPagoParcial = () => {
        const btnConfirmarPagoParcial = document.getElementById('btnConfirmarPagoParcial');
        if (!btnConfirmarPagoParcial) return;
        
        btnConfirmarPagoParcial.addEventListener('click', function() {
            const montoInput = document.getElementById('montoParcial');
            const monto = parseFloat(montoInput.value);
            const metodoPago = document.getElementById('metodoPagoParcial').value;
            
            // Validar monto
            if (isNaN(monto) || monto <= 0) {
                mostrarAlerta('error', 'Ingrese un monto válido');
                montoInput.focus();
                return;
            }
            
            if (monto > facturaTotal) {
                mostrarAlerta('error', 'El monto no puede exceder el total de la factura');
                montoInput.value = facturaTotal.toFixed(2);
                return;
            }
            
            if (!confirmarAccion(`¿Confirmar pago parcial de S/ ${monto.toFixed(2)} con ${getMetodoPagoTexto(metodoPago)}?`)) {
                return;
            }
            
            registrarPago({
                monto: monto,
                metodo_pago: metodoPago,
                es_parcial: true
            });
        });
        
        // Validar monto en tiempo real
        const montoInput = document.getElementById('montoParcial');
        if (montoInput) {
            montoInput.addEventListener('input', function() {
                let valor = parseFloat(this.value);
                if (isNaN(valor)) valor = 0;
                
                if (valor > facturaTotal) {
                    this.value = facturaTotal.toFixed(2);
                    mostrarAlerta('warning', 'Monto ajustado al máximo permitido', 2000);
                }
            });
            
            // Asegurar que el valor inicial sea el máximo
            montoInput.value = facturaTotal.toFixed(2);
        }
    };
    
    // ============================================
    // 3. ANULAR FACTURA
    // ============================================
    const initAnularFactura = () => {
        const btnAnularFactura = document.getElementById('btnAnularFactura');
        if (!btnAnularFactura) return;
        
        btnAnularFactura.addEventListener('click', function() {
            if (!confirmarAccion('¿Está seguro de anular esta factura? Esta acción no se puede deshacer.', 'warning')) {
                return;
            }
            
            anularFactura();
        });
    };
    
    // ============================================
    // 4. IMPRESIÓN
    // ============================================
    const initImpresion = () => {
        const btnImprimir = document.querySelector('.btn-imprimir');
        if (!btnImprimir) return;
        
        btnImprimir.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Agregar clase para ocultar elementos no imprimibles
            document.querySelectorAll('.no-print').forEach(el => {
                el.classList.add('d-print-none');
                el.style.display = 'none !important';
            });
            
            // Ocultar elementos Bootstrap no imprimibles
            document.querySelectorAll('.navbar, .sidebar, footer, .modal-backdrop').forEach(el => {
                el.style.display = 'none !important';
            });
            
            // Agregar estilos de impresión
            const printStyles = document.createElement('style');
            printStyles.innerHTML = `
                @media print {
                    body * {
                        visibility: hidden;
                    }
                    .comprobante-header, .comprobante-header *,
                    .comprobante-body, .comprobante-body * {
                        visibility: visible;
                    }
                    .comprobante-header {
                        position: absolute;
                        left: 0;
                        top: 0;
                        width: 100%;
                    }
                    .no-print {
                        display: none !important;
                    }
                }
            `;
            document.head.appendChild(printStyles);
            
            // Esperar un momento antes de imprimir
            setTimeout(() => {
                window.print();
                
                // Limpiar después de imprimir
                setTimeout(() => {
                    printStyles.remove();
                    document.querySelectorAll('.no-print').forEach(el => {
                        el.classList.remove('d-print-none');
                        el.style.display = '';
                    });
                    document.querySelectorAll('.navbar, .sidebar, footer, .modal-backdrop').forEach(el => {
                        el.style.display = '';
                    });
                }, 500);
            }, 300);
        });
    };
    
    // ============================================
    // 5. VALIDACIONES
    // ============================================
    const initValidaciones = () => {
        // Validar formulario de facturación (crear.html)
        const formFacturar = document.querySelector('form[action*="facturar"]');
        if (formFacturar) {
            formFacturar.addEventListener('submit', function(e) {
                const tipoComprobante = document.getElementById('tipo_comprobante');
                const metodoPago = document.getElementById('metodo_pago');
                
                if (!tipoComprobante.value || !metodoPago.value) {
                    e.preventDefault();
                    mostrarAlerta('error', 'Complete todos los campos obligatorios');
                }
                
                // Validar que si es factura, el cliente tenga DNI
                if (tipoComprobante.value === 'factura') {
                    const optionFactura = tipoComprobante.querySelector('option[value="factura"]');
                    if (optionFactura && optionFactura.disabled) {
                        e.preventDefault();
                        mostrarAlerta('error', 'No se puede emitir factura porque el cliente no tiene DNI registrado');
                    }
                }
            });
        }
    };
    
    // ============================================
    // FUNCIONES AUXILIARES
    // ============================================
    
    // Registrar pago (completo o parcial)
    const registrarPago = (datos) => {
        mostrarCargando();
        
        fetch(`/facturas/${facturaId}/pagar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(datos)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            ocultarCargando();
            
            if (data.success) {
                mostrarAlerta('success', data.message);
                setTimeout(() => {
                    location.reload();
                }, 1500);
            } else {
                mostrarAlerta('error', data.message);
            }
        })
        .catch(error => {
            ocultarCargando();
            console.error('Error:', error);
            mostrarAlerta('error', 'Error al registrar pago. Verifique la conexión.');
        });
    };
    
    // Anular factura
    const anularFactura = () => {
        mostrarCargando();
        
        fetch(`/facturas/${facturaId}/anular`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            ocultarCargando();
            
            if (data.success) {
                mostrarAlerta('success', data.message);
                setTimeout(() => {
                    location.reload();
                }, 1500);
            } else {
                mostrarAlerta('error', data.message);
            }
        })
        .catch(error => {
            ocultarCargando();
            console.error('Error:', error);
            mostrarAlerta('error', 'Error al anular factura');
        });
    };
    
    // Mostrar alerta
    const mostrarAlerta = (tipo, mensaje, tiempo = 3000) => {
        // Remover alertas anteriores
        document.querySelectorAll('.alert-flotante').forEach(el => el.remove());
        
        // Crear alerta
        const alerta = document.createElement('div');
        alerta.className = `alert alert-${tipo} alert-dismissible fade show position-fixed alert-flotante`;
        alerta.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 500px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease-out;
        `;
        
        // Icono según tipo
        const iconos = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-info-circle'
        };
        
        const icono = iconos[tipo] || 'fa-info-circle';
        
        alerta.innerHTML = `
            <i class="fas ${icono} me-2"></i>
            <strong>${tipo === 'success' ? 'Éxito' : tipo === 'error' ? 'Error' : tipo === 'warning' ? 'Advertencia' : 'Información'}</strong>
            <span class="ms-2">${mensaje}</span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alerta);
        
        // Auto-eliminar
        if (tiempo > 0) {
            setTimeout(() => {
                if (alerta.parentNode) {
                    alerta.remove();
                }
            }, tiempo);
        }
    };
    
    // Mostrar cargando
    const mostrarCargando = () => {
        let spinner = document.getElementById('cargando-spinner');
        
        if (!spinner) {
            spinner = document.createElement('div');
            spinner.id = 'cargando-spinner';
            spinner.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                    <p class="mt-3 text-muted">Procesando...</p>
                </div>
            `;
            document.body.appendChild(spinner);
        }
        
        spinner.style.display = 'block';
    };
    
    // Ocultar cargando
    const ocultarCargando = () => {
        const spinner = document.getElementById('cargando-spinner');
        if (spinner) {
            spinner.style.display = 'none';
        }
    };
    
    // Confirmar acción
    const confirmarAccion = (mensaje, tipo = 'warning') => {
        return confirm(mensaje);
    };
    
    // Obtener texto del método de pago
    const getMetodoPagoTexto = (metodo) => {
        const metodos = {
            'efectivo': 'Efectivo',
            'tarjeta': 'Tarjeta',
            'yape': 'Yape',
            'plin': 'Plin',
            'transferencia': 'Transferencia',
            'mixto': 'Pago Mixto'
        };
        return metodos[metodo] || metodo;
    };
    
    // Inicializar
    initFacturas();
});