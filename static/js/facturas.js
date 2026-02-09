// ============================================
// FACTURAS.JS - Versión Corregida
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
    // 1. PAGO COMPLETO - CORREGIDO
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
            
            // Usar confirmación personalizada, NO alert() nativa
            confirmarAccionPersonalizada({
                titulo: 'Confirmar Pago Completo',
                mensaje: `¿Confirmar pago de S/ ${montoPendiente.toFixed(2)} con ${getMetodoPagoTexto(metodoPago)}?`,
                tipo: 'warning',
                textoConfirmar: 'Sí, Registrar Pago',
                textoCancelar: 'Cancelar',
                onConfirm: () => {
                    registrarPago({
                        monto: montoPendiente,
                        metodo_pago: metodoPago,
                        es_parcial: false,
                        referencia: document.getElementById('referenciaPago')?.value || ''
                    });
                }
            });
        });
    };
    
    // ============================================
    // 2. PAGO PARCIAL - CORREGIDO
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
            
            // Usar confirmación personalizada
            confirmarAccionPersonalizada({
                titulo: 'Confirmar Pago Parcial',
                mensaje: `¿Confirmar pago parcial de S/ ${monto.toFixed(2)} con ${getMetodoPagoTexto(metodoPago)}?`,
                tipo: 'warning',
                textoConfirmar: 'Sí, Registrar Pago',
                textoCancelar: 'Cancelar',
                onConfirm: () => {
                    registrarPago({
                        monto: monto,
                        metodo_pago: metodoPago,
                        es_parcial: true,
                        referencia: document.getElementById('referenciaPagoParcial')?.value || ''
                    });
                }
            });
        });
        
        // Validar monto en tiempo real
        const montoInput = document.getElementById('montoParcial');
        if (montoInput) {
            montoInput.value = saldoPendiente.toFixed(2);
            
            montoInput.addEventListener('input', function() {
                let valor = parseFloat(this.value);
                if (isNaN(valor)) valor = 0;
                
                if (valor > saldoPendiente) {
                    this.value = saldoPendiente.toFixed(2);
                    mostrarAlerta('warning', 'Monto ajustado al saldo pendiente', 2000);
                }
            });
        }
    };
    
    // ============================================
    // 3. ANULAR FACTURA - COMPLETAMENTE REESCRITO
    // ============================================
    const initAnularFactura = () => {
        const btnAnularFactura = document.getElementById('btnAnularFactura');
        if (!btnAnularFactura) return;
        
        btnAnularFactura.addEventListener('click', function() {
            // Verificar si ya existe el modal
            let modalAnular = document.getElementById('modalAnularFactura');
            
            if (!modalAnular) {
                // Crear modal dinámicamente si no existe en el HTML
                crearModalAnulacion();
                modalAnular = document.getElementById('modalAnularFactura');
            }
            
            // Mostrar modal de anulación
            const modal = new bootstrap.Modal(modalAnular);
            modal.show();
            
            // Configurar botón de confirmación dentro del modal
            const btnConfirmarAnulacion = document.getElementById('btnConfirmarAnulacion');
            if (btnConfirmarAnulacion) {
                // Remover event listeners anteriores
                const nuevoBtn = btnConfirmarAnulacion.cloneNode(true);
                btnConfirmarAnulacion.parentNode.replaceChild(nuevoBtn, btnConfirmarAnulacion);
                
                // Agregar nuevo event listener
                nuevoBtn.addEventListener('click', function() {
                    const motivoInput = document.getElementById('motivoAnulacion');
                    const motivo = motivoInput ? motivoInput.value.trim() : '';
                    
                    // Usar confirmación personalizada
                    confirmarAccionPersonalizada({
                        titulo: 'Confirmar Anulación',
                        mensaje: '¿Está seguro de anular esta factura? Esta acción no se puede deshacer.',
                        tipo: 'error',
                        textoConfirmar: 'Sí, Anular',
                        textoCancelar: 'Cancelar',
                        onConfirm: () => {
                            modal.hide();
                            anularFactura(motivo);
                        }
                    });
                });
            }
        });
    };
    
    // Función para crear modal de anulación dinámicamente
    const crearModalAnulacion = () => {
        const modalHTML = `
        <div class="modal fade" id="modalAnularFactura" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-exclamation-triangle me-2"></i>Confirmar Anulación
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-warning">
                            <i class="fas fa-exclamation-circle me-2"></i>
                            <strong>¡Atención!</strong> Esta acción no se puede deshacer.
                        </div>
                        
                        <p>¿Está seguro de anular la factura <strong>${facturaId}</strong>?</p>
                        
                        <div class="mb-3">
                            <label for="motivoAnulacion" class="form-label">Motivo de anulación (opcional):</label>
                            <textarea class="form-control" id="motivoAnulacion" rows="3" 
                                      placeholder="Ej: Error en los datos, cliente canceló, etc."></textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times me-1"></i>Cancelar
                        </button>
                        <button type="button" class="btn btn-danger" id="btnConfirmarAnulacion">
                            <i class="fas fa-ban me-1"></i>Sí, Anular Factura
                        </button>
                    </div>
                </div>
            </div>
        </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    };
    
    // ============================================
    // 4. IMPRESIÓN
    // ============================================
    const initImpresion = () => {
        const btnImprimir = document.querySelector('.btn-imprimir');
        if (!btnImprimir) return;
        
        btnImprimir.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Guardar estilos originales
            const elementosOriginales = [];
            document.querySelectorAll('.no-print').forEach(el => {
                elementosOriginales.push({
                    element: el,
                    display: el.style.display
                });
                el.style.display = 'none';
            });
            
            // Imprimir
            window.print();
            
            // Restaurar después de un tiempo
            setTimeout(() => {
                elementosOriginales.forEach(item => {
                    item.element.style.display = item.display;
                });
            }, 500);
        });
    };
    
    // ============================================
    // 5. CALCULADORA DE PAGOS
    // ============================================
    const initCalculadora = () => {
        const btnCalculadora = document.getElementById('btnCalculadora');
        if (btnCalculadora) {
            btnCalculadora.addEventListener('click', mostrarCalculadora);
        }
    };
    
    const mostrarCalculadora = () => {
        const montoInput = document.getElementById('montoParcial');
        if (!montoInput) return;
        
        // Crear modal de calculadora
        const modalHTML = `
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
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Agregar al DOM si no existe
        if (!document.getElementById('modalCalculadora')) {
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }
        
        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('modalCalculadora'));
        modal.show();
        
        // Configurar eventos de la calculadora
        configurarCalculadora(modal, montoInput);
    };
    
    const configurarCalculadora = (modal, montoInput) => {
        const display = document.getElementById('displayCalculadora');
        if (!display) return;
        
        // Botones numéricos
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
        
        // Botón limpiar
        document.querySelector('#modalCalculadora [data-clear]').addEventListener('click', function() {
            display.value = '0';
        });
        
        // Botón retroceso
        document.querySelector('#modalCalculadora [data-back]').addEventListener('click', function() {
            if (display.value.length > 1) {
                display.value = display.value.slice(0, -1);
            } else {
                display.value = '0';
            }
        });
        
        // Botón máximo
        document.querySelector('#modalCalculadora [data-max]').addEventListener('click', function() {
            display.value = saldoPendiente.toFixed(2);
        });
        
        // Botón aplicar
        document.querySelector('#modalCalculadora [data-apply]').addEventListener('click', function() {
            const valor = parseFloat(display.value) || 0;
            montoInput.value = valor.toFixed(2);
            modal.hide();
        });
    };
    
    // ============================================
    // 6. EVENT LISTENERS ADICIONALES
    // ============================================
    const initEventListeners = () => {
        // Actualizar estado de botones según saldo
        actualizarEstadoBotones();
        
        // Copiar número de factura
        const btnCopiarFactura = document.getElementById('btnCopiarFactura');
        if (btnCopiarFactura) {
            btnCopiarFactura.addEventListener('click', copiarNumeroFactura);
        }
    };
    
    const actualizarEstadoBotones = () => {
        if (saldoPendiente <= 0) {
            document.querySelectorAll('.btn-pagar').forEach(btn => {
                btn.disabled = true;
                btn.classList.add('disabled');
            });
        }
    };
    
    const copiarNumeroFactura = () => {
        const numeroFactura = document.querySelector('.numero-factura')?.textContent || facturaId;
        navigator.clipboard.writeText(numeroFactura.toString())
            .then(() => mostrarAlerta('success', 'Número de factura copiado', 2000))
            .catch(() => mostrarAlerta('error', 'Error al copiar'));
    };
    
    // ============================================
    // 7. VALIDACIONES
    // ============================================
    const initValidaciones = () => {
        const formFacturar = document.querySelector('form[action*="facturar"]');
        if (formFacturar) {
            formFacturar.addEventListener('submit', validarFormularioFacturacion);
        }
    };
    
    const validarFormularioFacturacion = (e) => {
        const tipoComprobante = document.getElementById('tipo_comprobante');
        const metodoPago = document.getElementById('metodo_pago');
        
        if (!tipoComprobante || !tipoComprobante.value) {
            e.preventDefault();
            mostrarAlerta('error', 'Seleccione el tipo de comprobante');
            return;
        }
        
        if (!metodoPago || !metodoPago.value) {
            e.preventDefault();
            mostrarAlerta('error', 'Seleccione el método de pago');
            return;
        }
    };
    
    // ============================================
    // FUNCIONES AUXILIARES CORREGIDAS
    // ============================================
    
    // CONFIRMACIÓN PERSONALIZADA (sin alert() nativa)
    const confirmarAccionPersonalizada = (opciones) => {
        // Si SweetAlert2 está disponible, usarlo
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: opciones.titulo || 'Confirmar',
                text: opciones.mensaje,
                icon: opciones.tipo || 'warning',
                showCancelButton: true,
                confirmButtonText: opciones.textoConfirmar || 'Confirmar',
                cancelButtonText: opciones.textoCancelar || 'Cancelar',
                confirmButtonColor: '#198754',
                cancelButtonColor: '#dc3545',
                reverseButtons: true
            }).then((result) => {
                if (result.isConfirmed && opciones.onConfirm) {
                    opciones.onConfirm();
                }
            });
        } else {
            // Si no hay SweetAlert, crear nuestro propio modal de confirmación
            crearModalConfirmacionPersonalizada(opciones);
        }
    };
    
    // Crear modal de confirmación personalizada
    const crearModalConfirmacionPersonalizada = (opciones) => {
        const modalId = 'modalConfirmacionPersonalizada';
        let modal = document.getElementById(modalId);
        
        // Si ya existe, eliminarlo
        if (modal) modal.remove();
        
        // Crear modal
        const modalHTML = `
            <div class="modal fade" id="${modalId}" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-${opciones.tipo === 'error' ? 'danger' : opciones.tipo === 'warning' ? 'warning' : 'primary'} text-white">
                            <h5 class="modal-title">
                                <i class="fas fa-question-circle me-2"></i>${opciones.titulo || 'Confirmar'}
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${opciones.mensaje}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" id="btnCancelarConfirmacion">
                                ${opciones.textoCancelar || 'Cancelar'}
                            </button>
                            <button type="button" class="btn btn-${opciones.tipo === 'error' ? 'danger' : opciones.tipo === 'warning' ? 'warning' : 'primary'}" id="btnConfirmarAccion">
                                ${opciones.textoConfirmar || 'Confirmar'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Mostrar modal
        modal = document.getElementById(modalId);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Configurar botones
        document.getElementById('btnConfirmarAccion').addEventListener('click', function() {
            bsModal.hide();
            if (opciones.onConfirm) opciones.onConfirm();
        });
        
        document.getElementById('btnCancelarConfirmacion').addEventListener('click', function() {
            bsModal.hide();
        });
        
        // Auto-eliminar al cerrar
        modal.addEventListener('hidden.bs.modal', function() {
            setTimeout(() => {
                if (modal && modal.parentNode) {
                    modal.remove();
                }
            }, 300);
        });
    };
    
    // Registrar pago
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
                mostrarAlerta('success', data.message || 'Pago registrado correctamente');
                setTimeout(() => {
                    location.reload();
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
        
        const datos = {};
        if (motivo.trim()) {
            datos.motivo = motivo.trim();
        }
        
        fetch(`/facturas/${facturaId}/anular`, {
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
                mostrarAlerta('success', data.message || 'Factura anulada correctamente');
                setTimeout(() => {
                    location.reload();
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
    
    // Mostrar alerta (sin cambios)
    const mostrarAlerta = (tipo, mensaje, tiempo = 4000) => {
        // ... (mantener el mismo código de alerta que ya tenías)
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
    };
    
    // Mostrar cargando
    const mostrarCargando = () => {
        const overlay = document.createElement('div');
        overlay.id = 'cargando-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 99999;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(2px);
        `;
        
        overlay.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-light" style="width: 3rem; height: 3rem;"></div>
                <p class="mt-3 text-white">Procesando...</p>
            </div>
        `;
        
        document.body.appendChild(overlay);
    };
    
    // Ocultar cargando
    const ocultarCargando = () => {
        const overlay = document.getElementById('cargando-overlay');
        if (overlay) {
            overlay.remove();
        }
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
