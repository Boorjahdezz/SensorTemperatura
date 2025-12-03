from gpiozero import Button, LED
from signal import pause
import random

# --- CONFIGURACIÓN DE HARDWARE ---
# Ajusta pull_up=False o True según cómo te haya funcionado finalmente el botón
led_rojo = LED(17)   
led_verde = LED(27)  
boton = Button(16, pull_up=False, bounce_time=0.1)

# --- UMBRALES ---
LIMITE_TEMP = 26     
LIMITE_HUM = 60      

def gestionar_pulsacion():
    """
    Se ejecuta SOLO al pulsar el botón.
    """
    # 1. Generar valores (trucados para ver cambios 22, 25, 27)
    temp = random.choice([22, 25, 27]) 
    hum = random.choice([40, 55, 70])

    # 2. Lógica de LEDs (Semáforo)
    if temp > LIMITE_TEMP or hum > LIMITE_HUM:
        led_rojo.on()
        led_verde.off()
        estado_msg = "ALERTA (Supera límites)"
    else:
        led_verde.on()
        led_rojo.off()
        estado_msg = "NORMAL (Valores seguros)"

    print(f"[CLICK] Temp: {temp}°C | Hum: {hum}%  -->  LED: {estado_msg}")

# --- PROGRAMA PRINCIPAL ---
def main():
    # Estado inicial
    led_rojo.off()
    led_verde.off() 
    

    
    
    print("--- ESTACION METEOROLÓGICA LISTA ---")
    print("Programa corriendo. Pulsa el botón para leer datos.")
    print("Pulsa Ctrl + C para salir limpiamente.")
    print(f"Límites -> Temp > {LIMITE_TEMP}°C o Hum > {LIMITE_HUM}% enciende ROJO.")

    # Asignamos el evento
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