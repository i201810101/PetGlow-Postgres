import tkinter as tk
from datetime import datetime, date
import re

def center_window(window):
    """Centrar ventana en la pantalla"""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

def validate_email(email):
    """Validar formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validar formato de teléfono"""
    pattern = r'^[0-9\s\-\+\(\)]{7,15}$'
    return re.match(pattern, phone) is not None

def validate_dni(dni):
    """Validar formato de DNI"""
    pattern = r'^[0-9]{8}$'
    return re.match(pattern, dni) is not None

def format_currency(amount):
    """Formatear número como moneda"""
    return f"S/. {float(amount):,.2f}"

def format_date(date_obj):
    """Formatear fecha"""
    if isinstance(date_obj, date) or isinstance(date_obj, datetime):
        return date_obj.strftime("%d/%m/%Y")
    return date_obj

def format_datetime(datetime_obj):
    """Formatear fecha y hora"""
    if isinstance(datetime_obj, datetime):
        return datetime_obj.strftime("%d/%m/%Y %H:%M")
    return datetime_obj

def show_error(message, parent=None):
    """Mostrar mensaje de error"""
    tk.messagebox.showerror("Error", message, parent=parent)

def show_success(message, parent=None):
    """Mostrar mensaje de éxito"""
    tk.messagebox.showinfo("Éxito", message, parent=parent)

def show_warning(message, parent=None):
    """Mostrar mensaje de advertencia"""
    tk.messagebox.showwarning("Advertencia", message, parent=parent)

def confirm_action(message, parent=None):
    """Pedir confirmación al usuario"""
    return tk.messagebox.askyesno("Confirmar", message, parent=parent)

def validar_dni_peruano(dni):
    """Validar DNI peruano (8 dígitos) o Carnet de Extranjería (9 dígitos)"""
    if not dni:
        return True, ""  # Opcional, no hay error
    dni_str = str(dni).strip()
    
    if not re.match(r'^\d{8,9}$', dni_str):
        return False, "DNI debe tener 8 dígitos o Carnet de Extranjería 9 dígitos"
    
    if len(dni_str) == 8:
        # Validación básica para DNI peruano
        return True, ""
    elif len(dni_str) == 9:
        # Carnet de Extranjería
        return True, ""
    
    return False, "Formato no válido"

def validar_telefono_peruano(telefono):
    """Validar teléfono peruano (9 dígitos, empieza con 9)"""
    if not telefono:
        return False, "El teléfono es obligatorio"
    
    telefono_str = str(telefono).strip()
    
    # Remover espacios, guiones, etc.
    telefono_limpio = re.sub(r'\D', '', telefono_str)
    
    if not re.match(r'^9\d{8}$', telefono_limpio):
        return False, "Teléfono debe tener 9 dígitos y empezar con 9"
    
    return True, ""

def validar_nombre_apellido(texto):
    """Validar nombre o apellido (solo letras, espacios y longitud adecuada)"""
    if not texto:
        return False, "Este campo es obligatorio"
    
    texto_str = str(texto).strip()
    
    if len(texto_str) < 2 or len(texto_str) > 50:
        return False, "Debe tener entre 2 y 50 caracteres"
    
    if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúñÑ\s]+$', texto_str):
        return False, "Solo se permiten letras y espacios"
    
    return True, ""

def validar_email_cliente(email):
    """Validar email para cliente (opcional pero con formato correcto)"""
    if not email:
        return True, ""  # Opcional
    
    email_str = str(email).strip()
    
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_str):
        return False, "Por favor ingresa un email válido"
    
    return True, ""

def validar_cliente_completo(dni, nombre, apellido, telefono, email=""):
    """Validar todos los campos de un cliente"""
    errores = []
    
    # Validar DNI (opcional)
    if dni:
        dni_valido, mensaje_dni = validar_dni_peruano(dni)
        if not dni_valido:
            errores.append(mensaje_dni)
    
    # Validar nombre (obligatorio)
    nombre_valido, mensaje_nombre = validar_nombre_apellido(nombre)
    if not nombre_valido:
        errores.append(f"Nombre: {mensaje_nombre}")
    
    # Validar apellido (obligatorio)
    apellido_valido, mensaje_apellido = validar_nombre_apellido(apellido)
    if not apellido_valido:
        errores.append(f"Apellido: {mensaje_apellido}")
    
    # Validar teléfono (obligatorio)
    telefono_valido, mensaje_telefono = validar_telefono_peruano(telefono)
    if not telefono_valido:
        errores.append(f"Teléfono: {mensaje_telefono}")
    
    # Validar email (opcional)
    if email:
        email_valido, mensaje_email = validar_email_cliente(email)
        if not email_valido:
            errores.append(f"Email: {mensaje_email}")
    
    return len(errores) == 0, errores

