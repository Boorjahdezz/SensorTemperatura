# web_server.py
from flask import Flask, jsonify
from VariablesyColas import temp_actual, hum_actual, alerta_activa, cola_comandos

app = Flask(__name__)

@app.get("/data")
def obtener_datos():
    """Datos para la web."""
    return jsonify({
        "temperatura": temp_actual.value,
        "humedad": hum_actual.value,
        "alerta": alerta_activa.value
    })

@app.get("/reset")
def resetear_alerta():
    cola_comandos.put("reset_alerta")
    return {"ok": True}

def lanzar_web():
    print("[Web] Servidor en http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)
