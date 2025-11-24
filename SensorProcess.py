# SensorProcess.py

# ahora mismo simulado porque nos falta el sensor dht22
import time
import random
from VariablesyColas import cola_datos, temp_actual, hum_actual

def leer_sensor_simulado():
    """Valores aleatorios realistas."""
    temperatura = random.uniform(18.0, 27.0)
    humedad = random.uniform(30.0, 55.0)
    return temperatura, humedad

def sensor_loop():
    print("[Sensor] Proceso iniciado")

    while True:
        # Leer datos (simulado)
        temp, hum = leer_sensor_simulado()

        temp_actual.value = temp
        hum_actual.value = hum

        cola_datos.put(("datos", temp, hum))

        print(f"[Sensor] T={temp:.2f}°C  H={hum:.2f}%")

        time.sleep(2)  # Como el DHT22 real
