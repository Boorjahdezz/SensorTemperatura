from gpiozero import Button, LED
import time
import threading
import multiprocessing 
from signal import pause
import random
import sqlite3               
import datetime              

# --- LÍMITES DE ALERTA ---
LIMITE_TEMP = 26  
LIMITE_HUM = 60   

# --- CONFIGURACIÓN BASE DE DATOS ---
NOMBRE_BD = "estacion_meteo.db"

# --- CONFIGURACIÓN DE HARDWARE (Botón) ---
# El botón se gestiona en el proceso principal
boton = Button(16, pull_up=False, bounce_time=0.1)

# --- VARIABLES PARA HILOS (Solo dentro del proceso principal) ---
lock_datos = threading.Lock()
datos_compartidos = {"temp": 0, "hum": 0, "estado": "NORMAL"}


# ==========================================
#   PROCESO 2: GESTIÓN DE LEDS (ACTUADORES)
# ==========================================
def proceso_leds(cola_comandos):
    """
    PROCESO INDEPENDIENTE: Se encarga solo de las luces.
    """
    led_rojo = LED(17)
    led_verde = LED(27)
    
    estado_actual = "NORMAL"
    
    # --- CORRECCIÓN: Bloque try-except para evitar errores al salir ---
    try:
        while True:
            # 1. Leer mensajes de la cola (Comunicación entre procesos)
            if not cola_comandos.empty():
                nuevo_estado = cola_comandos.get()
                if nuevo_estado != estado_actual:
                    estado_actual = nuevo_estado
            
            # 2. Actuar según estado
            if estado_actual == "ALERTA":
                # Parpadeo Rojo Rápido
                led_rojo.on()
                led_verde.off()
                time.sleep(0.2)
                led_rojo.off()
                time.sleep(0.2)
            elif estado_actual == "SHUTDOWN":
                break # Salimos del bucle limpiamente
            else:
                # Verde Normal (Latido lento)
                led_verde.on()
                led_rojo.off()
                time.sleep(0.5)

    except KeyboardInterrupt:
        # Si recibe Ctrl+C, no hacemos nada (pass) para que no salga error
        pass
    finally:
        # Aseguramos que se apaguen las luces al morir el proceso
        led_rojo.off()
        led_verde.off()

# ==========================================
#   PROCESO 1: PRINCIPAL (SENSOR + BD + WEB)
# ==========================================

def iniciar_base_datos():
    try:
        conn = sqlite3.connect(NOMBRE_BD)
        cursor = conn.cursor()
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
    except Exception as e:
        print(f"Error iniciando BD: {e}")

def guardar_dato(temp, hum, estado):
    try:
        conn = sqlite3.connect(NOMBRE_BD)
        cursor = conn.cursor()
        ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO lecturas (fecha, temperatura, humedad, estado) VALUES (?, ?, ?, ?)", 
                       (ahora, temp, hum, estado))
        conn.commit()
        conn.close()
        print("   └── [SQL] ¡Guardado en Base de Datos!")
    except Exception as e:
        print(f"[ERROR SQL] {e}")

def hilo_sensor_simulado(cola_comunicacion):
    """
    HILO SENSOR: Genera datos y los muestra por pantalla automáticamente.
    """
    ultimo_estado_enviado = "NORMAL"
    
    while True:
        with lock_datos:
            # Simulación de sensor
            datos_compartidos["temp"] = random.randint(20, 30)
            datos_compartidos["hum"] = random.randint(40, 80)
            
            # Lógica de decisión
            if datos_compartidos["temp"] > LIMITE_TEMP or datos_compartidos["hum"] > LIMITE_HUM:
                datos_compartidos["estado"] = "ALERTA"
            else:
                datos_compartidos["estado"] = "NORMAL"
            
            # Copias locales para imprimir y enviar
            t = datos_compartidos["temp"]
            h = datos_compartidos["hum"]
            e = datos_compartidos["estado"]
            
        # 1. MOSTRAR DATOS AUTOMÁTICAMENTE
        print(f"[AUTO 7s] Sensor: {t}°C | {h}% -> Estado: {e}")

        # 2. COMUNICACIÓN CON PROCESO DE LEDS
        if e != ultimo_estado_enviado:
            cola_comunicacion.put(e)
            ultimo_estado_enviado = e
        
        # Esperar 7 segundos antes de la siguiente lectura automática
        time.sleep(7)

def gestionar_pulsacion():
    """Evento del botón: Solo guarda en BD al pulsar"""
    with lock_datos:
        t = datos_compartidos["temp"]
        h = datos_compartidos["hum"]
        e = datos_compartidos["estado"]
    
    print(f"\n[BOTÓN] >>> Capturando lectura actual: {t}°C, {h}%")
    guardar_dato(t, h, e)
    print("") # Salto de línea estético

def main():
    iniciar_base_datos()
    
    # Cola de Comunicación (IPC)
    cola_estados = multiprocessing.Queue()
    
    # Arrancar PROCESO SECUNDARIO (LEDs)
    proc_leds = multiprocessing.Process(target=proceso_leds, args=(cola_estados,), name="ProcesoLEDs")
    proc_leds.start()
    
    # Arrancar HILO SENSOR (en Proceso Principal)
    t_sensor = threading.Thread(target=hilo_sensor_simulado, args=(cola_estados,), name="HiloSensor", daemon=True)
    t_sensor.start()
    
    # Configurar botón
    boton.when_pressed = gestionar_pulsacion

    print("--- ESTACION METEOROLÓGICA LISTA (MULTIPROCESO) ---")
    print("1. Los datos saldrán automáticamente cada 7 segundos.")
    print("2. Pulsa el BOTÓN para guardar el dato actual en la BD.")
    print(f"Límites -> Temp > {LIMITE_TEMP}°C o Hum > {LIMITE_HUM}% enciende ROJO.")
    print("-------------------------------------------------------")

    try:
        pause()
    except KeyboardInterrupt:
        print("\n\nSaliendo del programa...")
        
        # Intentamos avisar al otro proceso de forma ordenada
        cola_estados.put("SHUTDOWN") 
        
        # Esperamos un poco y salimos
        proc_leds.join(timeout=1)
        
        # Si el proceso seguía vivo, forzamos el apagado de LEDs
        if proc_leds.is_alive():
            proc_leds.terminate()
            
        print("Luces apagadas. Estación cerrada")

if __name__ == "__main__":
    main()