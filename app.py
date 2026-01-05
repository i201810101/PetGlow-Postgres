from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from datetime import datetime
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

# Cargar variables de entorno
load_dotenv()

# Inicializar la aplicación
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'petglow-secret-key-2025')

# Configuración de la base de datos MySQL
def get_db_connection():
    """Obtener conexión a MySQL"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            database=os.getenv('DB_NAME', 'petglowbd'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '')
        )
        return connection
    except Error as e:
        print(f"❌ Error conectando a MySQL: {e}")
        return None

# ================= RUTAS =================

@app.route('/')
def index():
    """Página principal - Redirige directamente al dashboard"""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Panel de control principal"""
    # Obtener estadísticas
    conn = get_db_connection()
    stats = {
        'total_clientes': 15,  # Valores por defecto demo
        'total_mascotas': 42,
        'reservas_hoy': 5,
        'ventas_hoy': 850.0
    }
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Verificar si las tablas existen
            cursor.execute("SHOW TABLES LIKE 'clientes'")
            if cursor.fetchone():
                # Total clientes
                cursor.execute("SELECT COUNT(*) as total FROM clientes")
                result = cursor.fetchone()
                stats['total_clientes'] = result['total'] if result else 15
            
            cursor.execute("SHOW TABLES LIKE 'mascotas'")
            if cursor.fetchone():
                # Total mascotas
                cursor.execute("SELECT COUNT(*) as total FROM mascotas")
                result = cursor.fetchone()
                stats['total_mascotas'] = result['total'] if result else 42
            
            cursor.execute("SHOW TABLES LIKE 'reservas'")
            if cursor.fetchone():
                # Reservas de hoy
                cursor.execute("SELECT COUNT(*) as total FROM reservas WHERE DATE(fecha_reserva) = CURDATE()")
                result = cursor.fetchone()
                stats['reservas_hoy'] = result['total'] if result else 5
            
            cursor.execute("SHOW TABLES LIKE 'facturas'")
            if cursor.fetchone():
                # Ventas de hoy
                cursor.execute("""
                    SELECT COALESCE(SUM(total), 0) as total 
                    FROM facturas 
                    WHERE DATE(fecha_emision) = CURDATE() AND estado = 'pagada'
                """)
                result = cursor.fetchone()
                stats['ventas_hoy'] = float(result['total']) if result and result['total'] else 850.0
            
            cursor.close()
            
        except Error as e:
            print(f"⚠️  Error obteniendo estadísticas: {e}")
            # Mantener valores demo
        finally:
            conn.close()
    
    return render_template('dashboard.html', **stats)

@app.route('/clientes')
def clientes():
    """Listar clientes"""
    conn = get_db_connection()
    clientes_list = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM clientes ORDER BY fecha_registro DESC LIMIT 50")
            clientes_list = cursor.fetchall()
            cursor.close()
        except Error as e:
            flash(f'Error obteniendo clientes: {e}', 'danger')
        finally:
            conn.close()
    else:
        # Datos demo
        clientes_list = [
            {'id_cliente': 1, 'nombre': 'Juan', 'apellido': 'Pérez', 'telefono': '555-1234', 'email': 'juan@email.com', 'fecha_registro': datetime.now()},
            {'id_cliente': 2, 'nombre': 'María', 'apellido': 'García', 'telefono': '555-5678', 'email': 'maria@email.com', 'fecha_registro': datetime.now()},
            {'id_cliente': 3, 'nombre': 'Carlos', 'apellido': 'Ruiz', 'telefono': '555-9012', 'email': 'carlos@email.com', 'fecha_registro': datetime.now()}
        ]
    
    return render_template('clientes/listar.html', clientes=clientes_list)

