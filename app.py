from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import mysql.connector
import hashlib
from functools import wraps
from mysql.connector import Error

# Cargar variables de entorno
load_dotenv()



def login_required(f):
    """Decorador para requerir inicio de sesión"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id_usuario' not in session:
            flash('Por favor inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorador para requerir rol de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id_usuario' not in session:
            flash('Por favor inicia sesión.', 'warning')
            return redirect(url_for('login'))
        if session.get('rol') != 'admin':
            flash('No tienes permisos para acceder a esta página.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

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

# Middleware para establecer valores por defecto en sesión
@app.before_request
def set_default_session():
    """Establecer valores por defecto en sesión si no existen"""
    if 'rol' not in session:
        session['rol'] = 'admin'  # O 'cajero'
    if 'nombre' not in session:
        session['nombre'] = 'Administrador'
    if 'id_empleado' not in session:
        session['id_empleado'] = 1  # ID del empleado admin
    
    # Pasar la fecha/hora actual a todos los templates
    from datetime import datetime
    app.jinja_env.globals['now'] = datetime.now
# ================= RUTAS =================

@app.route('/')
def index():
    """Página principal - Redirige directamente al dashboard"""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Panel de control principal"""
    conn = get_db_connection()
    stats = {
        'total_clientes': 15,
        'total_mascotas': 42,
        'reservas_hoy': 5,
        'ventas_hoy': 850.0
    }
    
    ultimas_reservas = []  # ← Añadir esta línea
    
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
                
                # OBTENER ÚLTIMAS RESERVAS ← Añadir esta consulta
                cursor.execute("""
                    SELECT r.*, 
                           m.nombre as mascota_nombre, m.especie,
                           c.nombre as cliente_nombre, c.apellido as cliente_apellido,
                           e.nombre as empleado_nombre, e.apellido as empleado_apellido,
                           GROUP_CONCAT(DISTINCT s.nombre SEPARATOR ', ') as servicios_nombres
                    FROM reservas r
                    JOIN mascotas m ON r.id_mascota = m.id_mascota
                    JOIN clientes c ON m.id_cliente = c.id_cliente
                    JOIN empleados e ON r.id_empleado = e.id_empleado
                    LEFT JOIN reserva_servicios rs ON r.id_reserva = rs.id_reserva
                    LEFT JOIN servicios s ON rs.id_servicio = s.id_servicio
                    GROUP BY r.id_reserva
                    ORDER BY r.fecha_reserva DESC
                    LIMIT 10
                """)
                ultimas_reservas = cursor.fetchall()  # ← Obtener las reservas reales
            
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
    
    # Pasar las últimas reservas a la plantilla
    return render_template('dashboard.html', ultimas_reservas=ultimas_reservas, **stats)

def hash_password(password):
    """Generar hash seguro para contraseñas"""
    # Usar sha256 con salt
    salt = "petglow_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    # Si ya está logueado, redirigir al dashboard
    if 'id_usuario' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember') == 'on'
        
        # Validaciones básicas
        if not username or not password:
            flash('Usuario y contraseña son requeridos.', 'danger')
            return render_template('login/login.html')
        
        conn = get_db_connection()
        if not conn:
            flash('Error de conexión a la base de datos.', 'danger')
            return render_template('login/login.html')
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Buscar usuario
            cursor.execute("""
                SELECT u.*, e.nombre, e.apellido, e.email as empleado_email
                FROM usuarios u
                LEFT JOIN empleados e ON u.id_empleado = e.id_empleado
                WHERE u.username = %s AND u.activo = TRUE
            """, (username,))
            
            usuario = cursor.fetchone()
            
            if not usuario:
                flash('Usuario o contraseña incorrectos.', 'danger')
                return render_template('login/login.html')
            
            # Verificar contraseña (comparar hashes)
            hashed_password = hash_password(password)
            if usuario['password_hash'] != hashlib.sha256(password.encode()).hexdigest():
                # Registrar intento fallido
                cursor.execute("""
                    UPDATE usuarios 
                    SET intentos_fallidos = COALESCE(intentos_fallidos, 0) + 1,
                        ultimo_intento_fallido = NOW()
                    WHERE id_usuario = %s
                """, (usuario['id_usuario'],))
                conn.commit()
                
                flash('Usuario o contraseña incorrectos.', 'danger')
                return render_template('login/login.html')
            
            # Verificar si la cuenta está bloqueada por intentos fallidos
            if usuario.get('intentos_fallidos', 0) >= 5:
                # Verificar si han pasado 5 minutos desde el último intento
                cursor.execute("""
                    SELECT TIMESTAMPDIFF(MINUTE, ultimo_intento_fallido, NOW()) as minutos_desde_bloqueo
                    FROM usuarios 
                    WHERE id_usuario = %s
                """, (usuario['id_usuario'],))
                bloqueo = cursor.fetchone()
                
                if bloqueo and bloqueo['minutos_desde_bloqueo'] < 5:
                    flash('Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta nuevamente en 5 minutos.', 'danger')
                    return render_template('login/login.html')
                else:
                    # Restablecer intentos si ya pasaron 5 minutos
                    cursor.execute("""
                        UPDATE usuarios 
                        SET intentos_fallidos = 0,
                            ultimo_intento_fallido = NULL
                        WHERE id_usuario = %s
                    """, (usuario['id_usuario'],))
            
            # Restablecer intentos fallidos
            cursor.execute("""
                UPDATE usuarios 
                SET intentos_fallidos = 0,
                    ultimo_intento_fallido = NULL,
                    ultimo_login = NOW()
                WHERE id_usuario = %s
            """, (usuario['id_usuario'],))
            
            # Registrar historial de login
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            
            cursor.execute("""
                INSERT INTO login_history (id_usuario, ip_address, user_agent)
                VALUES (%s, %s, %s)
            """, (usuario['id_usuario'], ip_address, user_agent))
            
            conn.commit()
            
            # Configurar sesión
            session['id_usuario'] = usuario['id_usuario']
            session['username'] = usuario['username']
            session['rol'] = usuario['rol']
            session['nombre'] = usuario.get('nombre', 'Administrador')
            session['apellido'] = usuario.get('apellido', '')
            session['email'] = usuario.get('empleado_email', '')
            session['last_activity'] = datetime.now().isoformat()
            
            # Configurar duración de sesión
            if remember:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=7)  # 7 días
            else:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(hours=8)  # 8 horas
            
            flash(f'¡Bienvenido(a), {session["nombre"]}!', 'success')
            
            # Redirigir según rol
            if usuario['rol'] == 'admin':
                return redirect(url_for('dashboard'))
            elif usuario['rol'] == 'gerente':
                return redirect(url_for('reservas'))
            elif usuario['rol'] == 'cajero':
                return redirect(url_for('ventas'))
            else:
                return redirect(url_for('dashboard'))
            
        except Error as e:
            flash(f'Error en el inicio de sesión: {str(e)}', 'danger')
            return render_template('login/login.html')
        finally:
            cursor.close()
            conn.close()
    
    # GET: Mostrar formulario de login
    return render_template('login/login.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    # Registrar logout
    if 'id_usuario' in session:
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    UPDATE usuarios 
                    SET ultimo_logout = NOW()
                    WHERE id_usuario = %s
                """, (session['id_usuario'],))
                conn.commit()
            except:
                pass
            finally:
                cursor.close()
                conn.close()
    
    # Limpiar sesión
    session.clear()
    flash('Sesión cerrada exitosamente.', 'info')
    return redirect(url_for('login'))

# ==================== RUTA DE VERIFICACIÓN DE SESIÓN ====================

@app.before_request
def before_request():
    """Verificar sesión antes de cada petición"""
    # Excluir rutas públicas
    public_routes = ['login', 'static']
    if request.endpoint in public_routes:
        return
    
    # Verificar si hay sesión activa
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    
    # Verificar timeout de sesión (8 horas)
    if 'last_activity' in session:
        last_activity = datetime.fromisoformat(session['last_activity'])
        time_difference = datetime.now() - last_activity
        
        if time_difference.total_seconds() > 28800:  # 8 horas en segundos
            session.clear()
            flash('Tu sesión ha expirado por inactividad.', 'warning')
            return redirect(url_for('login'))
    
    # Actualizar última actividad
    session['last_activity'] = datetime.now().isoformat()

   
@app.route('/ventas')
def ventas():
    """Listar ventas/facturas"""
    conn = get_db_connection()
    ventas_list = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT f.*, 
                       c.nombre as cliente_nombre, 
                       c.apellido as cliente_apellido,
                       r.codigo_reserva
                FROM facturas f
                LEFT JOIN clientes c ON f.id_cliente = c.id_cliente
                LEFT JOIN reservas r ON f.id_reserva = r.id_reserva
                ORDER BY f.fecha_emision DESC 
                LIMIT 50
            """)
            ventas_list = cursor.fetchall()
            
            # Formatear estados para mostrar
            for venta in ventas_list:
                estado_clases = {
                    'pendiente': 'bg-warning text-dark',
                    'pagada': 'bg-success',
                    'anulada': 'bg-danger',
                    'credito': 'bg-info text-dark'
                }
                venta['estado_clase'] = estado_clases.get(venta['estado'], 'bg-secondary')
                venta['estado_texto'] = venta['estado'].capitalize()
                
                # Añadir icono según tipo
                if venta['tipo_comprobante'] == 'factura':
                    venta['tipo_icono'] = 'fa-file-invoice'
                    venta['tipo_color'] = 'text-primary'
                else:
                    venta['tipo_icono'] = 'fa-receipt'
                    venta['tipo_color'] = 'text-success'
            
            cursor.close()
        except Error as e:
            flash(f'Error obteniendo ventas: {e}', 'danger')
        finally:
            conn.close()
    
    return render_template('ventas/listar.html', ventas=ventas_list)
    
