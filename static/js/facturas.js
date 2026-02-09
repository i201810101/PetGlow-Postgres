// ============================================
// FACTURAS.JS - Versión Mejorada
// Funcionalidades para módulo de facturación
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    let facturaId = null;
    let facturaTotal = 0;
    let saldoPendiente = 0;
    
    // Inicializar
    const initFacturas = () => {
        // Obtener datos de la factura de los meta tags
        const facturaMeta = document.querySelector('meta[name="factura-id"]');
        const totalMeta = document.querySelector('meta[name="factura-total"]');
        const saldoMeta = document.querySelector('meta[name="saldo-pendiente"]');
        
        if (facturaMeta) {
            facturaId = parseInt(facturaMeta.getAttribute('content'));
        }
        
        if (totalMeta) {
            facturaTotal = parseFloat(totalMeta.getAttribute('content'));
        }
        
        if (saldoMeta) {
            saldoPendiente = parseFloat(saldoMeta.getAttribute('content')) || facturaTotal;
        } else {
            saldoPendiente = facturaTotal;
        }
        
        console.log(`Factura ID: ${facturaId}, Total: ${facturaTotal}, Saldo: ${saldoPendiente}`);
        
        // Inicializar componentes
        initPagoCompleto();
        initPagoParcial();
        initAnularFactura();
        initImpresion();
        initValidaciones();
        initCalculadora();
        initEventListeners();
    };
    
    // ============================================
    // 1. PAGO COMPLETO
    // ============================================
    const initPagoCompleto = () => {
        const btnConfirmarPago = document.getElementById('btnConfirmarPago');
        if (!btnConfirmarPago) return;
        
        btnConfirmarPago.addEventListener('click', function() {
            const metodoPago = document.getElementById('metodoPagoModal').value;
            const montoPendiente = Math.min(facturaTotal, saldoPendiente);
            
            if (montoPendiente <= 0) {
                mostrarAlerta('warning', 'La factura ya está pagada completamente');
                return;
            }
            
            if (!confirmarAccion(`¿Confirmar pago de S/ ${montoPendiente.toFixed(2)} con ${getMetodoPagoTexto(metodoPago)}?`)) {
                return;
            }
            
            registrarPago({
                monto: montoPendiente,
                metodo_pago: metodoPago,
                es_parcial: false,
                referencia: document.getElementById('referenciaPago')?.value || ''
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
            
            if (monto > saldoPendiente) {
                mostrarAlerta('error', `El monto no puede exceder el saldo pendiente (S/ ${saldoPendiente.toFixed(2)})`);
                montoInput.value = saldoPendiente.toFixed(2);
                return;
            }
            
            if (!confirmarAccion(`¿Confirmar pago parcial de S/ ${monto.toFixed(2)} con ${getMetodoPagoTexto(metodoPago)}?`)) {
                return;
            }
            
            registrarPago({
                monto: monto,
                metodo_pago: metodoPago,
                es_parcial: true,
                referencia: document.getElementById('referenciaPagoParcial')?.value || ''
            });
        });
        
        // Validar monto en tiempo real
        const montoInput = document.getElementById('montoParcial');
        if (montoInput) {
            // Establecer máximo inicial
            montoInput.max = saldoPendiente;
            montoInput.value = saldoPendiente.toFixed(2);
            
            montoInput.addEventListener('input', function() {
                let valor = parseFloat(this.value);
                if (isNaN(valor)) valor = 0;
                
                if (valor > saldoPendiente) {
                    this.value = saldoPendiente.toFixed(2);
                    mostrarAlerta('warning', 'Monto ajustado al saldo pendiente', 2000);
                }
                
                // Formatear con 2 decimales
                if (this.value.includes('.')) {
                    const decimales = this.value.split('.')[1];
                    if (decimales && decimales.length > 2) {
                        this.value = parseFloat(this.value).toFixed(2);
                    }
                }
            });
            
            // Permitir usar flechas para ajustar monto
            montoInput.addEventListener('keydown', function(e) {
                if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                    e.preventDefault();
                    let valor = parseFloat(this.value) || 0;
                    const paso = e.shiftKey ? 10 : 1;
                    
                    if (e.key === 'ArrowUp') {
                        valor += paso;
                    } else {
                        valor -= paso;
                    }
                    
                    if (valor < 0) valor = 0;
                    if (valor > saldoPendiente) valor = saldoPendiente;
                    
                    this.value = valor.toFixed(2);
                }
            });
        }
    };
    
    // ============================================
    // 3. ANULAR FACTURA
    // ============================================
    const initAnularFactura = () => {
        const btnAnularFactura = document.getElementById('btnAnularFactura');
        if (!btnAnularFactura) return;
        
        btnAnularFactura.addEventListener('click', function() {
            const motivoInput = document.getElementById('motivoAnulacion');
            let motivo = '';
            
            // Si hay campo de motivo, pedirlo
            if (motivoInput) {
                motivo = motivoInput.value.trim();
                if (!motivo) {
                    mostrarAlerta('error', 'Debe especificar el motivo de anulación');
                    motivoInput.focus();
                    return;
                }
                
                if (!confirmarAccion(`¿Está seguro de anular esta factura? Motivo: "${motivo}"`)) {
                    return;
                }
            } else {
                if (!confirmarAccion('¿Está seguro de anular esta factura? Esta acción no se puede deshacer.')) {
                    return;
                }
            }
            
            anularFactura(motivo);
        });
    };
    
    // ============================================
    // 4. IMPRESIÓN MEJORADA
    // ============================================
    const initImpresion = () => {
        const btnImprimir = document.querySelector('.btn-imprimir');
        if (!btnImprimir) return;
        
        btnImprimir.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Agregar clase de impresión al body
            document.body.classList.add('modo-impresion');
            
            // Guardar estilos originales
            const elementosOriginales = [];
            document.querySelectorAll('.no-print').forEach(el => {
                elementosOriginales.push({
                    element: el,
                    display: el.style.display
                });
                el.style.display = 'none';
            });
            
            // Ocultar elementos Bootstrap
            document.querySelectorAll('.modal-backdrop').forEach(el => {
                el.style.display = 'none';
            });
            
            // Agregar estilos de impresión temporales
            const printStyles = document.createElement('style');
            printStyles.id = 'print-styles-temp';
            printStyles.innerHTML = `
                @media print {
                    @page {
                        margin: 0.5cm;
                    }
                    body.modo-impresion {
                        font-size: 12pt !important;
                    }
                    .comprobante-impresion {
                        border: 1px solid #000 !important;
                        padding: 20px !important;
                        margin: 0 auto !important;
                        max-width: 21cm !important;
                    }
                    .no-print, .no-print * {
                        display: none !important;
                    }
                    .text-print-only {
                        display: block !important;
                    }
                    .table-print {
                        border-collapse: collapse !important;
                        width: 100% !important;
                    }
                    .table-print th, .table-print td {
                        border: 1px solid #000 !important;
                        padding: 4px !important;
                    }
                }
                .text-print-only {
                    display: none;
                }
            `;
            document.head.appendChild(printStyles);
            
            // Mostrar mensaje de impresión
            const mensajePrint = document.createElement('div');
            mensajePrint.className = 'alert alert-info text-center text-print-only';
            mensajePrint.innerHTML = `<small>Impreso el ${new Date().toLocaleDateString()} a las ${new Date().toLocaleTimeString()}</small>`;
            document.querySelector('.comprobante-impresion')?.appendChild(mensajePrint);
            
            // Imprimir después de un breve retraso
            setTimeout(() => {
                window.print();
                
                // Restaurar después de imprimir
                setTimeout(() => {
                    // Restaurar estilos originales
                    elementosOriginales.forEach(item => {
                        item.element.style.display = item.display;
                    });
                    
                    // Remover estilos temporales
                    printStyles.remove();
                    
                    // Remover mensaje de impresión
                    mensajePrint.remove();
                    
                    // Remover clase del body
                    document.body.classList.remove('modo-impresion');
                    
                    // Restaurar modales
                    document.querySelectorAll('.modal-backdrop').forEach(el => {
                        el.style.display = '';
                    });
                    
                    mostrarAlerta('info', 'Impresión completada', 2000);
                }, 500);
            }, 300);
        });
    };
    
    // ============================================
    // 5. VALIDACIONES MEJORADAS
    // ============================================
    const initValidaciones = () => {
        // Validar formulario de facturación (crear.html)
        const formFacturar = document.querySelector('form[action*="facturar"]');
        if (formFacturar) {
            formFacturar.addEventListener('submit', function(e) {
                const tipoComprobante = document.getElementById('tipo_comprobante');
                const metodoPago = document.getElementById('metodo_pago');
                let hayErrores = false;
                
                // Validar campos obligatorios
                if (!tipoComprobante || !tipoComprobante.value) {
                    mostrarAlerta('error', 'Seleccione el tipo de comprobante');
                    hayErrores = true;
                }
                
                if (!metodoPago || !metodoPago.value) {
                    mostrarAlerta('error', 'Seleccione el método de pago');
                    hayErrores = true;
                }
                
                // Validar que si es factura, el cliente tenga DNI
                if (tipoComprobante && tipoComprobante.value === 'factura') {
                    const clienteDNI = document.querySelector('input[name="cliente_dni"]')?.value || 
                                     document.querySelector('#cliente_dni')?.value;
                    if (!clienteDNI || clienteDNI.trim().length !== 8) {
                        mostrarAlerta('error', 'Para emitir factura, el cliente debe tener un DNI válido (8 dígitos)');
                        hayErrores = true;
                    }
                }
                
                if (hayErrores) {
                    e.preventDefault();
                }
            });
        }
    };
    
    // ============================================
    // 6. CALCULADORA DE PAGOS
    // ============================================
    const initCalculadora = () => {
        const btnCalculadora = document.getElementById('btnCalculadora');
        if (!btnCalculadora) return;
        
        btnCalculadora.addEventListener('click', function() {
            const montoInput = document.getElementById('montoParcial');
            if (!montoInput) return;
            
            // Crear interfaz de calculadora
            const calculadoraHTML = `
                <div class="modal fade" id="modalCalculadora" tabindex="-1">
                    <div class="modal-dialog modal-sm">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Calculadora</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="mb-3">
                                    <input type="text" class="form-control text-end fs-4" id="displayCalculadora" readonly value="${montoInput.value}">
                                </div>
                                <div class="row g-2">
                                    <div class="col-3"><button class="btn btn-light w-100" data-val="7">7</button></div>
                                    <div class="col-3"><button class="btn btn-light w-100" data-val="8">8</button></div>
                                    <div class="col-3"><button class="btn btn-light w-100" data-val="9">9</button></div>
                                    <div class="col-3"><button class="btn btn-danger w-100" data-clear>C</button></div>
                                    <div class="col-3"><button class="btn btn-light w-100" data-val="4">4</button></div>
                                    <div class="col-3"><button class="btn btn-light w-100" data-val="5">5</button></div>
                                    <div class="col-3"><button class="btn btn-light w-100" data-val="6">6</button></div>
                                    <div class="col-3"><button class="btn btn-warning w-100" data-back>⌫</button></div>
                                    <div class="col-3"><button class="btn btn-light w-100" data-val="1">1</button></div>
                                    <div class="col-3"><button class="btn btn-light w-100" data-val="2">2</button></div>
                                    <div class="col-3"><button class="btn btn-light w-100" data-val="3">3</button></div>
                                    <div class="col-3"><button class="btn btn-success w-100" data-apply>Aplicar</button></div>
                                    <div class="col-6"><button class="btn btn-light w-100" data-val="0">0</button></div>
                                    <div class="col-3"><button class="btn btn-light w-100" data-val=".">.</button></div>
                                    <div class="col-3"><button class="btn btn-primary w-100" data-max>Máx</button></div>
                                </div>
                                <div class="mt-3">
                                    <button class="btn btn-outline-secondary w-100 mb-2" data-quick="10">S/ 10</button>
                                    <button class="btn btn-outline-secondary w-100 mb-2" data-quick="20">S/ 20</button>
                                    <button class="btn btn-outline-secondary w-100 mb-2" data-quick="50">S/ 50</button>
                                    <button class="btn btn-outline-secondary w-100" data-quick="100">S/ 100</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Agregar al DOM si no existe
            if (!document.getElementById('modalCalculadora')) {
                document.body.insertAdjacentHTML('beforeend', calculadoraHTML);
            }
            
            // Mostrar modal
            const modal = new bootstrap.Modal(document.getElementById('modalCalculadora'));
            modal.show();
            
            // Configurar eventos
            const display = document.getElementById('displayCalculadora');
            
            document.querySelectorAll('#modalCalculadora [data-val]').forEach(btn => {
                btn.addEventListener('click', function() {
                    const val = this.getAttribute('data-val');
                    let current = display.value;
                    
                    if (val === '.' && current.includes('.')) return;
                    
                    if (current === '0' && val !== '.') {
                        current = '';
                    }
                    
                    display.value = current + val;
                });
            });
            
            document.querySelector('#modalCalculadora [data-clear]').addEventListener('click', function() {
                display.value = '0';
            });
            
            document.querySelector('#modalCalculadora [data-back]').addEventListener('click', function() {
                if (display.value.length > 1) {
                    display.value = display.value.slice(0, -1);
                } else {
                    display.value = '0';
                }
            });
            
            document.querySelector('#modalCalculadora [data-max]').addEventListener('click', function() {
                display.value = saldoPendiente.toFixed(2);
            });
            
            document.querySelectorAll('#modalCalculadora [data-quick]').forEach(btn => {
                btn.addEventListener('click', function() {
                    const val = parseFloat(this.getAttribute('data-quick'));
                    let current = parseFloat(display.value) || 0;
                    const newVal = current + val;
                    
                    if (newVal > saldoPendiente) {
                        display.value = saldoPendiente.toFixed(2);
                        mostrarAlerta('warning', 'Monto ajustado al saldo pendiente', 2000);
                    } else {
                        display.value = newVal.toFixed(2);
                    }
                });
            });
            
            document.querySelector('#modalCalculadora [data-apply]').addEventListener('click', function() {
                montoInput.value = parseFloat(display.value).toFixed(2);
                modal.hide();
            });
            
            // Limpiar al cerrar
            document.getElementById('modalCalculadora').addEventListener('hidden.bs.modal', function() {
                this.remove();
            });
        });
    };
    
    // ============================================
    // 7. EVENT LISTENERS ADICIONALES
    // ============================================
    const initEventListeners = () => {
        // Actualizar saldo pendiente en tiempo real
        const saldoElement = document.getElementById('saldoPendiente');
        if (saldoElement) {
            const actualizarSaldo = () => {
                saldoElement.textContent = `S/ ${saldoPendiente.toFixed(2)}`;
                if (saldoPendiente <= 0) {
                    saldoElement.classList.add('text-success', 'fw-bold');
                    document.querySelectorAll('.btn-pagar').forEach(btn => {
                        btn.disabled = true;
                        btn.classList.add('disabled');
                    });
                }
            };
            actualizarSaldo();
        }
        
        // Copiar número de factura
        const btnCopiarFactura = document.getElementById('btnCopiarFactura');
        if (btnCopiarFactura) {
            btnCopiarFactura.addEventListener('click', function() {
                const numeroFactura = document.querySelector('.numero-factura')?.textContent || facturaId;
                navigator.clipboard.writeText(numeroFactura.toString())
                    .then(() => mostrarAlerta('success', 'Número de factura copiado', 2000))
                    .catch(() => mostrarAlerta('error', 'Error al copiar'));
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
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
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
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else {
                        location.reload();
                    }
                }, 1500);
            } else {
                mostrarAlerta('error', data.message || 'Error al registrar pago');
            }
        })
        .catch(error => {
            ocultarCargando();
            console.error('Error:', error);
            mostrarAlerta('error', 'Error al registrar pago. Verifique la conexión.');
        });
    };
    
    // Anular factura
    const anularFactura = (motivo = '') => {
        mostrarCargando();
        
        const datos = motivo ? { motivo: motivo } : {};
        
        fetch(`/facturas/${facturaId}/anular`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
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
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    } else {
                        location.reload();
                    }
                }, 1500);
            } else {
                mostrarAlerta('error', data.message || 'Error al anular factura');
            }
        })
        .catch(error => {
            ocultarCargando();
            console.error('Error:', error);
            mostrarAlerta('error', 'Error al anular factura. Verifique la conexión.');
        });
    };
    
    // Mostrar alerta mejorada
    const mostrarAlerta = (tipo, mensaje, tiempo = 4000) => {
        // Remover alertas anteriores del mismo tipo
        document.querySelectorAll(`.alert-flotante.alert-${tipo}`).forEach(el => {
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 300);
        });
        
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
            animation: slideInRight 0.3s ease-out;
            border-left: 4px solid;
            border-left-color: ${tipo === 'success' ? '#198754' : tipo === 'error' ? '#dc3545' : tipo === 'warning' ? '#ffc107' : '#0dcaf0'};
        `;
        
        // Icono según tipo
        const iconos = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-info-circle'
        };
        
        const titulos = {
            'success': 'Éxito',
            'error': 'Error',
            'warning': 'Advertencia',
            'info': 'Información'
        };
        
        const icono = iconos[tipo] || 'fa-info-circle';
        const titulo = titulos[tipo] || 'Información';
        
        alerta.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas ${icono} fa-2x me-3"></i>
                <div class="flex-grow-1">
                    <strong>${titulo}</strong>
                    <div class="small">${mensaje}</div>
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.appendChild(alerta);
        
        // Auto-eliminar
        if (tiempo > 0) {
            setTimeout(() => {
                if (alerta.parentNode) {
                    alerta.style.opacity = '0';
                    alerta.style.transition = 'opacity 0.3s';
                    setTimeout(() => {
                        if (alerta.parentNode) alerta.remove();
                    }, 300);
                }
            }, tiempo);
        }
        
        // Agregar animación si no existe
        if (!document.querySelector('#alert-animation')) {
            const style = document.createElement('style');
            style.id = 'alert-animation';
            style.innerHTML = `
                @keyframes slideInRight {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
            `;
            document.head.appendChild(style);
        }
    };
    
    // Mostrar cargando mejorado
    const mostrarCargando = () => {
        let overlay = document.getElementById('cargando-overlay');
        
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'cargando-overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 99999;
                display: flex;
                align-items: center;
                justify-content: center;
                backdrop-filter: blur(2px);
            `;
            
            overlay.innerHTML = `
                <div class="bg-white rounded-3 p-4 shadow-lg text-center" style="min-width: 200px;">
                    <div class="spinner-border text-primary mb-3" style="width: 3rem; height: 3rem;"></div>
                    <p class="mb-1 fw-bold">Procesando</p>
                    <p class="small text-muted">Por favor espere...</p>
                </div>
            `;
            
            document.body.appendChild(overlay);
            document.body.style.overflow = 'hidden';
        } else {
            overlay.style.display = 'flex';
        }
    };
    
    // Ocultar cargando
    const ocultarCargando = () => {
        const overlay = document.getElementById('cargando-overlay');
        if (overlay) {
            overlay.style.display = 'none';
            document.body.style.overflow = '';
        }
    };
    
    // Confirmar acción con SweetAlert2 (si está disponible) o confirm nativo
    const confirmarAccion = (mensaje, tipo = 'warning') => {
        if (typeof Swal !== 'undefined') {
            return Swal.fire({
                title: 'Confirmar',
                text: mensaje,
                icon: tipo,
                showCancelButton: true,
                confirmButtonText: 'Sí, confirmar',
                cancelButtonText: 'Cancelar',
                confirmButtonColor: '#198754',
                cancelButtonColor: '#dc3545',
                reverseButtons: true
            }).then((result) => result.isConfirmed);
        } else {
            return confirm(mensaje);
        }
    };
    
    // Obtener texto del método de pago
    const getMetodoPagoTexto = (metodo) => {
        const metodos = {
            'efectivo': 'Efectivo',
            'tarjeta': 'Tarjeta',
            'yape': 'Yape',
            'plin': 'Plin',
            'transferencia': 'Transferencia Bancaria',
            'mixto': 'Pago Mixto',
            'credito': 'Crédito'
        };
        return metodos[metodo] || metodo;
    };
    
    // Inicializar
    initFacturas();
});

// Funciones globales accesibles desde otros scripts
window.Facturas = {
    actualizarSaldo: function(nuevoSaldo) {
        const saldoElement = document.getElementById('saldoPendiente');
        if (saldoElement) {
            saldoElement.textContent = `S/ ${parseFloat(nuevoSaldo).toFixed(2)}`;
        }
    },
    
    recargarDatos: function() {
        location.reload();
    }
};