@app.route('/clientes/crear', methods=['GET', 'POST'])
def crear_cliente():
    """Crear nuevo cliente"""
    if request.method == 'POST':
        # Obtener datos del formulario
        dni = request.form.get('dni', '').strip()
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        telefono = request.form.get('telefono', '').strip()
        email = request.form.get('email', '').strip()
        
        if not nombre or not telefono:
            flash('Nombre y teléfono son obligatorios.', 'danger')
            return render_template('clientes/crear.html')
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO clientes (dni, nombre, apellido, telefono, email)
                    VALUES (%s, %s, %s, %s, %s)
                """, (dni or None, nombre, apellido, telefono, email or None))
                conn.commit()
                
                flash(f'Cliente {nombre} {apellido} creado exitosamente.', 'success')
                return redirect(url_for('clientes'))
                
            except Error as e:
                flash(f'Error creando cliente: {e}', 'danger')
            finally:
                cursor.close()
                conn.close()
        else:
            flash('No hay conexión a la base de datos. Cliente guardado en modo demo.', 'warning')
            return redirect(url_for('clientes'))
    
    return render_template('clientes/crear.html')

# Añade estas rutas después de la ruta crear_cliente en app.py

@app.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    """Editar cliente existente"""
    conn = get_db_connection()
    cliente = None
    
    if not conn:
        flash('No hay conexión a la base de datos.', 'danger')
        return redirect(url_for('clientes'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'POST':
            # Obtener datos del formulario
            dni = request.form.get('dni', '').strip()
            nombre = request.form.get('nombre', '').strip()
            apellido = request.form.get('apellido', '').strip()
            telefono = request.form.get('telefono', '').strip()
            email = request.form.get('email', '').strip()
            
            if not nombre or not telefono:
                flash('Nombre y teléfono son obligatorios.', 'danger')
                return redirect(url_for('editar_cliente', id=id))
            
            # Actualizar cliente
            cursor.execute("""
                UPDATE clientes 
                SET dni = %s, nombre = %s, apellido = %s, 
                    telefono = %s, email = %s
                WHERE id_cliente = %s
            """, (dni or None, nombre, apellido, telefono, email or None, id))
            conn.commit()
            
            flash(f'Cliente {nombre} {apellido} actualizado exitosamente.', 'success')
            return redirect(url_for('clientes'))
        
        # Obtener datos del cliente para mostrar en el formulario
        cursor.execute("SELECT * FROM clientes WHERE id_cliente = %s", (id,))
        cliente = cursor.fetchone()
        
        if not cliente:
            flash('Cliente no encontrado.', 'danger')
            return redirect(url_for('clientes'))
        
    except Error as e:
        flash(f'Error editando cliente: {e}', 'danger')
        return redirect(url_for('clientes'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    return render_template('clientes/editar.html', cliente=cliente)

@app.route('/clientes/eliminar/<int:id>', methods=['POST'])
def eliminar_cliente(id):
    """Eliminar cliente (soft delete o hard delete)"""
    conn = get_db_connection()
    
    if not conn:
        return jsonify({'success': False, 'message': 'No hay conexión a la base de datos.'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el cliente tiene mascotas asociadas
        cursor.execute("SELECT COUNT(*) as total FROM mascotas WHERE id_cliente = %s", (id,))
        result = cursor.fetchone()
        
        if result and result['total'] > 0:
            return jsonify({
                'success': False, 
                'message': f'No se puede eliminar el cliente porque tiene {result["total"]} mascota(s) asociada(s). Primero elimina o transfiere las mascotas.'
            })
        
        # Si no tiene mascotas, proceder con eliminación
        cursor.execute("DELETE FROM clientes WHERE id_cliente = %s", (id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return jsonify({'success': True, 'message': 'Cliente eliminado exitosamente.'})
        else:
            return jsonify({'success': False, 'message': 'Cliente no encontrado.'}), 404
            
    except Error as e:
        return jsonify({'success': False, 'message': f'Error eliminando cliente: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# También puedes agregar una ruta para ver detalles del cliente
@app.route('/clientes/ver/<int:id>')
def ver_cliente(id):
    """Ver detalles del cliente"""
    conn = get_db_connection()
    cliente = None
    mascotas = []
    
    if not conn:
        flash('No hay conexión a la base de datos.', 'danger')
        return redirect(url_for('clientes'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener datos del cliente
        cursor.execute("SELECT * FROM clientes WHERE id_cliente = %s", (id,))
        cliente = cursor.fetchone()
        
        if not cliente:
            flash('Cliente no encontrado.', 'danger')
            return redirect(url_for('clientes'))
        
        # Obtener mascotas del cliente
        cursor.execute("SELECT * FROM mascotas WHERE id_cliente = %s", (id,))
        mascotas = cursor.fetchall()
        
    except Error as e:
        flash(f'Error obteniendo datos del cliente: {e}', 'danger')
        return redirect(url_for('clientes'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    return render_template('clientes/ver.html', cliente=cliente, mascotas=mascotas)


@app.route('/mascotas')
def mascotas():
    """Listar mascotas"""
    conn = get_db_connection()
    mascotas_list = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT m.*, c.nombre as cliente_nombre, c.apellido as cliente_apellido
                FROM mascotas m
                LEFT JOIN clientes c ON m.id_cliente = c.id_cliente
                ORDER BY m.fecha_registro DESC LIMIT 50
            """)
            mascotas_list = cursor.fetchall()
            cursor.close()
        except Error as e:
            flash(f'Error obteniendo mascotas: {e}', 'danger')
        finally:
            conn.close()
    else:
        # Datos demo
        mascotas_list = [
            {'id_mascota': 1, 'nombre': 'Max', 'especie': 'perro', 'raza': 'Labrador', 'cliente_nombre': 'Juan', 'cliente_apellido': 'Pérez', 'fecha_registro': datetime.now()},
            {'id_mascota': 2, 'nombre': 'Luna', 'especie': 'gato', 'raza': 'Siamés', 'cliente_nombre': 'María', 'cliente_apellido': 'García', 'fecha_registro': datetime.now()},
            {'id_mascota': 3, 'nombre': 'Rocky', 'especie': 'perro', 'raza': 'Bulldog', 'cliente_nombre': 'Carlos', 'cliente_apellido': 'Ruiz', 'fecha_registro': datetime.now()}
        ]
    
    return render_template('mascotas/listar.html', mascotas=mascotas_list)

