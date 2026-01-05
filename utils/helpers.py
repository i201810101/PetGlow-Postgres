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