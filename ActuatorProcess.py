# ActuatorProcess.py
import time
import threading
from gpiozero import Button, LED
from VariablesyColas import cola_datos, cola_comandos, alerta_activa

# LEDs reales
led_rojo = LED(17)    # GPIO17 (alerta)
led_verde = LED(27)   # GPIO27 (normal)

# Umbral para activar alerta
UMBRAL_ALERTA = 26.0

def hilo_boton():
    """Botón físico en GPIO16."""
    boton = Button(16, pull_up=False, bounce_time=0.05)

    while True:
        boton.wait_for_press()
        print("[BOTÓN] Pulsado → alerta reseteada")
        cola_comandos.put("reset_alerta")
        boton.wait_for_release()

def hilo_leds():
    """Maneja LEDs según estado alerta."""
    while True:
        if alerta_activa.value:
            led_rojo.on()
            led_verde.off()
        else:
            led_rojo.off()
            led_verde.on()

        time.sleep(0.1)

def actuator_loop():
    print("[Actuador] Proceso iniciado")

    # Iniciar hilos
    threading.Thread(target=hilo_boton, daemon=True).start()
    threading.Thread(target=hilo_leds, daemon=True).start()

    while True:
        msg = cola_datos.get()

        if msg[0] == "datos":
            _, temp, hum = msg

            # Activar o desactivar alerta automáticamente
            if temp >= UMBRAL_ALERTA:
                alerta_activa.value = True
            else:
                alerta_activa.value = False

        # Comandos desde web
        if not cola_comandos.empty():
            cmd = cola_comandos.get()

            if cmd == "reset_alerta":
                alerta_activa.value = False
                print("[Actuador] Alerta reseteada manualmente")