@app.route('/clientes')
@login_required
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
        # Obtener datos del formulario (¡FALTAN CAMPOS!)
        dni = request.form.get('dni', '').strip()
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        telefono = request.form.get('telefono', '').strip()
        email = request.form.get('email', '').strip()
        
        # ¡AGREGA ESTOS CAMPOS QUE FALTAN!
        direccion = request.form.get('direccion', '').strip()
        notas = request.form.get('notas', '').strip()
        
        if not nombre or not telefono:
            flash('Nombre y teléfono son obligatorios.', 'danger')
            return render_template('clientes/crear.html')
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # ¡ACTUALIZA EL INSERT CON TODOS LOS CAMPOS!
                cursor.execute("""
                    INSERT INTO clientes (dni, nombre, apellido, telefono, email, direccion, notas)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (dni or None, nombre, apellido, telefono, 
                      email or None, direccion or None, notas or None))
                conn.commit()
                
                flash(f'Cliente {nombre} {apellido} creado exitosamente.', 'success')
                return redirect(url_for('clientes'))
                
            except Error as e:
                flash(f'Error creando cliente: {e}', 'danger')
                # Si hay error, volver al formulario con los datos ingresados
                return render_template('clientes/crear.html', 
                                      dni=dni, nombre=nombre, apellido=apellido,
                                      telefono=telefono, email=email,
                                      direccion=direccion, notas=notas)
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
            # Obtener TODOS los datos del formulario
            dni = request.form.get('dni', '').strip()
            nombre = request.form.get('nombre', '').strip()
            apellido = request.form.get('apellido', '').strip()
            telefono = request.form.get('telefono', '').strip()
            email = request.form.get('email', '').strip()
            direccion = request.form.get('direccion', '').strip()
            notas = request.form.get('notas', '').strip()
            
            # Validaciones
            if not nombre or not telefono:
                flash('Nombre y teléfono son obligatorios.', 'danger')
                # Volver a la edición con los datos ingresados
                return render_template('clientes/editar.html', 
                                      cliente={'id_cliente': id, 'dni': dni, 'nombre': nombre, 
                                               'apellido': apellido, 'telefono': telefono,
                                               'email': email, 'direccion': direccion, 'notas': notas})
            
            try:
                # Actualizar cliente con TODOS los campos
                cursor.execute("""
                    UPDATE clientes 
                    SET dni = %s, nombre = %s, apellido = %s, 
                        telefono = %s, email = %s, direccion = %s,
                        notas = %s
                    WHERE id_cliente = %s
                """, (dni or None, nombre, apellido, telefono, 
                      email or None, direccion or None, notas or None, id))
                
                conn.commit()
                
                # Verificar si se actualizó
                if cursor.rowcount > 0:
                    flash(f'Cliente {nombre} {apellido} actualizado exitosamente.', 'success')
                else:
                    flash('No se realizaron cambios o el cliente no existe.', 'warning')
                
                return redirect(url_for('ver_cliente', id=id))
                
            except Error as e:
                conn.rollback()
                flash(f'Error actualizando cliente: {str(e)}', 'danger')
                # Volver a la edición con los datos ingresados
                return render_template('clientes/editar.html', 
                                      cliente={'id_cliente': id, 'dni': dni, 'nombre': nombre, 
                                               'apellido': apellido, 'telefono': telefono,
                                               'email': email, 'direccion': direccion, 'notas': notas})
        
        # GET request: Obtener datos del cliente para mostrar en el formulario
        cursor.execute("SELECT * FROM clientes WHERE id_cliente = %s", (id,))
        cliente = cursor.fetchone()
        
        if not cliente:
            flash('Cliente no encontrado.', 'danger')
            return redirect(url_for('clientes'))
        
    except Error as e:
        flash(f'Error obteniendo datos del cliente: {str(e)}', 'danger')
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
            corte = request.form.get('corte', '').strip()
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
                    fecha_nacimiento, peso, color,corte, caracteristicas, alergias
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                id_cliente, nombre, especie, raza or None, tamano or None,
                fecha_nacimiento_dt, peso_float, color or None, corte or None,
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
            corte = request.form.get('corte', '').strip()
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
            # En la función editar_mascota(), después de obtener los datos y antes del UPDATE:

           # Obtener el corte actual de la mascota
            cursor.execute("SELECT corte FROM mascotas WHERE id_mascota = %s", (id,))
            mascota_actual = cursor.fetchone()
            corte_anterior = mascota_actual['corte'] if mascota_actual else None

            # Registrar en historial si el corte cambió
            if corte and corte != corte_anterior:
                # Obtener id del empleado (ajusta según tu sistema)
                id_empleado = session.get('id_empleado') if 'id_empleado' in session else None
    
                descripcion = f"Cambio de corte: {corte_anterior or 'Sin corte'} → {corte}"
                notas = f"Actualizado al editar mascota"
    
                cursor.execute("""
                    INSERT INTO historial_cortes (id_mascota, tipo_corte, descripcion, id_empleado, notas)
                    VALUES (%s, %s, %s, %s, %s)
                """, (id, corte, descripcion, id_empleado, notas))
            # Actualizar mascota
            cursor.execute("""
                UPDATE mascotas 
                SET id_cliente = %s, nombre = %s, especie = %s, raza = %s, tamano = %s,
                    fecha_nacimiento = %s, peso = %s, color = %s, corte = %s, 
                    caracteristicas = %s, alergias = %s
                WHERE id_mascota = %s
            """, (
                id_cliente, nombre, especie, raza or None, tamano or None,
                fecha_nacimiento_dt, peso_float, color or None, corte or None,
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
        
        # OBTENER HISTORIAL DE CORTES (NUEVO)
        cursor.execute("""
            SELECT 
                hc.*,
                CONCAT(e.nombre, ' ', e.apellido) as empleado_nombre,
                DATE_FORMAT(hc.fecha_registro, '%%d/%%m/%%Y %%H:%%i') as fecha_formateada
            FROM historial_cortes hc
            LEFT JOIN empleados e ON hc.id_empleado = e.id_empleado
            WHERE hc.id_mascota = %s
            ORDER BY hc.fecha_registro DESC
            LIMIT 10
        """, (id,))
        historial_cortes = cursor.fetchall()
        
       # Formatear fechas en Python
        for corte in historial_cortes:
            if corte['fecha_registro']:
                # Formato: día/mes/año hora:minutos
                corte['fecha_formateada'] = corte['fecha_registro'].strftime('%d/%m/%Y %H:%M')
            else:
                corte['fecha_formateada'] = 'Fecha no disponible'
        
    except Error as e:
        flash(f'Error obteniendo datos de la mascota: {e}', 'danger')
        return redirect(url_for('mascotas'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('mascotas/ver.html', 
                         mascota=mascota, 
                         reservas=reservas,
                         historial_cortes=historial_cortes)  # Agregado el historial

def obtener_historial_cortes(id_mascota):
    """Obtener historial de cortes de una mascota"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                hc.*,
                CONCAT(e.nombre, ' ', e.apellido) as empleado_nombre,
                DATE_FORMAT(hc.fecha_registro, '%%d/%%m/%%Y %%H:%%i') as fecha_formateada,
                DATE_FORMAT(hc.fecha_registro, '%%Y-%%m-%%d') as fecha_simple,
                TIME(hc.fecha_registro) as hora
            FROM historial_cortes hc
            LEFT JOIN empleados e ON hc.id_empleado = e.id_empleado
            WHERE hc.id_mascota = %s
            ORDER BY hc.fecha_registro DESC
            LIMIT 20
        """, (id_mascota,))
        
        historial = cursor.fetchall()
        return historial
    except Error as e:
        print(f"Error obteniendo historial de cortes: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

@app.route('/mascotas/<int:id>/registrar-corte', methods=['POST'])
def registrar_corte(id):
    """Registrar un nuevo corte en el historial"""
    if request.method == 'POST':
        conn = get_db_connection()
        if not conn:
            flash('No hay conexión a la base de datos.', 'danger')
            return redirect(url_for('ver_mascota', id=id))
        
        try:
            # Obtener datos del formulario
            tipo_corte = request.form.get('tipo_corte', '').strip()
            descripcion = request.form.get('descripcion', '').strip()
            notas = request.form.get('notas', '').strip()
            
            # Validar
            if not tipo_corte:
                flash('El tipo de corte es obligatorio.', 'danger')
                return redirect(url_for('ver_mascota', id=id))
            
            cursor = conn.cursor()
            
            # 1. Actualizar el corte actual en la mascota
            cursor.execute("""
                UPDATE mascotas SET corte = %s WHERE id_mascota = %s
            """, (tipo_corte, id))
            
            # 2. Registrar en el historial
            # Si tienes sistema de autenticación, obtén el id_empleado de la sesión
            # Si no, puedes usar un valor por defecto o dejarlo NULL
            id_empleado = None  # Cambia esto según tu sistema
            
            cursor.execute("""
                INSERT INTO historial_cortes 
                (id_mascota, tipo_corte, descripcion, id_empleado, notas)
                VALUES (%s, %s, %s, %s, %s)
            """, (id, tipo_corte, descripcion, id_empleado, notas))
            
            conn.commit()
            flash(f'Corte "{tipo_corte}" registrado exitosamente.', 'success')
            
        except Error as e:
            conn.rollback()
            flash(f'Error registrando corte: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()
        
        return redirect(url_for('ver_mascota', id=id))

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
                       m.nombre as mascota_nombre, 
                       m.especie,
                       c.nombre as cliente_nombre, 
                       c.apellido as cliente_apellido,
                       e.nombre as empleado_nombre, 
                       e.apellido as empleado_apellido,
                       GROUP_CONCAT(DISTINCT s.nombre SEPARATOR ', ') as servicios_nombres
                FROM reservas r
                JOIN mascotas m ON r.id_mascota = m.id_mascota
                JOIN clientes c ON m.id_cliente = c.id_cliente
                JOIN empleados e ON r.id_empleado = e.id_empleado
                LEFT JOIN reserva_servicios rs ON r.id_reserva = rs.id_reserva
                LEFT JOIN servicios s ON rs.id_servicio = s.id_servicio
                GROUP BY r.id_reserva
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
                else:
                    reserva['vencida'] = False
            
            cursor.close()
        except Error as e:
            flash(f'Error obteniendo reservas: {e}', 'danger')
            print(f"Error SQL: {e}")  # Para debug
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
                'empleado_apellido': 'López',
                'servicios_nombres': 'Baño Básico, Corte',
                'estado': 'completada',
                'estado_clase': 'bg-success',
                'estado_texto': 'Completada',
                'vencida': False
            }
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
            
            # Validaciones básicas
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
                ahora = datetime.now()
                
                # CORRECCIÓN: Comparar solo año, mes, día, hora y minutos
                fecha_hora_sin_segundos = fecha_hora_dt.replace(second=0, microsecond=0)
                ahora_sin_segundos = ahora.replace(second=0, microsecond=0)
                
                if fecha_hora_sin_segundos < (ahora_sin_segundos - timedelta(minutes=1)):
                    flash('No se pueden crear reservas en fechas u horas pasadas.', 'danger')
                    return redirect(url_for('crear_reserva'))
                
                # Horario de atención LUNES A DOMINGO de 9:00 AM a 6:00 PM
                hora = fecha_hora_dt.hour
                minuto = fecha_hora_dt.minute
                
                # Validar horario: 9:00 AM - 6:00 PM todos los días
                if hora < 9 or (hora == 18 and minuto > 0) or hora >= 19:
                    flash('Horario de atención: Lunes a Domingo de 9:00 AM a 6:00 PM.', 'danger')
                    return redirect(url_for('crear_reserva'))
                
                # Calcular duración total de servicios para verificar disponibilidad
                if servicios:
                    # Obtener duración de todos los servicios seleccionados
                    servicios_tuple = tuple(map(int, servicios))
                    placeholders = ','.join(['%s'] * len(servicios))
                    cursor.execute(f"""
                        SELECT SUM(duracion_min) as duracion_total
                        FROM servicios 
                        WHERE id_servicio IN ({placeholders})
                    """, servicios_tuple)
                    resultado = cursor.fetchone()
                    duracion_total = int(resultado['duracion_total']) if resultado and resultado['duracion_total'] else 60
                    
                    # OBTENER INFORMACIÓN DEL EMPLEADO PARA VERIFICAR SI PUEDE MÚLTIPLES RESERVAS
                    cursor.execute("""
                        SELECT nombre, apellido 
                        FROM empleados 
                        WHERE id_empleado = %s
                    """, (id_empleado,))
                    empleado_info = cursor.fetchone()
                    
                    # Verificar si es administrador/sistema (puede múltiples reservas)
                    es_administrador = False
                    if empleado_info:
                        nombre_completo = f"{empleado_info['nombre']} {empleado_info['apellido']}".lower()
                        if any(keyword in nombre_completo for keyword in ['admin', 'sistema', 'administrador']):
                            es_administrador = True
                    
                    # Verificar disponibilidad del empleado SOLO si NO es administrador
                    if not es_administrador:
                        cursor.execute("""
                            SELECT r.id_reserva, r.fecha_reserva, s.duracion_min
                            FROM reservas r
                            JOIN reserva_servicios rs ON r.id_reserva = rs.id_reserva
                            JOIN servicios s ON rs.id_servicio = s.id_servicio
                            WHERE r.id_empleado = %s 
                            AND r.estado NOT IN ('cancelada', 'no_show')
                            AND DATE(r.fecha_reserva) = DATE(%s)
                        """, (id_empleado, fecha_reserva))
                        
                        reservas_existentes = cursor.fetchall()
                        
                        # Calcular hora de inicio y fin de la nueva reserva
                        nueva_inicio = fecha_hora_dt
                        nueva_fin = fecha_hora_dt + timedelta(minutes=int(duracion_total))
                        
                        # Verificar superposiciones
                        for reserva in reservas_existentes:
                            reserva_inicio = reserva['fecha_reserva']
                            reserva_duracion = int(reserva['duracion_min']) if reserva['duracion_min'] else 60
                            reserva_fin = reserva_inicio + timedelta(minutes=int(reserva_duracion))
                            
                            # Verificar si hay superposición
                            if (nueva_inicio < reserva_fin and nueva_fin > reserva_inicio):
                                flash(f'El empleado ya tiene una reserva de {reserva_inicio.strftime("%H:%M")} a {reserva_fin.strftime("%H:%M")}.', 'danger')
                                return redirect(url_for('crear_reserva'))
                
            except ValueError:
                flash('Formato de fecha u hora inválido.', 'danger')
                return redirect(url_for('crear_reserva'))
            
            # Generar código de reserva único
            cursor.execute("SELECT COALESCE(MAX(id_reserva), 0) + 1 as next_id FROM reservas")
            next_id = cursor.fetchone()['next_id']
            codigo_reserva = f"RES-{datetime.now().strftime('%y%m%d')}-{next_id:04d}"
            
            # Crear reserva
            cursor.execute("""
                INSERT INTO reservas (codigo_reserva, id_mascota, id_empleado, fecha_reserva, notas)
                VALUES (%s, %s, %s, %s, %s)
            """, (codigo_reserva, id_mascota, id_empleado, fecha_hora_dt, notas or None))
            
            id_reserva = cursor.lastrowid
            
            # Agregar servicios a la reserva
            for servicio_id in servicios:
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
        
        # Empleados - Ordenar con administrador primero
        cursor.execute("""
            SELECT id_empleado, nombre, apellido, especialidad
            FROM empleados
            WHERE activo = TRUE
            ORDER BY 
                CASE 
                    WHEN LOWER(nombre) LIKE '%admin%' OR LOWER(nombre) LIKE '%sistema%' THEN 1
                    ELSE 2
                END,
                nombre
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
        
        # Fecha mínima (siempre hoy)
        fecha_minima = datetime.now().strftime('%Y-%m-%d')
        
        # Hora mínima dinámica
        ahora = datetime.now()
        hora_minima = f"{ahora.hour:02d}:{ahora.minute:02d}"
        
        # Ajustar si está fuera de horario
        hora_actual = ahora.hour
        minuto_actual = ahora.minute
        
        if hora_actual > 18 or (hora_actual == 18 and minuto_actual > 0):
            fecha_minima = (ahora + timedelta(days=1)).strftime('%Y-%m-%d')
            hora_minima = '09:00'
        elif hora_actual < 9:
            hora_minima = '09:00'
        else:
            if hora_actual >= 18:
                hora_minima = '17:59'
        
    except Error as e:
        flash(f'Error creando reserva: {e}', 'danger')
        return redirect(url_for('reservas'))
    finally:
        cursor.close()
        conn.close()
    
    # Buscar el ID del empleado "Admin Sistema" para marcarlo como seleccionado
    empleado_admin_id = None
    for empleado in empleados:
        if 'admin' in empleado['nombre'].lower() or 'sistema' in empleado['nombre'].lower():
            empleado_admin_id = empleado['id_empleado']
            break
    
    return render_template('reservas/crear.html', 
                         mascotas=mascotas, 
                         empleados=empleados,
                         servicios_por_categoria=servicios_por_categoria,
                         fecha_minima=fecha_minima,
                         hora_minima=hora_minima,
                         empleado_admin_id=empleado_admin_id)

@app.route('/reservas/editar/<int:id>', methods=['GET', 'POST'])
def editar_reserva(id):
    """Editar reserva existente"""
    conn = get_db_connection()
    
    if not conn:
        flash('No hay conexión a la base de datos.', 'danger')
        return redirect(url_for('reservas'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Primero obtener la reserva actual
        cursor.execute("""
            SELECT r.*, m.nombre as mascota_nombre, m.id_cliente,
                   e.nombre as empleado_nombre, e.apellido as empleado_apellido,
                   m.especie
            FROM reservas r
            JOIN mascotas m ON r.id_mascota = m.id_mascota
            JOIN empleados e ON r.id_empleado = e.id_empleado
            WHERE r.id_reserva = %s
        """, (id,))
        reserva = cursor.fetchone()
        
        if not reserva:
            flash('Reserva no encontrada.', 'danger')
            return redirect(url_for('reservas'))
        
        if request.method == 'POST':
            # Obtener datos del formulario
            id_mascota = request.form.get('id_mascota', '').strip()
            id_empleado = request.form.get('id_empleado', '').strip()
            fecha_reserva = request.form.get('fecha_reserva', '').strip()
            hora_reserva = request.form.get('hora_reserva', '').strip()
            servicios = request.form.getlist('servicios[]')
            notas = request.form.get('notas', '').strip()
            estado = request.form.get('estado', 'pendiente').strip()
            
            # Validaciones básicas
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
                ahora = datetime.now()
                
                # Para edición: solo validar si la nueva fecha/hora es diferente a la actual
                # y si está en el futuro
                fecha_hora_actual = reserva['fecha_reserva']
                
                # Si se cambió la fecha/hora, aplicar validaciones
                if fecha_hora_dt != fecha_hora_actual:
                    # Verificar que no sea fecha/hora pasada
                    if fecha_hora_dt < ahora:
                        flash('No se pueden cambiar a fechas/horas pasadas.', 'danger')
                        return redirect(url_for('editar_reserva', id=id))
                    
                    # Para reservas que ya estaban confirmadas/comenzadas, permitir cambios con menos restricciones
                    if reserva['estado'] in ['pendiente', 'confirmada']:
                        # Solo validar horario de atención
                        dia_semana = fecha_hora_dt.weekday()  # 0 = lunes, 6 = domingo
                        hora = fecha_hora_dt.hour
                        minuto = fecha_hora_dt.minute
                        
                        # Validar domingo
                        if dia_semana == 6:
                            flash('Domingo cerrado. No se pueden programar reservas.', 'danger')
                            return redirect(url_for('editar_reserva', id=id))
                        
                        # Validar sábado (9:00 - 14:00)
                        if dia_semana == 5:
                            if hora < 9 or (hora == 14 and minuto > 0) or hora >= 15:
                                flash('Sábados: horario de atención 9:00 - 14:00.', 'danger')
                                return redirect(url_for('editar_reserva', id=id))
                        
                        # Validar lunes a viernes (9:00 - 18:00)
                        else:
                            if hora < 9 or (hora == 18 and minuto > 0) or hora >= 19:
                                flash('Lunes a Viernes: horario de atención 9:00 - 18:00.', 'danger')
                                return redirect(url_for('editar_reserva', id=id))
                    
                    # Para reservas en estado diferente, validar más estrictamente
                    else:
                        margen_minutos = 30
                        if fecha_hora_dt < (ahora + timedelta(minutes=margen_minutos)):
                            flash(f'Las reservas deben hacerse con al menos {margen_minutos} minutos de anticipación.', 'danger')
                            return redirect(url_for('editar_reserva', id=id))
                        
                        # Validar horario de atención
                        dia_semana = fecha_hora_dt.weekday()
                        hora = fecha_hora_dt.hour
                        minuto = fecha_hora_dt.minute
                        
                        # Validar domingo
                        if dia_semana == 6:
                            flash('Domingo cerrado.', 'danger')
                            return redirect(url_for('editar_reserva', id=id))
                        
                        # Validar sábado (9:00 - 14:00)
                        if dia_semana == 5:
                            if hora < 9 or (hora == 14 and minuto > 0) or hora >= 15:
                                flash('Sábados: horario de atención 9:00 - 14:00.', 'danger')
                                return redirect(url_for('editar_reserva', id=id))
                        
                        # Validar lunes a viernes (9:00 - 18:00)
                        else:
                            if hora < 9 or (hora == 18 and minuto > 0) or hora >= 19:
                                flash('Lunes a Viernes: horario de atención 9:00 - 18:00.', 'danger')
                                return redirect(url_for('editar_reserva', id=id))
                
                # Verificar disponibilidad del empleado si se cambió empleado o fecha/hora
                if id_empleado != str(reserva['id_empleado']) or fecha_hora_dt != fecha_hora_actual:
                    # OBTENER INFORMACIÓN DEL EMPLEADO
                    cursor.execute("SELECT nombre, apellido FROM empleados WHERE id_empleado = %s", (id_empleado,))
                    empleado_info = cursor.fetchone()
    
                    es_administrador = False
                    if empleado_info:
                        nombre_completo = f"{empleado_info['nombre']} {empleado_info['apellido']}".lower()
                        if any(keyword in nombre_completo for keyword in ['admin', 'sistema', 'administrador']):
                            es_administrador = True    
                    # Calcular duración total de servicios para verificar disponibilidad
                    if servicios:
                        servicios_tuple = tuple(map(int, servicios))
                        placeholders = ','.join(['%s'] * len(servicios))
                        cursor.execute(f"""
                            SELECT SUM(duracion_min) as duracion_total
                            FROM servicios 
                            WHERE id_servicio IN ({placeholders})
                        """, servicios_tuple)
                        resultado = cursor.fetchone()
                        duracion_total = int(resultado['duracion_total']) if resultado and resultado['duracion_total'] else 60
                        
                        # Verificar disponibilidad del empleado (excluyendo esta reserva)
                        cursor.execute("""
                            SELECT r.id_reserva, r.fecha_reserva, s.duracion_min
                            FROM reservas r
                            JOIN reserva_servicios rs ON r.id_reserva = rs.id_reserva
                            JOIN servicios s ON rs.id_servicio = s.id_servicio
                            WHERE r.id_empleado = %s 
                            AND r.id_reserva != %s
                            AND r.estado NOT IN ('cancelada', 'no_show')
                            AND DATE(r.fecha_reserva) = DATE(%s)
                        """, (id_empleado, id, fecha_reserva))
                        
                        reservas_existentes = cursor.fetchall()
                        
                        # Calcular hora de inicio y fin de la nueva reserva
                        nueva_inicio = fecha_hora_dt
                        nueva_fin = fecha_hora_dt + timedelta(minutes=int(duracion_total))
                        
                        # Verificar superposiciones
                        for reserva_existente in reservas_existentes:
                            reserva_inicio = reserva_existente['fecha_reserva']
                            reserva_duracion = int(reserva_existente['duracion_min']) if reserva_existente['duracion_min'] else 60
                            reserva_fin = reserva_inicio + timedelta(minutes=int(reserva_duracion))
                            
                            # Verificar si hay superposición
                            if (nueva_inicio < reserva_fin and nueva_fin > reserva_inicio):
                                flash(f'El empleado ya tiene una reserva de {reserva_inicio.strftime("%H:%M")} a {reserva_fin.strftime("%H:%M")}.', 'danger')
                                return redirect(url_for('editar_reserva', id=id))
                
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
        
        # Calcular si la reserva está vencida
        ahora = datetime.now()
        reserva['vencida'] = fecha_hora < ahora and reserva['estado'] in ['pendiente', 'confirmada']
        
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
# ==================== RUTAS API PARA EMPLEADOS ====================

@app.route('/api/empleado/info')
@login_required
def api_empleado_info():
    """Obtener información del empleado actual"""
    id_empleado = session.get('id_empleado')
    
    if not id_empleado:
        return jsonify({'success': False, 'message': 'No se encontró empleado'})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Error de conexión'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener información del empleado
        cursor.execute("""
            SELECT e.id_empleado, e.nombre, e.apellido, e.especialidad, e.email, e.telefono,
                   e.fecha_contratacion, u.username, u.rol
            FROM empleados e
            LEFT JOIN usuarios u ON e.id_empleado = u.id_empleado
            WHERE e.id_empleado = %s
        """, (id_empleado,))
        
        empleado = cursor.fetchone()
        
        if empleado:
            return jsonify({
                'success': True,
                'id': empleado['id_empleado'],
                'nombre': f"{empleado['nombre']} {empleado['apellido']}",
                'nombre_corto': empleado['nombre'],
                'apellido': empleado['apellido'],
                'especialidad': empleado['especialidad'],
                'email': empleado['email'],
                'telefono': empleado['telefono'],
                'username': empleado.get('username'),
                'rol': empleado.get('rol'),
                'fecha_contratacion': empleado['fecha_contratacion'].strftime('%d/%m/%Y') if empleado['fecha_contratacion'] else None
            })
        else:
            return jsonify({'success': False, 'message': 'Empleado no encontrado'})
            
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
# ==================== VISTA DE EMPLEADOS ====================

@app.route('/empleado/reservas')
@login_required
def empleado_reservas():
    """Vista especial para empleados - Ver sus reservas asignadas"""
    id_empleado = session.get('id_empleado')
    
    if not id_empleado:
        flash('No se encontró información del empleado.', 'danger')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    if not conn:
        flash('No hay conexión a la base de datos.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener reservas asignadas a este empleado
        # Hoy + próximos 7 días
        cursor.execute("""
            SELECT 
                r.*,
                m.id_mascota,
                m.nombre as mascota_nombre,
                m.especie,
                m.raza,
                m.color,
                m.tamano,
                c.id_cliente,
                c.nombre as cliente_nombre,
                c.apellido as cliente_apellido,
                c.telefono as cliente_telefono,
                CONCAT(e.nombre, ' ', e.apellido) as empleado_nombre,
                GROUP_CONCAT(DISTINCT s.nombre SEPARATOR ', ') as servicios_nombres,
                SUM(s.duracion_min) as duracion_total
            FROM reservas r
            JOIN mascotas m ON r.id_mascota = m.id_mascota
            JOIN clientes c ON m.id_cliente = c.id_cliente
            JOIN empleados e ON r.id_empleado = e.id_empleado
            LEFT JOIN reserva_servicios rs ON r.id_reserva = rs.id_reserva
            LEFT JOIN servicios s ON rs.id_servicio = s.id_servicio
            WHERE r.id_empleado = %s
            AND DATE(r.fecha_reserva) BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
            AND r.estado IN ('pendiente', 'confirmada', 'en_proceso')
            GROUP BY r.id_reserva
            ORDER BY 
                CASE r.estado 
                    WHEN 'en_proceso' THEN 1
                    WHEN 'confirmada' THEN 2
                    WHEN 'pendiente' THEN 3
                    ELSE 4
                END,
                r.fecha_reserva ASC
        """, (id_empleado,))
        
        reservas_asignadas = cursor.fetchall()
        
        # Obtener estadísticas
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes,
                SUM(CASE WHEN estado = 'confirmada' THEN 1 ELSE 0 END) as confirmadas,
                SUM(CASE WHEN estado = 'en_proceso' THEN 1 ELSE 0 END) as en_proceso
            FROM reservas 
            WHERE id_empleado = %s 
            AND DATE(fecha_reserva) >= CURDATE()
            AND estado IN ('pendiente', 'confirmada', 'en_proceso')
        """, (id_empleado,))
        
        estadisticas = cursor.fetchone()
        
        # Obtener información del empleado
        cursor.execute("""
            SELECT nombre, apellido, especialidad 
            FROM empleados 
            WHERE id_empleado = %s
        """, (id_empleado,))
        
        empleado_info = cursor.fetchone()
        
    except Error as e:
        flash(f'Error obteniendo reservas: {e}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('empleados/reservas.html', 
                         reservas=reservas_asignadas,
                         estadisticas=estadisticas,
                         empleado=empleado_info)

@app.route('/api/empleado/reservas/<int:id>/estado', methods=['POST'])
@login_required
def api_cambiar_estado_reserva_empleado(id):
    """API para que empleados cambien estado de sus reservas"""
    if 'id_usuario' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    data = request.get_json()
    nuevo_estado = data.get('estado')
    
    if not nuevo_estado:
        return jsonify({'success': False, 'message': 'Estado no especificado.'}), 400
    
    estados_validos = ['confirmada', 'en_proceso', 'completada', 'cancelada']
    if nuevo_estado not in estados_validos:
        return jsonify({'success': False, 'message': 'Estado no válido.'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'No hay conexión a la base de datos.'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        id_empleado = session.get('id_empleado')
        
        # Verificar que la reserva pertenece a este empleado
        cursor.execute("""
            SELECT id_reserva FROM reservas 
            WHERE id_reserva = %s AND id_empleado = %s
        """, (id, id_empleado))
        
        reserva = cursor.fetchone()
        
        if not reserva:
            return jsonify({'success': False, 'message': 'Reserva no encontrada o no asignada.'}), 404
        
        # Cambiar estado
        cursor.execute("""
            UPDATE reservas 
            SET estado = %s, fecha_modificacion = NOW()
            WHERE id_reserva = %s
        """, (nuevo_estado, id))
        
        conn.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Estado cambiado a {nuevo_estado.replace("_", " ").title()}',
            'estado': nuevo_estado
        })
            
    except Error as e:
        return jsonify({'success': False, 'message': f'Error cambiando estado: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empleado/reservas/hoy')
@login_required
def api_reservas_hoy_empleado():
    """API para obtener reservas de hoy del empleado (para pantallas de trabajo)"""
    id_empleado = session.get('id_empleado')
    
    if not id_empleado:
        return jsonify({'success': False, 'message': 'No se encontró empleado'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'No hay conexión a la base de datos.'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Reservas de hoy para este empleado
        cursor.execute("""
            SELECT 
                r.id_reserva,
                r.codigo_reserva,
                r.fecha_reserva,
                r.estado,
                r.notas,
                m.nombre as mascota_nombre,
                m.especie,
                m.raza,
                m.color,
                c.nombre as cliente_nombre,
                c.apellido as cliente_apellido,
                c.telefono as cliente_telefono,
                GROUP_CONCAT(DISTINCT s.nombre SEPARATOR ', ') as servicios_nombres,
                SUM(s.duracion_min) as duracion_total
            FROM reservas r
            JOIN mascotas m ON r.id_mascota = m.id_mascota
            JOIN clientes c ON m.id_cliente = c.id_cliente
            LEFT JOIN reserva_servicios rs ON r.id_reserva = rs.id_reserva
            LEFT JOIN servicios s ON rs.id_servicio = s.id_servicio
            WHERE r.id_empleado = %s
            AND DATE(r.fecha_reserva) = CURDATE()
            AND r.estado IN ('pendiente', 'confirmada', 'en_proceso')
            GROUP BY r.id_reserva
            ORDER BY r.fecha_reserva ASC
        """, (id_empleado,))
        
        reservas_hoy = cursor.fetchall()
        
        # Formatear datos
        for reserva in reservas_hoy:
            # Estado con clase CSS
            estado_clases = {
                'pendiente': 'warning',
                'confirmada': 'info',
                'en_proceso': 'primary',
                'completada': 'success',
                'cancelada': 'danger'
            }
            reserva['estado_color'] = estado_clases.get(reserva['estado'], 'secondary')
            
            # Formatear fecha/hora
            if reserva['fecha_reserva']:
                fecha_obj = reserva['fecha_reserva']
                if isinstance(fecha_obj, datetime):
                    reserva['hora_str'] = fecha_obj.strftime('%H:%M')
                    reserva['fecha_str'] = fecha_obj.strftime('%d/%m/%Y')
                    
                    # Calcular minutos restantes
                    ahora = datetime.now()
                    diferencia = (fecha_obj - ahora).total_seconds() / 60
                    reserva['minutos_restantes'] = int(diferencia) if diferencia > 0 else 0
                    reserva['es_proxima'] = 0 < diferencia <= 30
        
        return jsonify({
            'success': True,
            'reservas': reservas_hoy,
            'total': len(reservas_hoy),
            'hoy': datetime.now().strftime('%d/%m/%Y')
        })
        
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/empleado/monitor')
@login_required
def empleado_monitor():
    """Pantalla de monitor/kiosk para empleados (solo lectura, auto-refresh)"""
    return render_template('empleados/monitor.html')

@app.route('/api/mascota/<int:id>')
def obtener_datos_mascota(id):
    """Obtener datos completos de una mascota para AJAX"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'No hay conexión a la base de datos'})
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener datos completos de la mascota
        cursor.execute("""
            SELECT 
                m.*, 
                c.nombre as cliente_nombre, 
                c.apellido as cliente_apellido,
                c.telefono as cliente_telefono,
                c.email as cliente_email,
                TIMESTAMPDIFF(YEAR, m.fecha_nacimiento, CURDATE()) as edad_anios,
                TIMESTAMPDIFF(MONTH, m.fecha_nacimiento, CURDATE()) % 12 as edad_meses
            FROM mascotas m
            JOIN clientes c ON m.id_cliente = c.id_cliente
            WHERE m.id_mascota = %s
        """, (id,))
        
        mascota = cursor.fetchone()
        
        if not mascota:
            return jsonify({'success': False, 'error': 'Mascota no encontrada'})
        
        # OBTENER HISTORIAL DE CORTES - ¡SOLUCIÓN SIMPLE!
        cursor.execute("""
            SELECT 
                hc.*,
                CONCAT(e.nombre, ' ', e.apellido) as empleado_nombre,
                hc.fecha_registro
            FROM historial_cortes hc
            LEFT JOIN empleados e ON hc.id_empleado = e.id_empleado
            WHERE hc.id_mascota = %s
            ORDER BY hc.fecha_registro DESC
            LIMIT 10
        """, (id,))
        
        historial_cortes = cursor.fetchall()
        
        # Formatear fechas en Python - ¡EXACTAMENTE COMO EN VER_MASCOTA!
        for corte in historial_cortes:
            if corte['fecha_registro']:
                # Formato: día/mes/año hora:minutos
                corte['fecha_formateada'] = corte['fecha_registro'].strftime('%d/%m/%Y %H:%M')
            else:
                corte['fecha_formateada'] = 'Fecha no disponible'
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'mascota': mascota,
            'historial_cortes': historial_cortes
        })
        
    except Exception as e:
        print(f"Error al obtener datos de mascota: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/mascotas/actualizar-datos/<int:id>', methods=['POST'])
def actualizar_datos_mascota_reserva(id):
    """Actualizar datos de mascota desde la reserva"""
    print(f"Recibiendo actualización para mascota ID: {id}")
    print(f"Datos recibidos: {request.form}")
    
    if request.method == 'POST':
        conn = get_db_connection()
        if not conn:
            print("ERROR: No hay conexión a la base de datos")
            return jsonify({'success': False, 'error': 'No hay conexión a la base de datos'})
        
        try:
            # Obtener datos del formulario con valores por defecto
            raza = request.form.get('raza', '').strip()
            color = request.form.get('color', '').strip()
            corte = request.form.get('corte', '').strip()
            tamano = request.form.get('tamano', '').strip().lower()
            peso = request.form.get('peso', '').strip()
            caracteristicas = request.form.get('caracteristicas', '').strip()
            alergias = request.form.get('alergias', '').strip()
            
            print(f"Procesando datos: raza={raza}, color={color}, corte={corte}, tamano={tamano}, peso={peso}")
            
            # Validar campos requeridos
            if not raza:
                return jsonify({'success': False, 'error': 'El campo Raza es obligatorio'})
            if not color:
                return jsonify({'success': False, 'error': 'El campo Color es obligatorio'})
            
            cursor = conn.cursor(dictionary=True)
            
            # Verificar si la mascota existe
            cursor.execute("SELECT id_mascota, corte FROM mascotas WHERE id_mascota = %s", (id,))
            mascota_existente = cursor.fetchone()
            
            if not mascota_existente:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': 'Mascota no encontrada'})
            
            corte_anterior = mascota_existente.get('corte', None)
            
            # Preparar valores para la actualización
            valores = []
            campos = []
            
            # Agregar campos dinámicamente
            if raza:
                campos.append("raza = %s")
                valores.append(raza)
            
            if color:
                campos.append("color = %s")
                valores.append(color)
            
            if corte:
                campos.append("corte = %s")
                valores.append(corte)
            
            if tamano in ['pequeño', 'mediano', 'grande', 'gigante', 'pequeno']:
                # Normalizar "pequeno" sin ñ
                if tamano == 'pequeno':
                    tamano = 'pequeño'
                campos.append("tamano = %s")
                valores.append(tamano)
            
            if peso:
                try:
                    peso_float = float(peso)
                    campos.append("peso = %s")
                    valores.append(peso_float)
                except ValueError:
                    print(f"Advertencia: Peso no válido: {peso}")
            
            if caracteristicas:
                campos.append("caracteristicas = %s")
                valores.append(caracteristicas)
            
            if alergias:
                campos.append("alergias = %s")
                valores.append(alergias)
            
            # NOTA: Eliminamos fecha_actualizacion ya que no existe en tu tabla
            # Si necesitas una columna de fecha de actualización, puedes usar:
            # campos.append("updated_at = NOW()")
            # pero primero verifica qué columnas tienes en tu tabla
            
            # Agregar ID al final para la condición WHERE
            valores.append(id)
            
            # Construir y ejecutar la consulta
            if campos:
                sql = f"UPDATE mascotas SET {', '.join(campos)} WHERE id_mascota = %s"
                print(f"SQL ejecutado: {sql}")
                print(f"Valores: {valores}")
                
                cursor.execute(sql, valores)
                
                # Registrar en historial si el corte cambió
                if corte and corte != corte_anterior:
                    id_empleado = session.get('id_empleado') if 'id_empleado' in session else None
                    
                    descripcion = f"Cambio de corte: {corte_anterior or 'Sin corte'} → {corte}"
                    notas = f"Actualizado desde el sistema de reservas"
                    
                    try:
                        cursor.execute("""
                            INSERT INTO historial_cortes 
                            (id_mascota, tipo_corte, descripcion, id_empleado, notas, fecha_registro)
                            VALUES (%s, %s, %s, %s, %s, NOW())
                        """, (id, corte, descripcion, id_empleado, notas))
                        print("Registro en historial_cortes creado")
                    except Exception as hist_error:
                        print(f"Advertencia: No se pudo registrar en historial: {hist_error}")
                        # Continuar aunque falle el historial
                
                conn.commit()
                filas_afectadas = cursor.rowcount
                print(f"Filas afectadas: {filas_afectadas}")
                
                cursor.close()
                conn.close()
                
                if filas_afectadas > 0:
                    return jsonify({
                        'success': True, 
                        'message': 'Datos actualizados correctamente',
                        'corte_anterior': corte_anterior,
                        'corte_nuevo': corte
                    })
                else:
                    return jsonify({'success': False, 'error': 'No se realizaron cambios'})
            else:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': 'No se proporcionaron datos para actualizar'})
            
        except mysql.connector.Error as e:
            print(f"Error de MySQL: {str(e)}")
            if 'cursor' in locals() and cursor:
                cursor.close()
            if conn:
                conn.close()
            return jsonify({'success': False, 'error': f'Error de base de datos: {str(e)}'})
        except Exception as e:
            print(f"Error general: {str(e)}")
            import traceback
            traceback.print_exc()
            if 'cursor' in locals() and cursor:
                cursor.close()
            if conn:
                conn.close()
            return jsonify({'success': False, 'error': f'Error interno: {str(e)}'})

@app.route('/facturas/<int:id>')
def ver_factura(id):
    """Ver detalles de la factura"""
    conn = get_db_connection()
    
    if not conn:
        flash('No hay conexión a la base de datos.', 'danger')
        return redirect(url_for('ventas'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 1. Obtener datos de la factura
        cursor.execute("""
            SELECT f.*, 
                   c.nombre as cliente_nombre, c.apellido as cliente_apellido,
                   c.dni as cliente_dni, c.direccion as cliente_direccion,
                   r.codigo_reserva, m.nombre as mascota_nombre
            FROM facturas f
            LEFT JOIN clientes c ON f.id_cliente = c.id_cliente
            LEFT JOIN reservas r ON f.id_reserva = r.id_reserva
            LEFT JOIN mascotas m ON r.id_mascota = m.id_mascota
            WHERE f.id_factura = %s
        """, (id,))
        factura = cursor.fetchone()
        
        if not factura:
            flash('Factura no encontrada.', 'danger')
            return redirect(url_for('ventas'))
        
        # 2. Obtener servicios y productos
        cursor.execute("""
            SELECT fs.*, s.categoria
            FROM factura_servicios fs
            LEFT JOIN servicios s ON fs.id_servicio = s.id_servicio
            WHERE fs.id_factura = %s
        """, (id,))
        servicios = cursor.fetchall()
        
        cursor.execute("""
            SELECT fp.*, p.categoria
            FROM factura_productos fp
            LEFT JOIN productos p ON fp.id_producto = p.id_producto
            WHERE fp.id_factura = %s
        """, (id,))
        productos = cursor.fetchall()
        
        # 3. Calcular totales desde los detalles
        total_servicios = sum(float(s['subtotal']) for s in servicios) if servicios else 0.0
        total_productos = sum(float(p['subtotal']) for p in productos) if productos else 0.0
        
        # 4. Si la factura ya tiene totales calculados, usarlos
        if factura['total'] and factura['total'] > 0:
            total = float(factura['total'])
            subtotal = float(factura['subtotal']) if factura['subtotal'] else 0.0
            igv = float(factura['igv']) if factura['igv'] else 0.0
        else:
            # Calcular según tipo de comprobante
            total_base = total_servicios + total_productos
            
            if factura['tipo_comprobante'] == 'factura':
                # Para factura: separar IGV
                subtotal = total_base / 1.18
                igv = subtotal * 0.18
                total = subtotal + igv
            else:
                # Para boleta: no hay IGV separado
                subtotal = total_base
                igv = 0.00
                total = total_base
        
        # 5. Asignar valores a la factura
        factura['servicios'] = servicios
        factura['productos'] = productos
        factura['total_servicios'] = round(total_servicios, 2)
        factura['total_productos'] = round(total_productos, 2)
        factura['subtotal'] = round(subtotal, 2)
        factura['igv'] = round(igv, 2)
        factura['total'] = round(total, 2)
        
        # 6. Formatear fecha
        if factura['fecha_emision']:
            factura['fecha_emision_str'] = factura['fecha_emision'].strftime('%d/%m/%Y %H:%M')
        
        # 7. Verificar pagos
        cursor.execute("""
            SELECT * FROM movimientos_caja 
            WHERE id_factura = %s
            ORDER BY fecha_movimiento DESC
        """, (id,))
        pagos = cursor.fetchall()
        
        factura['pagos'] = pagos
        
    except Error as e:
        flash(f'Error obteniendo factura: {e}', 'danger')
        return redirect(url_for('ventas'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('facturas/ver.html', factura=factura)
    
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
        
        # Obtener factura asociada si existe - ¡IMPORTANTE!
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
        reserva['factura'] = factura  # ← AÑADE ESTO
        
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
# ================= RUTAS DE FACTURACIÓN =================

@app.route('/reservas/<int:id>/facturar', methods=['GET', 'POST'])
def facturar_reserva(id):
    """Crear factura a partir de una reserva"""
    conn = get_db_connection()
    
    if not conn:
        flash('No hay conexión a la base de datos.', 'danger')
        return redirect(url_for('ver_reserva', id=id))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 1. Verificar que la reserva existe y está completada
        cursor.execute("""
            SELECT r.*, 
                   m.id_mascota, m.nombre as mascota_nombre,
                   c.id_cliente, c.nombre as cliente_nombre, c.apellido as cliente_apellido,
                   c.dni as cliente_dni
            FROM reservas r
            JOIN mascotas m ON r.id_mascota = m.id_mascota
            JOIN clientes c ON m.id_cliente = c.id_cliente
            WHERE r.id_reserva = %s
        """, (id,))
        reserva = cursor.fetchone()
        
        if not reserva:
            flash('Reserva no encontrada.', 'danger')
            return redirect(url_for('reservas'))
        
        if reserva['estado'] != 'completada':
            flash('Solo se pueden facturar reservas completadas.', 'warning')
            return redirect(url_for('ver_reserva', id=id))
        
        # 2. Verificar que no tenga factura ya
        cursor.execute("SELECT * FROM facturas WHERE id_reserva = %s", (id,))
        factura_existente = cursor.fetchone()
        
        if factura_existente:
            flash('Esta reserva ya tiene una factura.', 'info')
            return redirect(url_for('ver_factura', id=factura_existente['id_factura']))
        
        if request.method == 'POST':
            # 3. Obtener datos del formulario
            tipo_comprobante = request.form.get('tipo_comprobante', 'boleta')
            metodo_pago = request.form.get('metodo_pago', 'efectivo')
            notas = request.form.get('notas', '').strip()
            
            # 4. Obtener servicios para calcular totales
            cursor.execute("""
                SELECT SUM(rs.subtotal) as total_servicios
                FROM reserva_servicios rs
                WHERE rs.id_reserva = %s
            """, (id,))
            total_servicios = cursor.fetchone()['total_servicios'] or 0
            total_servicios = float(total_servicios)
            
            # 5. Calcular según tipo de comprobante
            if tipo_comprobante == 'factura':
                # Para factura: calcular IGV (18%)
                subtotal = total_servicios / 1.18  # Base imponible
                igv = subtotal * 0.18  # IGV 18%
                total = subtotal + igv
            else:
                # Para boleta: no hay IGV
                subtotal = total_servicios  # Base imponible = total
                igv = 0.00
                total = total_servicios
            
            # 6. Generar número de factura/boleta
            cursor.execute("SELECT COALESCE(MAX(id_factura), 0) + 1 as next_id FROM facturas")
            next_id = cursor.fetchone()['next_id']
            
            serie = 'B001' if tipo_comprobante == 'boleta' else 'F001'
            numero = f"{serie}-{next_id:04d}"
            
            # 7. Crear factura con todos los campos CORREGIDOS
            cursor.execute("""
                INSERT INTO facturas (
                    serie, numero, tipo_comprobante, id_cliente, id_reserva,
                    metodo_pago, notas, id_empleado_cajero, estado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (serie, numero, tipo_comprobante, reserva['id_cliente'], 
                id, metodo_pago, notas or None, 1, 'pendiente'))
            
            id_factura = cursor.lastrowid
            
            # 8. Copiar servicios de reserva a factura
            cursor.execute("""
                INSERT INTO factura_servicios (id_factura, id_servicio, descripcion, precio_unitario, cantidad)
                SELECT 
                %s,
                rs.id_servicio,
                s.nombre,
                rs.precio_unitario,
                rs.cantidad
            FROM reserva_servicios rs
            JOIN servicios s ON rs.id_servicio = s.id_servicio
            WHERE rs.id_reserva = %s
        """, (id_factura, id))
            
            conn.commit()
            
            flash(f'{tipo_comprobante.capitalize()} {numero} creada exitosamente.', 'success')
            return redirect(url_for('ver_factura', id=id_factura))
        
        # GET: Mostrar formulario de facturación
        # Obtener servicios de la reserva para mostrar resumen
        cursor.execute("""
            SELECT s.*, rs.precio_unitario, rs.cantidad, rs.subtotal
            FROM reserva_servicios rs
            JOIN servicios s ON rs.id_servicio = s.id_servicio
            WHERE rs.id_reserva = %s
        """, (id,))
        servicios = cursor.fetchall()
        
        total = sum(float(s['subtotal']) for s in servicios) if servicios else 0
        
        # Calcular subtotal (sin IGV) - Solo para mostrar en formulario
        subtotal = total / 1.18  # Perú tiene 18% IGV
        igv = total - subtotal
        
        # Verificar si cliente tiene DNI para factura
        puede_factura = bool(reserva['cliente_dni'])
        
    except Error as e:
        flash(f'Error creando factura: {e}', 'danger')
        return redirect(url_for('ver_reserva', id=id))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('facturas/crear.html', 
                         reserva=reserva, 
                         servicios=servicios,
                         total=round(total, 2),
                         subtotal=round(subtotal, 2),
                         igv=round(igv, 2),
                         puede_factura=puede_factura)
# ================= RUTAS DE REPORTES Y CONFIGURACIÓN =================
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

# ============================================
# RUTAS PARA MANEJO DE CAJA
# ============================================

@app.route('/caja/apertura', methods=['GET', 'POST'])
def apertura_caja():
    from datetime import datetime
    """Abrir caja del día"""
    if request.method == 'POST':
        try:
            monto_apertura = float(request.form.get('monto_apertura', 0))
            id_empleado = session.get('id_empleado', 1)  # Usa el ID de la sesión
            
            if monto_apertura <= 0:
                flash('El monto de apertura debe ser mayor a 0.', 'danger')
                return redirect(url_for('apertura_caja'))
            
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                
                # Verificar si ya hay caja abierta hoy para este empleado
                cursor.execute("""
                    SELECT id_caja FROM caja_diaria 
                    WHERE fecha = CURDATE() 
                    AND id_empleado_cajero = %s
                    AND estado = 'abierta'
                """, (id_empleado,))
                
                caja_existente = cursor.fetchone()
                
                if caja_existente:
                    flash('Ya tienes una caja abierta para hoy.', 'warning')
                else:
                    # Crear nueva caja
                    cursor.execute("""
                        INSERT INTO caja_diaria 
                        (fecha, id_empleado_cajero, monto_apertura, estado, hora_apertura)
                        VALUES (CURDATE(), %s, %s, 'abierta', NOW())
                    """, (id_empleado, monto_apertura))
                    
                    conn.commit()
                    flash(f'✅ Caja abierta con S/ {monto_apertura:.2f} exitosamente.', 'success')
                    return redirect(url_for('dashboard'))
                
                cursor.close()
                conn.close()
            else:
                flash('❌ Error de conexión a la base de datos.', 'danger')
            
        except Exception as e:
            flash(f'❌ Error al abrir caja: {str(e)}', 'danger')
    
    # GET request: mostrar formulario
    date_now = datetime.now()
    return render_template('caja/apertura.html', date_now=date_now)

def safe_float(value, default=0.0):
    """Convertir cualquier valor a float de forma segura"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


@app.route('/caja/cierre', methods=['GET', 'POST'])
def cierre_caja():
    """Cerrar caja del día - VERSIÓN CORREGIDA"""
    conn = get_db_connection()
    
    if not conn:
        flash('❌ Error de conexión a la base de datos.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        id_empleado = session.get('id_empleado', 1)
        
        # Obtener caja abierta actual
        cursor.execute("""
            SELECT c.*, CONCAT(e.nombre, ' ', e.apellido) as cajero
            FROM caja_diaria c
            JOIN empleados e ON c.id_empleado_cajero = e.id_empleado
            WHERE fecha = CURDATE() 
            AND estado = 'abierta'
            AND c.id_empleado_cajero = %s
        """, (id_empleado,))
        
        caja_actual = cursor.fetchone()
        
        if not caja_actual:
            flash('ℹ️ No tienes caja abierta para hoy.', 'info')
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            monto_cierre = float(request.form.get('monto_cierre', 0))
            observaciones = request.form.get('observaciones', '')
            
            # Convertir todos los valores a float
            monto_apertura = safe_float(caja_actual['monto_apertura'])
            venta_efectivo = safe_float(caja_actual['venta_efectivo'])
            venta_tarjeta = safe_float(caja_actual['venta_tarjeta'])
            venta_digital = safe_float(caja_actual['venta_digital'])
            total_ventas = safe_float(caja_actual['total_ventas'])
            
            # Calcular diferencia
            efectivo_esperado = monto_apertura + venta_efectivo
            diferencia = monto_cierre - efectivo_esperado
            
            print(f"🔢 Valores calculados:")
            print(f"   Monto cierre: {monto_cierre}")
            print(f"   Monto apertura: {monto_apertura}")
            print(f"   Venta efectivo: {venta_efectivo}")
            print(f"   Efectivo esperado: {efectivo_esperado}")
            print(f"   Diferencia: {diferencia}")
            
            # Actualizar caja
            cursor.execute("""
                UPDATE caja_diaria 
                SET monto_cierre = %s,
                    diferencia = %s,
                    observaciones = %s,
                    estado = 'cerrada',
                    hora_cierre = NOW()
                WHERE id_caja = %s
            """, (monto_cierre, diferencia, observaciones, caja_actual['id_caja']))
            
            conn.commit()
            
            # Determinar mensaje según diferencia
            if abs(diferencia) < 0.01:  # Menos de 1 céntimo
                mensaje = f'✅ Caja cerrada perfectamente. Sin diferencia.'
            elif diferencia > 0:
                mensaje = f'✅ Caja cerrada. Sobrante: S/ {diferencia:.2f}'
            else:
                mensaje = f'✅ Caja cerrada. Faltante: S/ {abs(diferencia):.2f}'
            
            flash(mensaje, 'success')
            return redirect(url_for('dashboard'))
        
        # GET request: preparar datos para la plantilla
        # Convertir todos los valores Decimal a float para la plantilla
        for key in ['monto_apertura', 'venta_efectivo', 'venta_tarjeta', 
                   'venta_digital', 'total_ventas', 'monto_cierre', 'diferencia']:
            if key in caja_actual:
                caja_actual[f'{key}_float'] = safe_float(caja_actual[key])
        
        # Calcular efectivo esperado para mostrar
        efectivo_esperado = safe_float(caja_actual['monto_apertura']) + safe_float(caja_actual['venta_efectivo'])
        caja_actual['efectivo_esperado'] = efectivo_esperado
        
        return render_template('caja/cierre.html', caja=caja_actual)
        
    except Exception as e:
        flash(f'❌ Error al cerrar caja: {str(e)}', 'danger')
        import traceback
        print(f"🔍 Error completo: {traceback.format_exc()}")
        return redirect(url_for('dashboard'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/caja/estado')
def estado_caja():
    """API para verificar estado de caja (para AJAX)"""
    conn = get_db_connection()
    
    if not conn:
        return jsonify({'caja_abierta': False, 'message': 'Sin conexión a BD'})
    
    try:
        cursor = conn.cursor(dictionary=True)
        id_empleado = session.get('id_empleado', 1)
        
        cursor.execute("""
            SELECT c.*, CONCAT(e.nombre, ' ', e.apellido) as cajero
            FROM caja_diaria c
            JOIN empleados e ON c.id_empleado_cajero = e.id_empleado
            WHERE fecha = CURDATE() 
            AND estado = 'abierta'
            AND c.id_empleado_cajero = %s
        """, (id_empleado,))
        
        caja = cursor.fetchone()
        
        return jsonify({
            'caja_abierta': caja is not None,
            'caja': caja
        })
        
    except Exception as e:
        return jsonify({'caja_abierta': False, 'message': str(e)})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/caja/historial')
def historial_caja():
    """Ver historial de cajas"""
    conn = get_db_connection()
    
    if not conn:
        flash('❌ Error de conexión a la base de datos.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener últimas 30 cajas
        cursor.execute("""
            SELECT c.*, CONCAT(e.nombre, ' ', e.apellido) as cajero
            FROM caja_diaria c
            JOIN empleados e ON c.id_empleado_cajero = e.id_empleado
            ORDER BY c.fecha DESC, c.hora_apertura DESC
            LIMIT 30
        """)
        
        cajas = cursor.fetchall()
        
        return render_template('caja/historial.html', cajas=cajas)
        
    except Exception as e:
        flash(f'❌ Error obteniendo historial: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
@app.template_filter('igv_subtotal')
def igv_subtotal_filter(total):
    """Calcular subtotal sin IGV (18%)"""
    try:
        return float(total) / 1.18
    except (ValueError, TypeError):
        return 0.0

@app.template_filter('igv_amount')
def igv_amount_filter(total):
    """Calcular monto de IGV (18%)"""
    try:
        return float(total) - (float(total) / 1.18)
    except (ValueError, TypeError):
        return 0.0

@app.route('/debug/routes')
def debug_routes():
    """Mostrar todas las rutas registradas"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': str(rule)
        })
    routes.sort(key=lambda x: x['endpoint'])
    
    # Verificar específicamente las rutas de caja
    caja_routes = [r for r in routes if 'caja' in r['endpoint'].lower()]
    
    return jsonify({
        'total_routes': len(routes),
        'caja_routes': caja_routes,
        'tiene_apertura_caja': any(r['endpoint'] == 'apertura_caja' for r in routes)
    })
@app.route('/ventas/crear')
def crear_venta():
    """Crear nueva venta directa (sin reserva)"""
    conn = get_db_connection()
    
    if not conn:
        flash('No hay conexión a la base de datos.', 'danger')
        return redirect(url_for('ventas'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener clientes para el select
        cursor.execute("SELECT id_cliente, nombre, apellido FROM clientes ORDER BY apellido, nombre")
        clientes = cursor.fetchall()
        
        # Obtener servicios activos
        cursor.execute("SELECT * FROM servicios WHERE activo = 1 ORDER BY nombre")
        servicios = cursor.fetchall()
        
        # Obtener productos con stock
        cursor.execute("SELECT * FROM productos WHERE stock_actual > 0 AND activo = 1 ORDER BY nombre")
        productos = cursor.fetchall()
        
        # Agrupar servicios por categoría
        servicios_por_categoria = {}
        for servicio in servicios:
            categoria = servicio['categoria']
            if categoria not in servicios_por_categoria:
                servicios_por_categoria[categoria] = []
            servicios_por_categoria[categoria].append(servicio)
        
        return render_template('ventas/crear.html', 
                             clientes=clientes, 
                             servicios_por_categoria=servicios_por_categoria,
                             productos=productos)
        
    except Error as e:
        flash(f'Error obteniendo datos: {e}', 'danger')
        return redirect(url_for('ventas'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()     


@app.route('/facturas/<int:id>/pagar', methods=['POST'])
def pagar_factura(id):
    """Registrar pago de factura - VERSIÓN CORREGIDA"""
    print(f"🔍 DEBUG: Pago para factura {id}")
    
    conn = get_db_connection()
    
    if not conn:
        return jsonify({'success': False, 'message': 'No hay conexión a la base de datos.'}), 500
    
    try:
        # Verificar que recibimos JSON
        if not request.is_json:
            return jsonify({'success': False, 'message': 'Solo se aceptan solicitudes JSON.'}), 400
        
        data = request.get_json()
        print(f"📦 Datos recibidos: {data}")
        
        if not data:
            return jsonify({'success': False, 'message': 'No se recibieron datos.'}), 400
        
        monto_pagado = data.get('monto', 0)
        metodo_pago = data.get('metodo_pago', 'efectivo')
        es_parcial = data.get('es_parcial', False)
        
        # Convertir y validar monto
        try:
            monto_pagado = float(monto_pagado)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Monto inválido.'}), 400
        
        if monto_pagado <= 0:
            return jsonify({'success': False, 'message': 'El monto debe ser mayor a 0.'}), 400
        
        cursor = conn.cursor(dictionary=True)
        
        # 1. Obtener factura
        cursor.execute("""
            SELECT f.*, c.nombre, c.apellido, c.dni
            FROM facturas f
            LEFT JOIN clientes c ON f.id_cliente = c.id_cliente
            WHERE f.id_factura = %s
        """, (id,))
        
        factura = cursor.fetchone()
        print(f"📄 Factura obtenida: {factura}")
        
        if not factura:
            return jsonify({'success': False, 'message': 'Factura no encontrada.'}), 404
        
        if factura['estado'] == 'pagada':
            return jsonify({'success': False, 'message': 'La factura ya está pagada.'}), 400
        
        if factura['estado'] == 'anulada':
            return jsonify({'success': False, 'message': 'No se puede pagar una factura anulada.'}), 400
        
        # 2. Verificar monto
        total_factura = safe_float(factura['total'])
        if monto_pagado > total_factura:
            return jsonify({'success': False, 'message': f'El monto excede el total. Total: S/ {total_factura:.2f}'}), 400
        
        # 3. Determinar nuevo estado
        if es_parcial and monto_pagado < total_factura:
            nuevo_estado = 'credito'
            saldo_pendiente = total_factura - monto_pagado
            mensaje_estado = f'Pago parcial de S/ {monto_pagado:.2f} registrado. Pendiente: S/ {saldo_pendiente:.2f}'
            
            # Verificar si existe columna saldo_pendiente
            cursor.execute("SHOW COLUMNS FROM facturas LIKE 'saldo_pendiente'")
            tiene_saldo_pendiente = cursor.fetchone()
            
            if tiene_saldo_pendiente:
                cursor.execute("""
                    UPDATE facturas 
                    SET estado = 'credito', 
                        metodo_pago = %s, 
                        fecha_pago = NOW(),
                        saldo_pendiente = %s
                    WHERE id_factura = %s
                """, (metodo_pago, saldo_pendiente, id))
            else:
                cursor.execute("""
                    UPDATE facturas 
                    SET estado = 'credito', 
                        metodo_pago = %s, 
                        fecha_pago = NOW()
                    WHERE id_factura = %s
                """, (metodo_pago, id))
        else:
            # Pago completo
            nuevo_estado = 'pagada'
            monto_pagado = total_factura
            mensaje_estado = f'Pago completo de S/ {monto_pagado:.2f} registrado.'
            
            cursor.execute("""
                UPDATE facturas 
                SET estado = 'pagada', 
                    metodo_pago = %s, 
                    fecha_pago = NOW()
                WHERE id_factura = %s
            """, (metodo_pago, id))
        
        print(f"🔄 Actualizando factura {id} a estado: {nuevo_estado}")
        
        # 4. Registrar movimiento en caja
        id_empleado = session.get('id_empleado', 1)
        cursor.execute("""
            SELECT id_caja 
            FROM caja_diaria 
            WHERE fecha = CURDATE() 
            AND estado = 'abierta'
            AND id_empleado_cajero = %s
            LIMIT 1
        """, (id_empleado,))
        
        caja_abierta = cursor.fetchone()
        
        if caja_abierta:
            id_caja = caja_abierta['id_caja']
            print(f"📦 Caja abierta encontrada: ID {id_caja}")
            
            # Registrar movimiento en caja
            try:
                cursor.execute("""
                    INSERT INTO movimientos_caja 
                    (id_caja, id_factura, tipo, metodo_pago, concepto, monto, fecha_movimiento, id_empleado)
                    VALUES (%s, %s, 'ingreso', %s, %s, %s, NOW(), %s)
                """, (id_caja, id, metodo_pago, 
                      f'Pago de {factura["tipo_comprobante"]} {factura["numero"]}', 
                      monto_pagado, id_empleado))
                
                print("✅ Movimiento en caja registrado")
                
                # Actualizar totales en caja
                campo_venta = ''
                if metodo_pago == 'efectivo':
                    campo_venta = 'venta_efectivo'
                elif metodo_pago == 'tarjeta':
                    campo_venta = 'venta_tarjeta'
                else:
                    campo_venta = 'venta_digital'
                
                cursor.execute(f"""
                    UPDATE caja_diaria 
                    SET {campo_venta} = COALESCE({campo_venta}, 0) + %s,
                        total_ventas = COALESCE(total_ventas, 0) + %s
                    WHERE id_caja = %s
                """, (monto_pagado, monto_pagado, id_caja))
                
            except Exception as e:
                print(f"⚠️  Error registrando en caja: {e}")
        else:
            print("⚠️  No hay caja abierta")
            mensaje_estado += " (Sin registro en caja)"
        
        conn.commit()
        
        print(f"✅ Pago registrado para factura {id}")
        
        return jsonify({
            'success': True, 
            'message': mensaje_estado,
            'nuevo_estado': nuevo_estado,
            'monto_pagado': monto_pagado,
            'caja_registrada': caja_abierta is not None
        })
            
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error en pagar_factura: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Error registrando pago: {str(e)}'}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/facturas/<int:id>/anular', methods=['POST'])
def anular_factura(id):
    """Anular factura"""
    print(f"🔍 DEBUG: Anulando factura {id}")
    
    conn = get_db_connection()
    
    if not conn:
        return jsonify({'success': False, 'message': 'No hay conexión a la base de datos.'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Verificar que la factura existe
        cursor.execute("SELECT estado, numero FROM facturas WHERE id_factura = %s", (id,))
        factura = cursor.fetchone()
        
        if not factura:
            return jsonify({'success': False, 'message': 'Factura no encontrada.'}), 404
        
        if factura['estado'] == 'anulada':
            return jsonify({'success': False, 'message': 'La factura ya está anulada.'})
        
        # No permitir anular facturas ya pagadas sin confirmación especial
        if factura['estado'] == 'pagada':
            return jsonify({
                'success': False, 
                'message': 'No se puede anular una factura pagada automáticamente. Contacte al administrador.'
            })
        
        # Anular factura
        cursor.execute("UPDATE facturas SET estado = 'anulada' WHERE id_factura = %s", (id,))
        conn.commit()
        
        print(f"✅ Factura {factura['numero']} anulada exitosamente")
        
        return jsonify({'success': True, 'message': 'Factura anulada exitosamente.'})
            
    except Error as e:
        if conn:
            conn.rollback()
        print(f"❌ Error anulando factura: {e}")
        return jsonify({'success': False, 'message': f'Error anulando factura: {str(e)}'}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if conn:
            conn.close()        


# Añadir estas rutas a tu app.py

@app.route('/empleados')
@login_required
def empleados():
    """Página principal de gestión de empleados"""
    return render_template('empleados/listar.html')

# ==================== API PARA EMPLEADOS ====================

@app.route('/api/empleados', methods=['GET'])
def api_get_empleados():
    """Obtener todos los empleados"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id_empleado, dni, nombre, apellido, telefono, email, 
                   especialidad, fecha_contratacion, activo
            FROM empleados
            ORDER BY nombre, apellido
        """)
        empleados = cursor.fetchall()
        return jsonify(empleados)
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empleados', methods=['POST'])
def api_create_empleado():
    """Crear nuevo empleado"""
    data = request.get_json()
    
    # Validar datos requeridos
    required_fields = ['dni', 'nombre', 'apellido', 'email', 'especialidad']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'El campo {field} es requerido'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el DNI ya existe
        cursor.execute("SELECT id_empleado FROM empleados WHERE dni = %s", (data['dni'],))
        if cursor.fetchone():
            return jsonify({'error': 'El DNI ya está registrado'}), 400
        
        # Verificar si el email ya existe
        cursor.execute("SELECT id_empleado FROM empleados WHERE email = %s", (data['email'],))
        if cursor.fetchone():
            return jsonify({'error': 'El email ya está registrado'}), 400
        
        # Insertar empleado
        cursor.execute("""
            INSERT INTO empleados (dni, nombre, apellido, telefono, email, 
                                  especialidad, fecha_contratacion, activo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['dni'],
            data['nombre'],
            data['apellido'],
            data.get('telefono'),
            data['email'],
            data['especialidad'],
            data.get('fecha_contratacion'),
            data.get('activo', True)
        ))
        
        id_empleado = cursor.lastrowid
        
        # Crear usuario si se solicitó
        if 'usuario' in data and data['usuario']:
            usuario_data = data['usuario']
            
            # Validar datos del usuario
            if not usuario_data.get('username') or not usuario_data.get('password') or not usuario_data.get('rol'):
                return jsonify({'error': 'Faltan datos para crear el usuario'}), 400
            
            # Crear hash de la contraseña
            password_hash = hashlib.sha256(usuario_data['password'].encode()).hexdigest()
            
            cursor.execute("""
                INSERT INTO usuarios (id_empleado, username, password_hash, rol)
                VALUES (%s, %s, %s, %s)
            """, (
                id_empleado,
                usuario_data['username'],
                password_hash,
                usuario_data['rol']
            ))
        
        conn.commit()
        
        # Obtener el empleado creado
        cursor.execute("""
            SELECT id_empleado, dni, nombre, apellido, telefono, email, 
                   especialidad, fecha_contratacion, activo
            FROM empleados
            WHERE id_empleado = %s
        """, (id_empleado,))
        empleado = cursor.fetchone()
        
        return jsonify({'success': True, 'empleado': empleado})
        
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empleados/<int:id>', methods=['GET'])
def api_get_empleado(id):
    """Obtener un empleado específico"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id_empleado, dni, nombre, apellido, telefono, email, 
                   especialidad, fecha_contratacion, activo
            FROM empleados
            WHERE id_empleado = %s
        """, (id,))
        empleado = cursor.fetchone()
        
        if not empleado:
            return jsonify({'error': 'Empleado no encontrado'}), 404
        
        return jsonify(empleado)
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empleados/<int:id>', methods=['PUT'])
def api_update_empleado(id):
    """Actualizar empleado"""
    data = request.get_json()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el empleado existe
        cursor.execute("SELECT id_empleado FROM empleados WHERE id_empleado = %s", (id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Empleado no encontrado'}), 404
        
        # Verificar duplicados de DNI (excluyendo el actual)
        if 'dni' in data:
            cursor.execute("SELECT id_empleado FROM empleados WHERE dni = %s AND id_empleado != %s", 
                          (data['dni'], id))
            if cursor.fetchone():
                return jsonify({'error': 'El DNI ya está registrado por otro empleado'}), 400
        
        # Verificar duplicados de email (excluyendo el actual)
        if 'email' in data:
            cursor.execute("SELECT id_empleado FROM empleados WHERE email = %s AND id_empleado != %s", 
                          (data['email'], id))
            if cursor.fetchone():
                return jsonify({'error': 'El email ya está registrado por otro empleado'}), 400
        
        # Construir query de actualización dinámica
        update_fields = []
        params = []
        
        field_mapping = {
            'dni': 'dni',
            'nombre': 'nombre',
            'apellido': 'apellido',
            'telefono': 'telefono',
            'email': 'email',
            'especialidad': 'especialidad',
            'fecha_contratacion': 'fecha_contratacion',
            'activo': 'activo'
        }
        
        for key, db_field in field_mapping.items():
            if key in data:
                update_fields.append(f"{db_field} = %s")
                params.append(data[key])
        
        if not update_fields:
            return jsonify({'error': 'No hay datos para actualizar'}), 400
        
        params.append(id)  # Para el WHERE
        
        query = f"""
            UPDATE empleados 
            SET {', '.join(update_fields)}
            WHERE id_empleado = %s
        """
        
        cursor.execute(query, params)
        conn.commit()
        
        return jsonify({'success': True})
        
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empleados/<int:id>', methods=['DELETE'])
def api_delete_empleado(id):
    """Desactivar empleado (no eliminar permanentemente)"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el empleado existe
        cursor.execute("SELECT id_empleado FROM empleados WHERE id_empleado = %s", (id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Empleado no encontrado'}), 404
        
        # Desactivar empleado (no eliminar)
        cursor.execute("UPDATE empleados SET activo = FALSE WHERE id_empleado = %s", (id,))
        
        # También desactivar el usuario si existe
        cursor.execute("UPDATE usuarios SET activo = FALSE WHERE id_empleado = %s", (id,))
        
        conn.commit()
        return jsonify({'success': True})
        
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empleados/<int:id>/usuario', methods=['GET'])
def api_get_usuario_empleado(id):
    """Obtener información del usuario de un empleado"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el empleado existe
        cursor.execute("SELECT id_empleado FROM empleados WHERE id_empleado = %s", (id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Empleado no encontrado'}), 404
        
        # Obtener usuario
        cursor.execute("""
            SELECT id_usuario, username, rol, fecha_creacion, ultimo_login, activo
            FROM usuarios
            WHERE id_empleado = %s
        """, (id,))
        usuario = cursor.fetchone()
        
        if usuario:
            # Formatear fechas
            if usuario['fecha_creacion']:
                usuario['fecha_creacion'] = usuario['fecha_creacion'].strftime('%d/%m/%Y %H:%M')
            if usuario['ultimo_login']:
                usuario['ultimo_login'] = usuario['ultimo_login'].strftime('%d/%m/%Y %H:%M')
            
            return jsonify({'existe': True, 'usuario': usuario})
        else:
            return jsonify({'existe': False})
        
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empleados/<int:id>/usuario', methods=['POST'])
def api_create_usuario_empleado(id):
    """Crear usuario para un empleado"""
    data = request.get_json()
    
    # Validar datos
    required_fields = ['username', 'password', 'rol']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'El campo {field} es requerido'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el empleado existe
        cursor.execute("SELECT id_empleado FROM empleados WHERE id_empleado = %s", (id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Empleado no encontrado'}), 404
        
        # Verificar si ya tiene usuario
        cursor.execute("SELECT id_usuario FROM usuarios WHERE id_empleado = %s", (id,))
        if cursor.fetchone():
            return jsonify({'error': 'El empleado ya tiene un usuario'}), 400
        
        # Verificar si el username ya existe
        cursor.execute("SELECT id_usuario FROM usuarios WHERE username = %s", (data['username'],))
        if cursor.fetchone():
            return jsonify({'error': 'El username ya está en uso'}), 400
        
        # Crear hash de la contraseña
        password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
        
        # Crear usuario
        cursor.execute("""
            INSERT INTO usuarios (id_empleado, username, password_hash, rol)
            VALUES (%s, %s, %s, %s)
        """, (id, data['username'], password_hash, data['rol']))
        
        conn.commit()
        return jsonify({'success': True})
        
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/usuarios/<int:id>', methods=['PUT'])
def api_update_usuario(id):
    """Actualizar usuario"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No hay datos para actualizar'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el usuario existe
        cursor.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = %s", (id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Construir query de actualización dinámica
        update_fields = []
        params = []
        
        if 'rol' in data:
            update_fields.append("rol = %s")
            params.append(data['rol'])
        
        if 'password' in data and data['password']:
            password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
            update_fields.append("password_hash = %s")
            params.append(password_hash)
        
        if 'activo' in data:
            update_fields.append("activo = %s")
            params.append(data['activo'])
        
        if not update_fields:
            return jsonify({'error': 'No hay datos válidos para actualizar'}), 400
        
        params.append(id)  # Para el WHERE
        
        query = f"""
            UPDATE usuarios 
            SET {', '.join(update_fields)}
            WHERE id_usuario = %s
        """
        
        cursor.execute(query, params)
        conn.commit()
        
        return jsonify({'success': True})
        
    except Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==================== FUNCIONES DE REPORTES ====================

@app.route('/api/empleados/estadisticas')
def api_get_estadisticas_empleados():
    """Obtener estadísticas de empleados"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Estadísticas básicas
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN activo = TRUE THEN 1 ELSE 0 END) as activos,
                SUM(CASE WHEN activo = FALSE THEN 1 ELSE 0 END) as inactivos,
                COUNT(DISTINCT especialidad) as especialidades_diferentes
            FROM empleados
        """)
        estadisticas = cursor.fetchone()
        
        # Conteo por especialidad
        cursor.execute("""
            SELECT especialidad, COUNT(*) as cantidad
            FROM empleados
            WHERE activo = TRUE
            GROUP BY especialidad
            ORDER BY cantidad DESC
        """)
        por_especialidad = cursor.fetchall()
        
        # Últimos empleados contratados
        cursor.execute("""
            SELECT nombre, apellido, fecha_contratacion, especialidad
            FROM empleados
            WHERE fecha_contratacion IS NOT NULL
            ORDER BY fecha_contratacion DESC
            LIMIT 5
        """)
        ultimos_contratados = cursor.fetchall()
        
        # Formatear fechas
        for empleado in ultimos_contratados:
            if empleado['fecha_contratacion']:
                empleado['fecha_contratacion'] = empleado['fecha_contratacion'].strftime('%d/%m/%Y')
        
        return jsonify({
            'estadisticas': estadisticas,
            'por_especialidad': por_especialidad,
            'ultimos_contratados': ultimos_contratados
        })
        
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/empleados/exportar')
def exportar_empleados():
    """Exportar empleados a Excel"""
    conn = get_db_connection()
    if not conn:
        flash('No hay conexión a la base de datos.', 'danger')
        return redirect(url_for('empleados'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT dni, nombre, apellido, telefono, email, especialidad,
                   fecha_contratacion, 
                   CASE WHEN activo = TRUE THEN 'Activo' ELSE 'Inactivo' END as estado
            FROM empleados
            ORDER BY nombre, apellido
        """)
        empleados = cursor.fetchall()
        
        # Crear DataFrame
        import pandas as pd
        df = pd.DataFrame(empleados)
        
        # Crear respuesta Excel
        from io import BytesIO
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Empleados', index=False)
            
            # Ajustar ancho de columnas
            worksheet = writer.sheets['Empleados']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        # Enviar archivo
        from flask import send_file
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'empleados_petglow_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        )
        
    except Error as e:
        flash(f'Error exportando empleados: {str(e)}', 'danger')
        return redirect(url_for('empleados'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('empleados'))
    finally:
        cursor.close()
        conn.close()
@app.route('/api/empleado/<int:id>/disponibilidad')
def verificar_disponibilidad_empleado(id):
    """Verificar disponibilidad de un empleado en fecha y hora específicas"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'disponible': False, 'mensaje': 'Error de conexión'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        fecha = request.args.get('fecha')
        hora = request.args.get('hora')
        
        if not fecha or not hora:
            return jsonify({'disponible': False, 'mensaje': 'Fecha y hora requeridas'}), 400
        
        # Obtener información del empleado
        cursor.execute("SELECT nombre, apellido FROM empleados WHERE id_empleado = %s", (id,))
        empleado = cursor.fetchone()
        
        if not empleado:
            return jsonify({'disponible': False, 'mensaje': 'Empleado no encontrado'}), 404
        
        # Verificar si es administrador
        nombre_completo = f"{empleado['nombre']} {empleado['apellido']}".lower()
        es_administrador = any(keyword in nombre_completo for keyword in ['admin', 'sistema', 'administrador'])
        
        # Si es administrador, siempre está disponible
        if es_administrador:
            return jsonify({
                'disponible': True,
                'mensaje': 'Administrador - puede múltiples reservas'
            })
        
        # Si no es administrador, verificar disponibilidad normal
        fecha_hora_str = f"{fecha} {hora}"
        try:
            fecha_hora_dt = datetime.strptime(fecha_hora_str, '%Y-%m-%d %H:%M')
        except ValueError:
            return jsonify({'disponible': False, 'mensaje': 'Formato de fecha/hora inválido'}), 400
        
        # Verificar reservas existentes
        cursor.execute("""
            SELECT r.id_reserva, r.fecha_reserva, s.duracion_min
            FROM reservas r
            JOIN reserva_servicios rs ON r.id_reserva = rs.id_reserva
            JOIN servicios s ON rs.id_servicio = s.id_servicio
            WHERE r.id_empleado = %s 
            AND r.estado NOT IN ('cancelada', 'no_show')
            AND DATE(r.fecha_reserva) = DATE(%s)
        """, (id, fecha))
        
        reservas_existentes = cursor.fetchall()
        
        # Para simplificar, asumimos duración de 60 minutos
        duracion_estimada = 60
        nueva_inicio = fecha_hora_dt
        nueva_fin = fecha_hora_dt + timedelta(minutes=duracion_estimada)
        
        for reserva in reservas_existentes:
            reserva_inicio = reserva['fecha_reserva']
            reserva_duracion = int(reserva['duracion_min']) if reserva['duracion_min'] else 60
            reserva_fin = reserva_inicio + timedelta(minutes=int(reserva_duracion))
            
            if (nueva_inicio < reserva_fin and nueva_fin > reserva_inicio):
                return jsonify({
                    'disponible': False,
                    'mensaje': f'Ya tiene reserva de {reserva_inicio.strftime("%H:%M")} a {reserva_fin.strftime("%H:%M")}'
                })
        
        return jsonify({'disponible': True, 'mensaje': 'Empleado disponible'})
        
    except Error as e:
        return jsonify({'disponible': False, 'mensaje': f'Error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()
# ==================== RUTAS PARA USUARIOS ====================

@app.route('/usuarios')
@login_required  # Agregar este decorador
@admin_required  # Solo administradores pueden ver usuarios
def usuarios():
    """Listar usuarios del sistema"""
    if 'id_usuario' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        flash('No hay conexión a la base de datos.', 'danger')
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener todos los usuarios
        cursor.execute("""
            SELECT u.*, e.nombre as empleado_nombre, e.apellido as empleado_apellido, 
                   e.email, e.dni as empleado_dni
            FROM usuarios u
            LEFT JOIN empleados e ON u.id_empleado = e.id_empleado
            ORDER BY u.id_usuario DESC
        """)
        usuarios = cursor.fetchall()
        
        # Estadísticas
        cursor.execute("SELECT COUNT(*) as total FROM usuarios")
        total_usuarios = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as activos FROM usuarios WHERE activo = TRUE")
        usuarios_activos = cursor.fetchone()['activos']
        
        cursor.execute("SELECT COUNT(*) as admins FROM usuarios WHERE rol = 'admin'")
        administradores = cursor.fetchone()['admins']
        
        # Obtener empleados sin usuario
        cursor.execute("""
            SELECT e.* FROM empleados e
            LEFT JOIN usuarios u ON e.id_empleado = u.id_empleado
            WHERE u.id_usuario IS NULL AND e.activo = TRUE
            ORDER BY e.nombre
        """)
        empleados_sin_usuario = cursor.fetchall()
        
        # Último registro
        ultimo_registro = None
        if usuarios:
            ultimo_registro = usuarios[0].get('fecha_creacion')
        
    except Error as e:
        flash(f'Error cargando usuarios: {e}', 'danger')
        return redirect(url_for('index'))
    finally:
        cursor.close()
        conn.close()
    
    return render_template('usuarios/listar.html',
                         usuarios=usuarios,
                         total_usuarios=total_usuarios,
                         usuarios_activos=usuarios_activos,
                         administradores=administradores,
                         ultimo_registro=ultimo_registro,
                         empleados_sin_usuario=empleados_sin_usuario)

# ==================== API PARA USUARIOS ====================

@app.route('/api/usuarios', methods=['POST'])
def api_crear_usuario():
    """Crear un nuevo usuario (API)"""
    if 'id_usuario' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    data = request.json
    required_fields = ['username', 'password', 'rol']
    
    # Validar campos requeridos
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'success': False, 'error': f'El campo {field} es requerido'}), 400
    
    # Validar longitud de contraseña
    if len(data['password']) < 6:
        return jsonify({'success': False, 'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Error de conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el usuario ya existe
        cursor.execute("SELECT id_usuario FROM usuarios WHERE username = %s", (data['username'],))
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'El nombre de usuario ya existe'}), 400
        
        # Crear usuario
        cursor.execute("""
            INSERT INTO usuarios (username, password, id_empleado, rol, activo)
            VALUES (%s, %s, %s, %s, %s)
        """, (data['username'], data['password'], 
              data.get('id_empleado'), data['rol'], 
              data.get('activo', True)))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Usuario creado exitosamente'})
        
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/usuarios/<int:id>', methods=['GET'])
def api_obtener_usuario(id):
    """Obtener información de un usuario (API)"""
    if 'id_usuario' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Error de conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener usuario
        cursor.execute("""
            SELECT u.*, e.nombre, e.apellido, e.dni, e.email
            FROM usuarios u
            LEFT JOIN empleados e ON u.id_empleado = e.id_empleado
            WHERE u.id_usuario = %s
        """, (id,))
        
        usuario = cursor.fetchone()
        
        if not usuario:
            return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
        
        # Obtener historial de login (últimos 5)
        cursor.execute("""
            SELECT fecha_login, ip_address, user_agent
            FROM login_history
            WHERE id_usuario = %s
            ORDER BY fecha_login DESC
            LIMIT 5
        """, (id,))
        
        historial = cursor.fetchall()
        usuario['historial_login'] = historial
        
        return jsonify({'success': True, 'usuario': usuario})
        
    except Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/usuarios/<int:id>', methods=['PUT'])
def api_actualizar_usuario(id):
    """Actualizar un usuario (API)"""
    if 'id_usuario' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    data = request.json
    
    # Validar campos requeridos
    if 'username' not in data or not data['username']:
        return jsonify({'success': False, 'error': 'El nombre de usuario es requerido'}), 400
    
    if 'rol' not in data or not data['rol']:
        return jsonify({'success': False, 'error': 'El rol es requerido'}), 400
    
    # Validar contraseña si se proporciona
    if 'password' in data and data['password']:
        if len(data['password']) < 6:
            return jsonify({'success': False, 'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Error de conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el usuario existe
        cursor.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = %s", (id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
        
        # Verificar si el username ya existe (excluyendo el actual)
        cursor.execute("SELECT id_usuario FROM usuarios WHERE username = %s AND id_usuario != %s", 
                      (data['username'], id))
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'El nombre de usuario ya existe'}), 400
        
        # Actualizar usuario
        if 'password' in data and data['password']:
            cursor.execute("""
                UPDATE usuarios 
                SET username = %s, password = %s, rol = %s, activo = %s
                WHERE id_usuario = %s
            """, (data['username'], data['password'], data['rol'], 
                  data.get('activo', True), id))
        else:
            cursor.execute("""
                UPDATE usuarios 
                SET username = %s, rol = %s, activo = %s
                WHERE id_usuario = %s
            """, (data['username'], data['rol'], 
                  data.get('activo', True), id))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Usuario actualizado exitosamente'})
        
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/usuarios/<int:id>', methods=['DELETE'])
def api_eliminar_usuario(id):
    """Eliminar un usuario (API)"""
    if 'id_usuario' not in session:
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    # Prevenir que un usuario se elimine a sí mismo
    if id == session.get('id_usuario'):
        return jsonify({'success': False, 'error': 'No puedes eliminar tu propio usuario'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Error de conexión a la base de datos'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el usuario existe
        cursor.execute("SELECT id_usuario, rol FROM usuarios WHERE id_usuario = %s", (id,))
        usuario = cursor.fetchone()
        
        if not usuario:
            return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
        
        # Prevenir eliminación del último administrador
        if usuario['rol'] == 'admin':
            cursor.execute("SELECT COUNT(*) as total_admins FROM usuarios WHERE rol = 'admin'")
            total_admins = cursor.fetchone()['total_admins']
            
            if total_admins <= 1:
                return jsonify({'success': False, 'error': 'No se puede eliminar el único administrador'}), 400
        
        # Eliminar usuario
        cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id,))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Usuario eliminado exitosamente'})
        
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
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


