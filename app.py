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
    

@app.route('/mascotas/crear', methods=['GET', 'POST'])
def crear_mascota():
    """Crear nueva mascota"""
    conn = get_db_connection()
    
    if not conn:
        flash('No hay conexión a la base de datos.', 'danger')
        return redirect(url_for('mascotas'))
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            id_cliente = request.form.get('id_cliente', '').strip()
            nombre = request.form.get('nombre', '').strip()
            especie = request.form.get('especie', 'perro').strip()
            raza = request.form.get('raza', '').strip()
            tamano = request.form.get('tamano', '').strip()
            fecha_nacimiento = request.form.get('fecha_nacimiento', '').strip()
            peso = request.form.get('peso', '').strip()
            color = request.form.get('color', '').strip()
            caracteristicas = request.form.get('caracteristicas', '').strip()
            alergias = request.form.get('alergias', '').strip()
            
            # Validaciones básicas
            if not id_cliente or not nombre:
                flash('Cliente y nombre de mascota son obligatorios.', 'danger')
                return redirect(url_for('crear_mascota'))
            
            # Convertir fecha
            fecha_nacimiento_dt = None
            if fecha_nacimiento:
                try:
                    fecha_nacimiento_dt = datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
                except ValueError:
                    flash('Formato de fecha inválido. Use YYYY-MM-DD.', 'danger')
                    return redirect(url_for('crear_mascota'))
            
            # Convertir peso
            peso_float = None
            if peso:
                try:
                    peso_float = float(peso)
                except ValueError:
                    flash('Peso debe ser un número válido.', 'danger')
                    return redirect(url_for('crear_mascota'))
            
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mascotas (
                    id_cliente, nombre, especie, raza, tamano, 
                    fecha_nacimiento, peso, color, caracteristicas, alergias
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                id_cliente, nombre, especie, raza or None, tamano or None,
                fecha_nacimiento_dt, peso_float, color or None, 
                caracteristicas or None, alergias or None
            ))
            conn.commit()
            
            flash(f'Mascota {nombre} creada exitosamente.', 'success')
            return redirect(url_for('mascotas'))
            
        except Error as e:
            flash(f'Error creando mascota: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    # GET: Obtener clientes para el select
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_cliente, nombre, apellido FROM clientes ORDER BY apellido, nombre")
        clientes = cursor.fetchall()
        cursor.close()
    except Error as e:
        flash(f'Error obteniendo clientes: {e}', 'danger')
        clientes = []
    finally:
        conn.close()
    
    return render_template('mascotas/crear.html', clientes=clientes)

@app.route('/mascotas/editar/<int:id>', methods=['GET', 'POST'])
def editar_mascota(id):
    """Editar mascota existente"""
    conn = get_db_connection()
    
    if not conn:
        flash('No hay conexión a la base de datos.', 'danger')
        return redirect(url_for('mascotas'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'POST':
            # Obtener datos del formulario
            id_cliente = request.form.get('id_cliente', '').strip()
            nombre = request.form.get('nombre', '').strip()
            especie = request.form.get('especie', 'perro').strip()
            raza = request.form.get('raza', '').strip()
            tamano = request.form.get('tamano', '').strip()
            fecha_nacimiento = request.form.get('fecha_nacimiento', '').strip()
            peso = request.form.get('peso', '').strip()
            color = request.form.get('color', '').strip()
            caracteristicas = request.form.get('caracteristicas', '').strip()
            alergias = request.form.get('alergias', '').strip()
            
            # Validaciones básicas
            if not id_cliente or not nombre:
                flash('Cliente y nombre de mascota son obligatorios.', 'danger')
                return redirect(url_for('editar_mascota', id=id))
            
            # Convertir fecha
            fecha_nacimiento_dt = None
            if fecha_nacimiento:
                try:
                    fecha_nacimiento_dt = datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
                except ValueError:
                    flash('Formato de fecha inválido. Use YYYY-MM-DD.', 'danger')
                    return redirect(url_for('editar_mascota', id=id))
            
            # Convertir peso
            peso_float = None
            if peso:
                try:
                    peso_float = float(peso)
                except ValueError:
                    flash('Peso debe ser un número válido.', 'danger')
                    return redirect(url_for('editar_mascota', id=id))
            
            # Actualizar mascota
            cursor.execute("""
                UPDATE mascotas 
                SET id_cliente = %s, nombre = %s, especie = %s, raza = %s, tamano = %s,
                    fecha_nacimiento = %s, peso = %s, color = %s, 
                    caracteristicas = %s, alergias = %s
                WHERE id_mascota = %s
            """, (
                id_cliente, nombre, especie, raza or None, tamano or None,
                fecha_nacimiento_dt, peso_float, color or None, 
                caracteristicas or None, alergias or None, id
            ))
            conn.commit()
            
            flash(f'Mascota {nombre} actualizada exitosamente.', 'success')
            return redirect(url_for('mascotas'))
        
        # GET: Obtener datos de la mascota
        cursor.execute("SELECT * FROM mascotas WHERE id_mascota = %s", (id,))
        mascota = cursor.fetchone()
        
        if not mascota:
            flash('Mascota no encontrada.', 'danger')
            return redirect(url_for('mascotas'))
        
        # Obtener clientes para el select
        cursor.execute("SELECT id_cliente, nombre, apellido FROM clientes ORDER BY apellido, nombre")
        clientes = cursor.fetchall()
        
        # Formatear fecha para input type="date"
        if mascota['fecha_nacimiento']:
            mascota['fecha_nacimiento_str'] = mascota['fecha_nacimiento'].strftime('%Y-%m-%d')
        else:
            mascota['fecha_nacimiento_str'] = ''
        
    except Error as e:
        flash(f'Error editando mascota: {e}', 'danger')
        return redirect(url_for('mascotas'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('mascotas/editar.html', mascota=mascota, clientes=clientes)

@app.route('/mascotas/eliminar/<int:id>', methods=['POST'])
def eliminar_mascota(id):
    """Eliminar mascota (soft delete)"""
    conn = get_db_connection()
    
    if not conn:
        return jsonify({'success': False, 'message': 'No hay conexión a la base de datos.'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Verificar si la mascota tiene reservas asociadas
        cursor.execute("SELECT COUNT(*) as total FROM reservas WHERE id_mascota = %s", (id,))
        result = cursor.fetchone()
        
        if result and result[0] > 0:
            return jsonify({
                'success': False, 
                'message': f'No se puede eliminar la mascota porque tiene {result[0]} reserva(s) asociada(s).'
            })
        
        # Soft delete (cambiar activo a false)
        cursor.execute("UPDATE mascotas SET activo = FALSE WHERE id_mascota = %s", (id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return jsonify({'success': True, 'message': 'Mascota eliminada exitosamente.'})
        else:
            return jsonify({'success': False, 'message': 'Mascota no encontrada.'}), 404
            
    except Error as e:
        return jsonify({'success': False, 'message': f'Error eliminando mascota: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/mascotas/ver/<int:id>')
def ver_mascota(id):
    """Ver detalles de la mascota"""
    conn = get_db_connection()
    
    if not conn:
        flash('No hay conexión a la base de datos.', 'danger')
        return redirect(url_for('mascotas'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener datos de la mascota con información del cliente
        cursor.execute("""
            SELECT m.*, 
                   c.id_cliente, c.nombre as cliente_nombre, c.apellido as cliente_apellido,
                   c.telefono as cliente_telefono, c.email as cliente_email
            FROM mascotas m
            LEFT JOIN clientes c ON m.id_cliente = c.id_cliente
            WHERE m.id_mascota = %s
        """, (id,))
        mascota = cursor.fetchone()
        
        if not mascota:
            flash('Mascota no encontrada.', 'danger')
            return redirect(url_for('mascotas'))
        
        # Obtener historial de reservas CORREGIDO
        cursor.execute("""
            SELECT r.*, 
                   e.nombre as empleado_nombre, e.apellido as empleado_apellido,
                   GROUP_CONCAT(s.nombre SEPARATOR ', ') as servicios_nombres
            FROM reservas r
            LEFT JOIN empleados e ON r.id_empleado = e.id_empleado
            LEFT JOIN reserva_servicios rs ON r.id_reserva = rs.id_reserva
            LEFT JOIN servicios s ON rs.id_servicio = s.id_servicio
            WHERE r.id_mascota = %s
            GROUP BY r.id_reserva
            ORDER BY r.fecha_reserva DESC
            LIMIT 10
        """, (id,))
        reservas = cursor.fetchall()
        
        # Formatear fechas
        if mascota['fecha_nacimiento']:
            from datetime import datetime
            hoy = datetime.now().date()
            nacimiento = mascota['fecha_nacimiento']
            edad_dias = (hoy - nacimiento).days
            mascota['edad_anios'] = edad_dias // 365
            mascota['edad_meses'] = (edad_dias % 365) // 30
        
    except Error as e:
        flash(f'Error obteniendo datos de la mascota: {e}', 'danger')
        return redirect(url_for('mascotas'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('mascotas/ver.html', mascota=mascota, reservas=reservas)

@app.route('/servicios')
def servicios():
    """Listar servicios"""
    conn = get_db_connection()
    servicios_list = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM servicios 
                WHERE activo = 1 
                ORDER BY categoria, precio
            """)
            servicios_list = cursor.fetchall()
            
            # Calcular márgenes si no están en la BD
            for servicio in servicios_list:
                if servicio['margen'] is None and servicio['costo'] and servicio['precio']:
                    if servicio['costo'] > 0:
                        servicio['margen'] = ((servicio['precio'] - servicio['costo']) / servicio['costo']) * 100
                    else:
                        servicio['margen'] = 0
            
            cursor.close()
        except Error as e:
            flash(f'Error obteniendo servicios: {e}', 'danger')
        finally:
            conn.close()
    else:
        # Datos demo con márgenes calculados
        servicios_list = [
            {'id_servicio': 1, 'nombre': 'Baño Básico', 'precio': 25.00, 'costo': 10.00, 'margen': 150.00, 'descripcion': 'Baño con shampoo especial', 'categoria': 'baño', 'duracion_min': 45},
            {'id_servicio': 2, 'nombre': 'Corte de Pelo', 'precio': 35.00, 'costo': 12.00, 'margen': 191.67, 'descripcion': 'Corte profesional', 'categoria': 'corte', 'duracion_min': 60},
            {'id_servicio': 3, 'nombre': 'Baño + Corte', 'precio': 50.00, 'costo': 20.00, 'margen': 150.00, 'descripcion': 'Servicio completo', 'categoria': 'spa', 'duracion_min': 90},
            {'id_servicio': 4, 'nombre': 'Limpieza Dental', 'precio': 20.00, 'costo': 8.00, 'margen': 150.00, 'descripcion': 'Limpieza dental especializada', 'categoria': 'salud', 'duracion_min': 30},
        ]
    
    return render_template('servicios/listar.html', servicios=servicios_list)

# ================= RUTAS DE SERVICIOS =================

@app.route('/servicios/crear', methods=['GET', 'POST'])
def crear_servicio():
    """Crear nuevo servicio"""
    if request.method == 'POST':
        # Obtener datos del formulario
        codigo = request.form.get('codigo', '').strip()
        nombre = request.form.get('nombre', '').strip()
        categoria = request.form.get('categoria', 'baño').strip()
        descripcion = request.form.get('descripcion', '').strip()
        duracion_min = request.form.get('duracion_min', '60').strip()
        costo = request.form.get('costo', '0').strip()
        precio = request.form.get('precio', '0').strip()
        
        # Validaciones básicas
        if not codigo or not nombre:
            flash('Código y nombre son obligatorios.', 'danger')
            return redirect(url_for('crear_servicio'))
        
        try:
            duracion_int = int(duracion_min) if duracion_min else 60
            costo_float = float(costo) if costo else 0.0
            precio_float = float(precio) if precio else 0.0
        except ValueError:
            flash('Duración, costo y precio deben ser números válidos.', 'danger')
            return redirect(url_for('crear_servicio'))
        
        if precio_float <= 0:
            flash('El precio debe ser mayor a 0.', 'danger')
            return redirect(url_for('crear_servicio'))
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO servicios (codigo, nombre, categoria, descripcion, 
                                          duracion_min, costo, precio)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (codigo, nombre, categoria, descripcion or None, 
                      duracion_int, costo_float, precio_float))
                conn.commit()
                
                flash(f'Servicio {nombre} creado exitosamente.', 'success')
                return redirect(url_for('servicios'))
                
            except Error as e:
                flash(f'Error creando servicio: {e}', 'danger')
            finally:
                cursor.close()
                conn.close()
        else:
            flash('No hay conexión a la base de datos.', 'danger')
    
    return render_template('servicios/crear.html')

@app.route('/servicios/editar/<int:id>', methods=['GET', 'POST'])
def editar_servicio(id):
    """Editar servicio existente"""
    conn = get_db_connection()
    
    if not conn:
        flash('No hay conexión a la base de datos.', 'danger')
        return redirect(url_for('servicios'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'POST':
            # Obtener datos del formulario
            codigo = request.form.get('codigo', '').strip()
            nombre = request.form.get('nombre', '').strip()
            categoria = request.form.get('categoria', 'baño').strip()
            descripcion = request.form.get('descripcion', '').strip()
            duracion_min = request.form.get('duracion_min', '60').strip()
            costo = request.form.get('costo', '0').strip()
            precio = request.form.get('precio', '0').strip()
            
            # Validaciones
            if not codigo or not nombre:
                flash('Código y nombre son obligatorios.', 'danger')
                return redirect(url_for('editar_servicio', id=id))
            
            try:
                duracion_int = int(duracion_min) if duracion_min else 60
                costo_float = float(costo) if costo else 0.0
                precio_float = float(precio) if precio else 0.0
            except ValueError:
                flash('Duración, costo y precio deben ser números válidos.', 'danger')
                return redirect(url_for('editar_servicio', id=id))
            
            if precio_float <= 0:
                flash('El precio debe ser mayor a 0.', 'danger')
                return redirect(url_for('editar_servicio', id=id))
            
            # Actualizar servicio
            cursor.execute("""
                UPDATE servicios 
                SET codigo = %s, nombre = %s, categoria = %s, descripcion = %s,
                    duracion_min = %s, costo = %s, precio = %s
                WHERE id_servicio = %s
            """, (codigo, nombre, categoria, descripcion or None, 
                  duracion_int, costo_float, precio_float, id))
            conn.commit()
            
            flash(f'Servicio {nombre} actualizado exitosamente.', 'success')
            return redirect(url_for('servicios'))
        
        # GET: Obtener datos del servicio
        cursor.execute("SELECT * FROM servicios WHERE id_servicio = %s", (id,))
        servicio = cursor.fetchone()
        
        if not servicio:
            flash('Servicio no encontrado.', 'danger')
            return redirect(url_for('servicios'))
        
    except Error as e:
        flash(f'Error editando servicio: {e}', 'danger')
        return redirect(url_for('servicios'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('servicios/editar.html', servicio=servicio)

@app.route('/servicios/eliminar/<int:id>', methods=['POST'])
def eliminar_servicio(id):
    """Eliminar servicio (soft delete)"""
    conn = get_db_connection()
    
    if not conn:
        return jsonify({'success': False, 'message': 'No hay conexión a la base de datos.'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Verificar si el servicio está en uso en reservas
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM reserva_servicios 
            WHERE id_servicio = %s
        """, (id,))
        result = cursor.fetchone()
        
        if result and result[0] > 0:
            return jsonify({
                'success': False, 
                'message': f'No se puede eliminar el servicio porque está en {result[0]} reserva(s).'
            })
        
        # Soft delete
        cursor.execute("UPDATE servicios SET activo = FALSE WHERE id_servicio = %s", (id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return jsonify({'success': True, 'message': 'Servicio eliminado exitosamente.'})
        else:
            return jsonify({'success': False, 'message': 'Servicio no encontrado.'}), 404
            
    except Error as e:
        return jsonify({'success': False, 'message': f'Error eliminando servicio: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/servicios/ver/<int:id>')
def ver_servicio(id):
    """Ver detalles del servicio"""
    conn = get_db_connection()
    
    if not conn:
        flash('No hay conexión a la base de datos.', 'danger')
        return redirect(url_for('servicios'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener datos del servicio
        cursor.execute("SELECT * FROM servicios WHERE id_servicio = %s", (id,))
        servicio = cursor.fetchone()
        
        if not servicio:
            flash('Servicio no encontrado.', 'danger')
            return redirect(url_for('servicios'))
        
        # Calcular margen si no está en la BD
        if servicio['margen'] is None and servicio['costo'] and servicio['precio']:
            if servicio['costo'] > 0:
                servicio['margen'] = ((servicio['precio'] - servicio['costo']) / servicio['costo']) * 100
            else:
                servicio['margen'] = 0
        
        # Obtener estadísticas de uso
        cursor.execute("""
            SELECT COUNT(*) as total_reservas,
                   SUM(rs.cantidad) as total_veces,
                   SUM(rs.subtotal) as total_ingresos
            FROM reserva_servicios rs
            WHERE rs.id_servicio = %s
        """, (id,))
        estadisticas = cursor.fetchone()
        
        servicio['total_reservas'] = estadisticas['total_reservas'] or 0
        servicio['total_veces'] = estadisticas['total_veces'] or 0
        servicio['total_ingresos'] = estadisticas['total_ingresos'] or 0.0
        
    except Error as e:
        flash(f'Error obteniendo datos del servicio: {e}', 'danger')
        return redirect(url_for('servicios'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('servicios/ver.html', servicio=servicio)

@app.route('/reservas')
def reservas():
    """Listar reservas"""
    conn = get_db_connection()
    reservas_list = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT r.*, 
                       m.nombre as mascota_nombre, m.especie,
                       c.nombre as cliente_nombre, c.apellido as cliente_apellido,
                       e.nombre as empleado_nombre, e.apellido as empleado_apellido,
                       (SELECT GROUP_CONCAT(s.nombre SEPARATOR ', ')
                        FROM reserva_servicios rs
                        JOIN servicios s ON rs.id_servicio = s.id_servicio
                        WHERE rs.id_reserva = r.id_reserva) as servicios_nombres
                FROM reservas r
                JOIN mascotas m ON r.id_mascota = m.id_mascota
                JOIN clientes c ON m.id_cliente = c.id_cliente
                JOIN empleados e ON r.id_empleado = e.id_empleado
                ORDER BY r.fecha_reserva DESC 
                LIMIT 50
            """)
            reservas_list = cursor.fetchall()
            
            # Formatear datos
            for reserva in reservas_list:
                # Estado con clase CSS
                estado_clases = {
                    'pendiente': 'bg-warning',
                    'confirmada': 'bg-info',
                    'en_proceso': 'bg-primary',
                    'completada': 'bg-success',
                    'cancelada': 'bg-danger',
                    'no_show': 'bg-secondary'
                }
                reserva['estado_clase'] = estado_clases.get(reserva['estado'], 'bg-secondary')
                reserva['estado_texto'] = reserva['estado'].replace('_', ' ').title()
                
                # Verificar si está vencida
                if reserva['estado'] == 'pendiente' and reserva['fecha_reserva'] < datetime.now():
                    reserva['vencida'] = True
                    reserva['estado_clase'] = 'bg-dark'
                    reserva['estado_texto'] = 'Vencida'
            
            cursor.close()
        except Error as e:
            flash(f'Error obteniendo reservas: {e}', 'danger')
        finally:
            conn.close()
    else:
        # Datos demo
        reservas_list = [
            {
                'id_reserva': 1, 
                'codigo_reserva': 'RES-231201-0001',
                'fecha_reserva': datetime.now(), 
                'mascota_nombre': 'Max', 
                'cliente_nombre': 'Juan', 
                'cliente_apellido': 'Pérez', 
                'empleado_nombre': 'Ana', 
                'servicios_nombres': 'Baño Básico, Corte',
                'estado': 'completada',
                'estado_clase': 'bg-success',
                'estado_texto': 'Completada'
            },
            {
                'id_reserva': 2, 
                'codigo_reserva': 'RES-231201-0002',
                'fecha_reserva': datetime.now(), 
                'mascota_nombre': 'Luna', 
                'cliente_nombre': 'María', 
                'cliente_apellido': 'García', 
                'empleado_nombre': 'Carlos', 
                'servicios_nombres': 'Corte Premium',
                'estado': 'pendiente',
                'estado_clase': 'bg-warning',
                'estado_texto': 'Pendiente'
            },
        ]
    
    return render_template('reservas/listar.html', reservas=reservas_list)

# ================= RUTAS DE RESERVAS =================

@app.route('/reservas/crear', methods=['GET', 'POST'])
def crear_reserva():
    """Crear nueva reserva"""
    conn = get_db_connection()
    
    if not conn:
        flash('No hay conexión a la base de datos.', 'danger')
        return redirect(url_for('reservas'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'POST':
            # Obtener datos del formulario
            id_mascota = request.form.get('id_mascota', '').strip()
            id_empleado = request.form.get('id_empleado', '').strip()
            fecha_reserva = request.form.get('fecha_reserva', '').strip()
            hora_reserva = request.form.get('hora_reserva', '').strip()
            servicios = request.form.getlist('servicios[]')
            notas = request.form.get('notas', '').strip()
            
            # Validaciones
            if not id_mascota or not id_empleado or not fecha_reserva or not hora_reserva:
                flash('Todos los campos obligatorios deben ser completados.', 'danger')
                return redirect(url_for('crear_reserva'))
            
            if not servicios:
                flash('Debe seleccionar al menos un servicio.', 'danger')
                return redirect(url_for('crear_reserva'))
            
            # Combinar fecha y hora
            try:
                fecha_hora_str = f"{fecha_reserva} {hora_reserva}"
                fecha_hora_dt = datetime.strptime(fecha_hora_str, '%Y-%m-%d %H:%M')
                
                # Verificar que la fecha no sea pasada
                if fecha_hora_dt < datetime.now():
                    flash('No se pueden crear reservas en fechas pasadas.', 'danger')
                    return redirect(url_for('crear_reserva'))
            except ValueError:
                flash('Formato de fecha u hora inválido.', 'danger')
                return redirect(url_for('crear_reserva'))
            
            # Generar código de reserva único
            codigo_reserva = f"RES-{datetime.now().strftime('%y%m%d')}-{cursor.lastrowid or 1:04d}"
            
            # Crear reserva
            cursor.execute("""
                INSERT INTO reservas (codigo_reserva, id_mascota, id_empleado, fecha_reserva, notas)
                VALUES (%s, %s, %s, %s, %s)
            """, (codigo_reserva, id_mascota, id_empleado, fecha_hora_dt, notas or None))
            
            id_reserva = cursor.lastrowid
            
            # Agregar servicios a la reserva
            for servicio_id in servicios:
                # Obtener precio del servicio
                cursor.execute("SELECT precio FROM servicios WHERE id_servicio = %s", (servicio_id,))
                servicio = cursor.fetchone()
                if servicio:
                    cursor.execute("""
                        INSERT INTO reserva_servicios (id_reserva, id_servicio, precio_unitario)
                        VALUES (%s, %s, %s)
                    """, (id_reserva, servicio_id, servicio['precio']))
            
            conn.commit()
            
            flash(f'Reserva {codigo_reserva} creada exitosamente.', 'success')
            return redirect(url_for('ver_reserva', id=id_reserva))
        
        # GET: Obtener datos para formulario
        # Mascotas
        cursor.execute("""
            SELECT m.id_mascota, m.nombre as mascota_nombre, 
                   c.nombre as cliente_nombre, c.apellido as cliente_apellido
            FROM mascotas m
            JOIN clientes c ON m.id_cliente = c.id_cliente
            WHERE m.activo = TRUE
            ORDER BY m.nombre
        """)
        mascotas = cursor.fetchall()
        
        # Empleados
        cursor.execute("""
            SELECT id_empleado, nombre, apellido, especialidad
            FROM empleados
            WHERE activo = TRUE
            ORDER BY nombre
        """)
        empleados = cursor.fetchall()
        
        # Servicios
        cursor.execute("""
            SELECT id_servicio, nombre, precio, categoria, duracion_min
            FROM servicios
            WHERE activo = TRUE
            ORDER BY categoria, nombre
        """)
        servicios = cursor.fetchall()
        
        # Agrupar servicios por categoría
        servicios_por_categoria = {}
        for servicio in servicios:
            categoria = servicio['categoria']
            if categoria not in servicios_por_categoria:
                servicios_por_categoria[categoria] = []
            servicios_por_categoria[categoria].append(servicio)
        
        # Fecha mínima (hoy)
        fecha_minima = datetime.now().strftime('%Y-%m-%d')
        # Hora mínima (hora actual redondeada a 30 minutos)
        hora_actual = datetime.now()
        hora_minima = f"{hora_actual.hour:02d}:{(hora_actual.minute // 30) * 30:02d}"
        
    except Error as e:
        flash(f'Error creando reserva: {e}', 'danger')
        return redirect(url_for('reservas'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('reservas/crear.html', 
                         mascotas=mascotas, 
                         empleados=empleados,
                         servicios_por_categoria=servicios_por_categoria,
                         fecha_minima=fecha_minima,
                         hora_minima=hora_minima)

@app.route('/reservas/editar/<int:id>', methods=['GET', 'POST'])
def editar_reserva(id):
    """Editar reserva existente"""
    conn = get_db_connection()
    
    if not conn:
        flash('No hay conexión a la base de datos.', 'danger')
        return redirect(url_for('reservas'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'POST':
            # Obtener datos del formulario
            id_mascota = request.form.get('id_mascota', '').strip()
            id_empleado = request.form.get('id_empleado', '').strip()
            fecha_reserva = request.form.get('fecha_reserva', '').strip()
            hora_reserva = request.form.get('hora_reserva', '').strip()
            servicios = request.form.getlist('servicios[]')
            notas = request.form.get('notas', '').strip()
            estado = request.form.get('estado', 'pendiente').strip()
            
            # Validaciones
            if not id_mascota or not id_empleado or not fecha_reserva or not hora_reserva:
                flash('Todos los campos obligatorios deben ser completados.', 'danger')
                return redirect(url_for('editar_reserva', id=id))
            
            if not servicios:
                flash('Debe seleccionar al menos un servicio.', 'danger')
                return redirect(url_for('editar_reserva', id=id))
            
            # Combinar fecha y hora
            try:
                fecha_hora_str = f"{fecha_reserva} {hora_reserva}"
                fecha_hora_dt = datetime.strptime(fecha_hora_str, '%Y-%m-%d %H:%M')
            except ValueError:
                flash('Formato de fecha u hora inválido.', 'danger')
                return redirect(url_for('editar_reserva', id=id))
            
            # Actualizar reserva
            cursor.execute("""
                UPDATE reservas 
                SET id_mascota = %s, id_empleado = %s, fecha_reserva = %s, 
                    notas = %s, estado = %s
                WHERE id_reserva = %s
            """, (id_mascota, id_empleado, fecha_hora_dt, notas or None, estado, id))
            
            # Eliminar servicios anteriores y agregar nuevos
            cursor.execute("DELETE FROM reserva_servicios WHERE id_reserva = %s", (id,))
            
            # Agregar servicios a la reserva
            for servicio_id in servicios:
                # Obtener precio del servicio
                cursor.execute("SELECT precio FROM servicios WHERE id_servicio = %s", (servicio_id,))
                servicio = cursor.fetchone()
                if servicio:
                    cursor.execute("""
                        INSERT INTO reserva_servicios (id_reserva, id_servicio, precio_unitario)
                        VALUES (%s, %s, %s)
                    """, (id, servicio_id, servicio['precio']))
            
            conn.commit()
            
            flash(f'Reserva actualizada exitosamente.', 'success')
            return redirect(url_for('ver_reserva', id=id))
        
        # GET: Obtener datos de la reserva
        cursor.execute("""
            SELECT r.*, m.nombre as mascota_nombre, m.id_cliente,
                   e.nombre as empleado_nombre, e.apellido as empleado_apellido
            FROM reservas r
            JOIN mascotas m ON r.id_mascota = m.id_mascota
            JOIN empleados e ON r.id_empleado = e.id_empleado
            WHERE r.id_reserva = %s
        """, (id,))
        reserva = cursor.fetchone()
        
        if not reserva:
            flash('Reserva no encontrada.', 'danger')
            return redirect(url_for('reservas'))
        
        # Obtener servicios de la reserva
        cursor.execute("""
            SELECT rs.id_servicio, s.nombre, rs.precio_unitario
            FROM reserva_servicios rs
            JOIN servicios s ON rs.id_servicio = s.id_servicio
            WHERE rs.id_reserva = %s
        """, (id,))
        servicios_reserva = cursor.fetchall()
        servicios_ids = [str(s['id_servicio']) for s in servicios_reserva]
        
        # Formatear fecha para inputs
        fecha_hora = reserva['fecha_reserva']
        reserva['fecha_str'] = fecha_hora.strftime('%Y-%m-%d')
        reserva['hora_str'] = fecha_hora.strftime('%H:%M')
        
        # Datos para formulario
        # Mascotas
        cursor.execute("""
            SELECT m.id_mascota, m.nombre as mascota_nombre, 
                   c.nombre as cliente_nombre, c.apellido as cliente_apellido
            FROM mascotas m
            JOIN clientes c ON m.id_cliente = c.id_cliente
            WHERE m.activo = TRUE
            ORDER BY m.nombre
        """)
        mascotas = cursor.fetchall()
        
        # Empleados
        cursor.execute("""
            SELECT id_empleado, nombre, apellido, especialidad
            FROM empleados
            WHERE activo = TRUE
            ORDER BY nombre
        """)
        empleados = cursor.fetchall()
        
        # Servicios
        cursor.execute("""
            SELECT id_servicio, nombre, precio, categoria, duracion_min
            FROM servicios
            WHERE activo = TRUE
            ORDER BY categoria, nombre
        """)
        servicios = cursor.fetchall()
        
        # Agrupar servicios por categoría
        servicios_por_categoria = {}
        for servicio in servicios:
            categoria = servicio['categoria']
            if categoria not in servicios_por_categoria:
                servicios_por_categoria[categoria] = []
            servicios_por_categoria[categoria].append(servicio)
        
    except Error as e:
        flash(f'Error editando reserva: {e}', 'danger')
        return redirect(url_for('reservas'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('reservas/editar.html', 
                         reserva=reserva,
                         servicios_ids=servicios_ids,
                         mascotas=mascotas, 
                         empleados=empleados,
                         servicios_por_categoria=servicios_por_categoria)

@app.route('/reservas/eliminar/<int:id>', methods=['POST'])
def eliminar_reserva(id):
    """Eliminar reserva"""
    conn = get_db_connection()
    
    if not conn:
        return jsonify({'success': False, 'message': 'No hay conexión a la base de datos.'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Verificar si la reserva tiene factura asociada
        cursor.execute("SELECT COUNT(*) as total FROM facturas WHERE id_reserva = %s", (id,))
        result = cursor.fetchone()
        
        if result and result[0] > 0:
            return jsonify({
                'success': False, 
                'message': f'No se puede eliminar la reserva porque tiene una factura asociada.'
            })
        
        # Eliminar servicios de la reserva primero
        cursor.execute("DELETE FROM reserva_servicios WHERE id_reserva = %s", (id,))
        
        # Eliminar reserva
        cursor.execute("DELETE FROM reservas WHERE id_reserva = %s", (id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return jsonify({'success': True, 'message': 'Reserva eliminada exitosamente.'})
        else:
            return jsonify({'success': False, 'message': 'Reserva no encontrada.'}), 404
            
    except Error as e:
        return jsonify({'success': False, 'message': f'Error eliminando reserva: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/reservas/ver/<int:id>')
def ver_reserva(id):
    """Ver detalles de la reserva"""
    conn = get_db_connection()
    
    if not conn:
        flash('No hay conexión a la base de datos.', 'danger')
        return redirect(url_for('reservas'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener datos principales de la reserva
        cursor.execute("""
            SELECT r.*, 
                   m.id_mascota, m.nombre as mascota_nombre, m.especie, m.raza,
                   c.id_cliente, c.nombre as cliente_nombre, c.apellido as cliente_apellido,
                   c.telefono as cliente_telefono, c.email as cliente_email,
                   e.id_empleado, e.nombre as empleado_nombre, e.apellido as empleado_apellido,
                   e.especialidad as empleado_especialidad
            FROM reservas r
            JOIN mascotas m ON r.id_mascota = m.id_mascota
            JOIN clientes c ON m.id_cliente = c.id_cliente
            JOIN empleados e ON r.id_empleado = e.id_empleado
            WHERE r.id_reserva = %s
        """, (id,))
        reserva = cursor.fetchone()
        
        if not reserva:
            flash('Reserva no encontrada.', 'danger')
            return redirect(url_for('reservas'))
        
        # Calcular tiempo restante si es pendiente
        if reserva['estado'] == 'pendiente' and reserva['fecha_reserva'] > datetime.now():
            tiempo_restante = reserva['fecha_reserva'] - datetime.now()
            dias = tiempo_restante.days
            horas = tiempo_restante.seconds // 3600
            minutos = (tiempo_restante.seconds % 3600) // 60
            reserva['tiempo_restante'] = f"{dias}d {horas}h {minutos}m"
        
        # Obtener servicios de la reserva
        cursor.execute("""
            SELECT rs.*, s.nombre, s.categoria, s.duracion_min
            FROM reserva_servicios rs
            JOIN servicios s ON rs.id_servicio = s.id_servicio
            WHERE rs.id_reserva = %s
        """, (id,))
        servicios = cursor.fetchall()
        
        # Calcular total
        total = sum(s['subtotal'] for s in servicios) if servicios else 0
        
        # Obtener factura asociada si existe
        cursor.execute("""
            SELECT f.* 
            FROM facturas f 
            WHERE f.id_reserva = %s
            ORDER BY f.fecha_emision DESC 
            LIMIT 1
        """, (id,))
        factura = cursor.fetchone()
        
        reserva['servicios'] = servicios
        reserva['total'] = total
        reserva['factura'] = factura
        
        # Obtener historial de cambios de estado
        # (Podrías agregar una tabla de historial_reservas si necesitas más detalle)
        
    except Error as e:
        flash(f'Error obteniendo datos de la reserva: {e}', 'danger')
        return redirect(url_for('reservas'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('reservas/ver.html', reserva=reserva)

@app.route('/reservas/cambiar-estado/<int:id>', methods=['POST'])
def cambiar_estado_reserva(id):
    """Cambiar estado de una reserva"""
    conn = get_db_connection()
    
    if not conn:
        return jsonify({'success': False, 'message': 'No hay conexión a la base de datos.'}), 500
    
    try:
        data = request.get_json()
        nuevo_estado = data.get('estado')
        
        if not nuevo_estado:
            return jsonify({'success': False, 'message': 'Estado no especificado.'}), 400
        
        estados_validos = ['pendiente', 'confirmada', 'en_proceso', 'completada', 'cancelada', 'no_show']
        if nuevo_estado not in estados_validos:
            return jsonify({'success': False, 'message': 'Estado no válido.'}), 400
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE reservas 
            SET estado = %s, fecha_modificacion = NOW()
            WHERE id_reserva = %s
        """, (nuevo_estado, id))
        conn.commit()
        
        if cursor.rowcount > 0:
            return jsonify({
                'success': True, 
                'message': f'Estado cambiado a {nuevo_estado.replace("_", " ").title()}'
            })
        else:
            return jsonify({'success': False, 'message': 'Reserva no encontrada.'}), 404
            
    except Error as e:
        return jsonify({'success': False, 'message': f'Error cambiando estado: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

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