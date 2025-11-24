# VariablesyColas.py
from multiprocessing import Queue, Value
from ctypes import c_bool, c_float

# Cola: sensor → actuador / web
cola_datos = Queue()

# Cola: web → actuador
cola_comandos = Queue()

# Variables compartidas
alerta_activa = Value(c_bool, False)

temp_actual = Value(c_float, 0.0)
hum_actual  = Value(c_float, 0.0)
