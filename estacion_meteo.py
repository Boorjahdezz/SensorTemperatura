from gpiozero import Button, LED
import time
import threading
from signal import pause
import random
import sqlite3               
import datetime              

# --- CONFIGURACIÓN DE HARDWARE ---
led_rojo = LED(17)   
led_verde = LED(27)  
boton = Button(16, pull_up=False, bounce_time=0.1)

# --- VARIABLES PARA HILOS ---
eventoparada = threading.Event()
lock_datos = threading.Lock()
datos_compartidos = {"temp": 0, "hum": 0, "estado": "normal"} #Estado predefinido a normal

# --- UMBRALES ---
LIMITE_TEMP = 26     
LIMITE_HUM = 60      

# --- CONFIGURACIÓN BASE DE DATOS ---
NOMBRE_BD = "estacion_meteo.db"

def iniciar_base_datos():
    """
    Crea la tabla si no existe. Esto prepara el archivo para Flask.
    """
    try:
        conn = sqlite3.connect(NOMBRE_BD)
        cursor = conn.cursor()
        # Creamos una tabla simple compatible con SQL estándar
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lecturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT,
                temperatura REAL,
                humedad REAL,
                estado TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print(f"--- Base de datos '{NOMBRE_BD}' verificada ---")
    except Exception as e:
        print(f"Error iniciando BD: {e}")

def guardar_dato(temp, hum, estado):
    """
    Inserta el registro en la base de datos SQL.
    """
    try:
        conn = sqlite3.connect(NOMBRE_BD)
        cursor = conn.cursor()
        
        # Obtenemos fecha y hora actual
        ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Sentencia SQL para insertar
        cursor.execute("INSERT INTO lecturas (fecha, temperatura, humedad, estado) VALUES (?, ?, ?, ?)", 
                       (ahora, temp, hum, estado))
        
        conn.commit()
        conn.close()
        print("[SQL] Dato guardado en base de datos.")
    except Exception as e:
        print(f"[ERROR SQL] No se pudo guardar: {e}")

def hilo_sensor_simulado():
    #Hilo 1: Simula lectura de sensores en segundo plano cada 5s
    while not eventoparada.is_set():
        with lock_datos: # Sección crítica
            datos_compartidos["temp"] = random.randint(15, 40)
            datos_compartidos["hum"] = random.randint(30, 90)
            
            # Lógica simple de estado
            if datos_compartidos["temp"] > 26 or datos_compartidos["hum"] > 60:
                datos_compartidos["estado"] = "ALERTA"
            else:
                datos_compartidos["estado"] = "NORMAL"
            
            print(f"[HILO SENSOR] Leído: {datos_compartidos}")
        
        time.sleep(5)

def gestionar_pulsacion():
    """
    Se ejecuta SOLO al pulsar el botón.
    """
    # 1. Generar valores aleatorios
    temp = random.randint(20, 35) 
    hum = random.randint(30, 90)
    
    # Variable para guardar un estado simplificado en la BD
    estado_corto = "NORMAL"

    # 2. Lógica de LEDs (Semáforo)
    if temp > LIMITE_TEMP or hum > LIMITE_HUM:
        led_rojo.on()
        led_verde.off()
        estado_msg = "ALERTA (Supera límites)"
        estado_corto = "ALERTA"
    else:
        led_verde.on()
        led_rojo.off()
        estado_msg = "NORMAL (Valores seguros)"
        estado_corto = "NORMAL"

    print(f"[CLICK] Temp: {temp}°C | Hum: {hum}%  -->  LED: {estado_msg}")
    
    # 3. Guardar en la base de datos
    guardar_dato(temp, hum, estado_corto)

# --- PROGRAMA PRINCIPAL ---
def main():
    # Iniciar la base de datos
    iniciar_base_datos()
    t1 = threading.Thread(target=hilo_sensor_simulado,name="HiloSensorSimulado")
    t2= threading.Thread(target=gestionar_pulsacion,name="HiloGestionarPulsacion")
    # Estado inicial
    led_rojo.off()
    led_verde.off() 
    
    print("--- ESTACION METEOROLÓGICA LISTA ---")
    print("Programa corriendo. Pulsa el botón para leer datos.")
    print("Pulsa Ctrl + C para salir limpiamente.")
    print(f"Límites -> Temp > {LIMITE_TEMP}°C o Hum > {LIMITE_HUM}% enciende ROJO.")

    # Asignar el evento
    boton.when_pressed = gestionar_pulsacion

    # --- BLOQUE DE SEGURIDAD PARA SALIR ---
    try:
        # El programa se queda aquí 'dormido' esperando el botón
        pause()
    except KeyboardInterrupt:
        # Esto atrapa el Ctrl + C para que no salga el error rojo
        print("\n\nSaliendo del programa...")
        led_rojo.off()
        led_verde.off()
        print("Luces apagadas. Estación cerrada")

if __name__ == "__main__":
    main()