@app.route('/servicios')
def servicios():
    """Listar servicios"""
    conn = get_db_connection()
    servicios_list = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM servicios WHERE activo = 1 ORDER BY precio")
            servicios_list = cursor.fetchall()
            cursor.close()
        except Error as e:
            flash(f'Error obteniendo servicios: {e}', 'danger')
        finally:
            conn.close()
    else:
        # Datos demo
        servicios_list = [
            {'id_servicio': 1, 'nombre': 'Baño Básico', 'precio': 25.00, 'descripcion': 'Baño con shampoo especial'},
            {'id_servicio': 2, 'nombre': 'Corte de Pelo', 'precio': 35.00, 'descripcion': 'Corte profesional'},
            {'id_servicio': 3, 'nombre': 'Baño + Corte', 'precio': 50.00, 'descripcion': 'Servicio completo'},
            {'id_servicio': 4, 'nombre': 'Limpieza Dental', 'precio': 20.00, 'descripcion': 'Limpieza dental especializada'}
        ]
    
    return render_template('servicios/listar.html', servicios=servicios_list)

@app.route('/reservas')
def reservas():
    """Listar reservas"""
    conn = get_db_connection()
    reservas_list = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT r.*, m.nombre as mascota_nombre, 
                       c.nombre as cliente_nombre, c.apellido as cliente_apellido,
                       s.nombre as servicio_nombre, s.precio as servicio_precio
                FROM reservas r
                LEFT JOIN mascotas m ON r.id_mascota = m.id_mascota
                LEFT JOIN clientes c ON m.id_cliente = c.id_cliente
                LEFT JOIN servicios s ON r.id_servicio = s.id_servicio
                ORDER BY r.fecha_reserva DESC LIMIT 50
            """)
            reservas_list = cursor.fetchall()
            cursor.close()
        except Error as e:
            flash(f'Error obteniendo reservas: {e}', 'danger')
        finally:
            conn.close()
    else:
        # Datos demo
        reservas_list = [
            {'id_reserva': 1, 'fecha_reserva': datetime.now(), 'mascota_nombre': 'Max', 'cliente_nombre': 'Juan', 'cliente_apellido': 'Pérez', 'servicio_nombre': 'Baño Básico', 'estado': 'completada'},
            {'id_reserva': 2, 'fecha_reserva': datetime.now(), 'mascota_nombre': 'Luna', 'cliente_nombre': 'María', 'cliente_apellido': 'García', 'servicio_nombre': 'Corte de Pelo', 'estado': 'pendiente'},
        ]
    
    return render_template('reservas/listar.html', reservas=reservas_list)

@app.route('/ventas')
def ventas():
    """Listar ventas/facturas"""
    conn = get_db_connection()
    ventas_list = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT f.*, c.nombre as cliente_nombre, c.apellido as cliente_apellido
                FROM facturas f
                LEFT JOIN clientes c ON f.id_cliente = c.id_cliente
                ORDER BY f.fecha_emision DESC LIMIT 50
            """)
            ventas_list = cursor.fetchall()
            cursor.close()
        except Error as e:
            flash(f'Error obteniendo ventas: {e}', 'danger')
        finally:
            conn.close()
    else:
        # Datos demo
        ventas_list = [
            {'id_factura': 1, 'numero': 'B001-0001', 'total': 50.00, 'fecha_emision': datetime.now(), 'cliente_nombre': 'Juan', 'cliente_apellido': 'Pérez', 'estado': 'pagada'},
            {'id_factura': 2, 'numero': 'B001-0002', 'total': 35.00, 'fecha_emision': datetime.now(), 'cliente_nombre': 'María', 'cliente_apellido': 'García', 'estado': 'pagada'},
        ]
    
    return render_template('ventas/listar.html', ventas=ventas_list)

@app.route('/reportes')
def reportes():
    """Página de reportes"""
    return render_template('reportes/ventas.html')

@app.route('/config')
def config():
    """Configuración del sistema"""
    return render_template('config.html')

# ================= MANEJO DE ERRORES =================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# ================= CONTEXT PROCESSORS =================

@app.context_processor
def inject_now():
    """Inyectar fecha actual en todas las plantillas"""
    return {'now': datetime.now()}

@app.context_processor
def inject_user_data():
    """Inyectar datos del usuario (ahora siempre con usuario demo)"""
    return {
        'current_user': {
            'id': 1,
            'username': 'admin',
            'rol': 'admin',
            'nombre': 'Administrador'
        },
        'user_role': 'admin'
    }

# ================= EJECUCIÓN =================

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 PETGLOW WEB SYSTEM - SIN LOGIN")
    print("=" * 50)
    print("📊 URL: http://localhost:5000")
    print("👤 Acceso directo al dashboard")
    print("=" * 50)
    
    # Verificar conexión a BD
    conn = get_db_connection()
    if conn:
        print("✅ Conectado a MySQL")
        conn.close()
    else:
        print("⚠️  Modo DEMO - Sin conexión a MySQL")
        print("   Configura tu .env con las credenciales correctas")
    
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)