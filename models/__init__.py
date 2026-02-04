# models/__init__.py
# Importa todos tus modelos aquí

from .empleado import Empleado
from .cliente import Cliente
from .mascota import Mascota
from .servicio import Servicio
from .reserva import Reserva
from .detalle_reserva import DetalleReserva
# ... otros modelos que tengas ...

__all__ = ['Empleado', 'Cliente', 'Mascota', 'Servicio', 'Reserva', 'DetalleReserva']