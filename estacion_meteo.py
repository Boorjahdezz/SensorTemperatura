from gpiozero import Button, LED
import time
import threading
from signal import pause
import random
import sqlite3               
import datetime              


# --- LÍMITES DE ALERTA ---
LIMITE_TEMP = 26  
LIMITE_HUM = 60   
# --- CONFIGURACIÓN DE HARDWARE ---
led_rojo = LED(17)   
led_verde = LED(27)  
boton = Button(16, pull_up=False, bounce_time=0.1)#bounce time para evitar rebotes

# --- VARIABLES PARA HILOS ---
eventoparada = threading.Event()
lock_datos = threading.Lock()
datos_compartidos = {"temp": 0, "hum": 0, "estado": "normal"} #Estado predefinido a normal

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
            datos_compartidos["temp"] = random.randint(23, 29)
            datos_compartidos["hum"] = random.randint(50,70)
            
            # Lógica simple de estado
            if datos_compartidos["temp"] > 26 or datos_compartidos["hum"] > 60:
                datos_compartidos["estado"] = "ALERTA"
            else:
                datos_compartidos["estado"] = "NORMAL"
            
            print(f"[HILO SENSOR] Leído: {datos_compartidos}")
        
        time.sleep(10)

def hilo_indicadores_led():
    """Hilo 2: Gestiona los LEDs independientemente de la lectura"""
    while not eventoparada.is_set():
        estado_actual = "NORMAL"
        
        # Leemos el estado de forma segura
        with lock_datos:
            estado_actual = datos_compartidos["estado"]
        
        if estado_actual == "ALERTA":
            # Parpadeo rápido rojo
            led_rojo.on()
            led_verde.off()
            time.sleep(0.5)
            led_rojo.off()
            time.sleep(0.5)
        else:
            # Verde cono parpadeo lento "latido"
            led_verde.on()
            led_rojo.off()
            time.sleep(1)
def gestionar_pulsacion():
    with lock_datos:
        t = datos_compartidos["temp"]
        h = datos_compartidos["hum"]
        e = datos_compartidos["estado"]
    
    #Guardar en la base de datos
    guardar_dato(t, h, e)

# --- PROGRAMA PRINCIPAL ---
def main():
    # Iniciar la base de datos
    iniciar_base_datos()
    # Crear y arrancar hilos
    t1 = threading.Thread(target=hilo_sensor_simulado,name="HiloSensorSimulado")
    t2= threading.Thread(target=hilo_indicadores_led,name="HiloIndicadoresLED")
    t1.start()
    t2.start()
    
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
        eventoparada.set()  # Señal para que los hilos terminen
        t1.join()
        t2.join()
        print("\n\nSaliendo del programa...")
        led_rojo.off()
        led_verde.off()
        print("Luces apagadas. Estación cerrada")

if __name__ == "__main__":
    main()