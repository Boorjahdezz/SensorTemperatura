# main.py
from multiprocessing import Process
from SensorProcess import sensor_loop
from ActuatorProcess import actuator_loop
from WebServer import lanzar_web

if __name__ == "__main__":
    print("[MAIN] Iniciando estación meteorológica...")

    p_sensor = Process(target=sensor_loop)
    p_act = Process(target=actuator_loop)
    p_web = Process(target=lanzar_web)

    p_sensor.start()
    p_act.start()
    p_web.start()

    p_sensor.join()
    p_act.join()
    p_web.join()