# Agrega estas funciones a tu helpers.py existente

def validar_peso_mascota(peso):
    """Validar peso de mascota (0.1 - 200 kg)"""
    if peso is None or peso == '':
        return True, ""  # Opcional
    
    try:
        peso_float = float(peso)
        if peso_float <= 0 or peso_float > 200:
            return False, "El peso debe estar entre 0.1 y 200 kg"
        return True, ""
    except ValueError:
        return False, "El peso debe ser un número válido"

def validar_fecha_nacimiento(fecha_str):
    """Validar fecha de nacimiento"""
    if not fecha_str:
        return True, None  # Opcional
    
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        if fecha > datetime.now().date():
            return False, None, "La fecha de nacimiento no puede ser futura"
        return True, fecha, ""
    except ValueError:
        return False, None, "Formato de fecha inválido. Use YYYY-MM-DD"

def calcular_edad_mascota(fecha_nacimiento):
    """Calcular edad de la mascota en años y meses"""
    if not fecha_nacimiento:
        return None, None
    
    hoy = datetime.now().date()
    edad_dias = (hoy - fecha_nacimiento).days
    
    if edad_dias < 0:
        return None, None
    
    años = edad_dias // 365
    meses = (edad_dias % 365) // 30
    
    return años, meses

def validar_mascota_completa(id_cliente, nombre, especie, peso=None, fecha_nacimiento_str=None):
    """Validar todos los campos de una mascota"""
    errores = []
    
    # Validar dueño
    if not id_cliente:
        errores.append("Debe seleccionar un dueño")
    
    # Validar nombre
    if not nombre or len(nombre.strip()) < 2:
        errores.append("El nombre debe tener al menos 2 caracteres")
    
    # Validar especie
    if not especie or especie not in ['perro', 'gato', 'otro']:
        errores.append("Especie no válida")
    
    # Validar peso
    if peso:
        peso_valido, mensaje_peso = validar_peso_mascota(peso)
        if not peso_valido:
            errores.append(f"Peso: {mensaje_peso}")
    
    # Validar fecha
    if fecha_nacimiento_str:
        fecha_valida, fecha, mensaje_fecha = validar_fecha_nacimiento(fecha_nacimiento_str)
        if not fecha_valida:
            errores.append(f"Fecha: {mensaje_fecha}")
    
    return len(errores) == 0, errores

# Agrega estas funciones a tu helpers.py existente

def validar_codigo_servicio(codigo):
    """Validar código de servicio"""
    if not codigo or len(codigo.strip()) < 3:
        return False, "El código debe tener al menos 3 caracteres"
    
    # Puedes agregar más validaciones, como formato específico
    return True, ""

def validar_precio_servicio(costo, precio):
    """Validar relación costo-precio"""
    try:
        costo_float = float(costo) if costo else 0.0
        precio_float = float(precio) if precio else 0.0
        
        if precio_float <= 0:
            return False, "El precio debe ser mayor a 0"
        
        if precio_float <= costo_float:
            return False, "El precio debe ser mayor al costo"
        
        # Calcular margen mínimo recomendado
        if costo_float > 0:
            margen = ((precio_float - costo_float) / costo_float) * 100
            if margen < 50:
                return True, f"Margen bajo ({margen:.1f}%), considera aumentar el precio"
        
        return True, ""
        
    except ValueError:
        return False, "Costo y precio deben ser números válidos"

def calcular_margen_servicio(costo, precio):
    """Calcular margen de ganancia"""
    if not costo or not precio:
        return 0.0
    
    try:
        costo_float = float(costo)
        precio_float = float(precio)
        
        if costo_float == 0:
            return 0.0
        
        return ((precio_float - costo_float) / costo_float) * 100
    except:
        return 0.0

def validar_duracion_servicio(duracion):
    """Validar duración del servicio (en minutos)"""
    try:
        duracion_int = int(duracion)
        if duracion_int < 15 or duracion_int > 300:
            return False, "La duración debe estar entre 15 y 300 minutos"
        return True, ""
    except ValueError:
        return False, "La duración debe ser un número entero"

# Agrega estas funciones a tu helpers.py existente

def validar_fecha_reserva(fecha_str, hora_str):
    """Validar fecha y hora de reserva"""
    try:
        # Combinar fecha y hora
        fecha_hora_str = f"{fecha_str} {hora_str}"
        fecha_hora = datetime.strptime(fecha_hora_str, '%Y-%m-%d %H:%M')
        
        # Verificar que no sea fecha pasada
        if fecha_hora < datetime.now():
            return False, "No se pueden crear reservas en fechas pasadas"
        
        # Verificar horario de atención
        hora = fecha_hora.hour
        minutos = fecha_hora.minute
        
        # Lunes a Viernes: 9:00 - 18:00
        # Sábados: 9:00 - 14:00
        dia_semana = fecha_hora.weekday()  # 0 = lunes, 6 = domingo
        
        if dia_semana == 6:  # Domingo
            return False, "Domingo cerrado"
        
        if dia_semana == 5:  # Sábado
            if hora < 9 or hora > 14 or (hora == 14 and minutos > 0):
                return False, "Sábados: 9:00 AM - 2:00 PM"
        else:  # Lunes a Viernes
            if hora < 9 or hora > 18 or (hora == 18 and minutos > 0):
                return False, "Lunes a Viernes: 9:00 AM - 6:00 PM"
        
        return True, ""
        
    except ValueError:
        return False, "Formato de fecha u hora inválido"

def calcular_duracion_total_servicios(servicios_ids):
    """Calcular duración total de servicios"""
    if not servicios_ids:
        return 0
    
    conn = get_db_connection()
    if not conn:
        return 0
    
    try:
        cursor = conn.cursor()
        # Convertir lista de IDs a tupla
        ids_tuple = tuple(map(int, servicios_ids))
        cursor.execute(f"""
            SELECT SUM(duracion_min) 
            FROM servicios 
            WHERE id_servicio IN ({','.join(['%s']*len(ids_tuple))})
        """, ids_tuple)
        resultado = cursor.fetchone()
        return resultado[0] if resultado and resultado[0] else 0
    except:
        return 0
    finally:
        cursor.close()
        conn.close()

def verificar_disponibilidad_empleado(id_empleado, fecha_reserva, duracion_min):
    """Verificar si un empleado está disponible en una fecha/hora"""
    conn = get_db_connection()
    if not conn:
        return False, "Error de conexión"
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Convertir fecha_reserva a datetime si es string
        if isinstance(fecha_reserva, str):
            fecha_reserva = datetime.strptime(fecha_reserva, '%Y-%m-%d %H:%M')
        
        # Calcular hora de inicio y fin
        hora_inicio = fecha_reserva
        hora_fin = fecha_reserva + timedelta(minutes=duracion_min)
        
        # Verificar reservas existentes del empleado
        cursor.execute("""
            SELECT fecha_reserva, duracion_min
            FROM reservas r
            JOIN reserva_servicios rs ON r.id_reserva = rs.id_reserva
            JOIN servicios s ON rs.id_servicio = s.id_servicio
            WHERE r.id_empleado = %s 
            AND r.estado NOT IN ('cancelada', 'no_show')
            AND DATE(fecha_reserva) = DATE(%s)
        """, (id_empleado, fecha_reserva))
        
        reservas_existentes = cursor.fetchall()
        
        for reserva in reservas_existentes:
            reserva_inicio = reserva['fecha_reserva']
            reserva_fin = reserva_inicio + timedelta(minutes=reserva['duracion_min'])
            
            # Verificar superposición
            if (hora_inicio < reserva_fin and hora_fin > reserva_inicio):
                return False, f"Empleado ocupado de {reserva_inicio.strftime('%H:%M')} a {reserva_fin.strftime('%H:%M')}"
        
        return True, "Disponible"
        
    except Exception as e:
        return False, f"Error verificando disponibilidad: {str(e)}"
    finally:
        cursor.close()
        conn.close()