from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Configuración de la base de datos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOMBRE_BD = "estacion_meteo.db"

def get_db_connection():
    """Crea una conexión a la base de datos"""
    conn = sqlite3.connect(NOMBRE_BD)
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    return conn

def get_latest_reading():
    """Obtiene la última lectura de la base de datos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM lecturas 
            ORDER BY id DESC 
            LIMIT 1
        """)
        lectura = cursor.fetchone()
        conn.close()
        
        if lectura:
            return {
                "id": lectura["id"],
                "fecha": lectura["fecha"],
                "temperatura": lectura["temperatura"],
                "humedad": lectura["humedad"],
                "estado": lectura["estado"]
            }
        else:
            return None
    except Exception as e:
        print(f"Error obteniendo última lectura: {e}")
        return None

def get_recent_readings(limit=20):
    """Obtiene las últimas N lecturas para gráficos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM lecturas 
            ORDER BY id DESC 
            LIMIT ?
        """, (limit,))
        lecturas = cursor.fetchall()
        conn.close()
        
        # Invertir para que estén en orden cronológico
        lecturas = list(reversed(lecturas))
        
        return [{
            "id": l["id"],
            "fecha": l["fecha"],
            "temperatura": l["temperatura"],
            "humedad": l["humedad"],
            "estado": l["estado"]
        } for l in lecturas]
    except Exception as e:
        print(f"Error obteniendo lecturas recientes: {e}")
        return []

def get_statistics():
    """Calcula estadísticas de las lecturas"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(temperatura) as temp_promedio,
                MAX(temperatura) as temp_maxima,
                MIN(temperatura) as temp_minima,
                AVG(humedad) as hum_promedio,
                MAX(humedad) as hum_maxima,
                MIN(humedad) as hum_minima,
                SUM(CASE WHEN estado = 'ALERTA' THEN 1 ELSE 0 END) as total_alertas
            FROM lecturas
        """)
        stats = cursor.fetchone()
        conn.close()
        
        if stats and stats["total"] > 0:
            return {
                "total_lecturas": stats["total"],
                "temp_promedio": round(stats["temp_promedio"], 1),
                "temp_maxima": stats["temp_maxima"],
                "temp_minima": stats["temp_minima"],
                "hum_promedio": round(stats["hum_promedio"], 1),
                "hum_maxima": stats["hum_maxima"],
                "hum_minima": stats["hum_minima"],
                "total_alertas": stats["total_alertas"]
            }
        else:
            return None
    except Exception as e:
        print(f"Error calculando estadísticas: {e}")
        return None

@app.route("/")
def index():
    """Página principal"""
    ultima_lectura = get_latest_reading()
    estadisticas = get_statistics()
    
    # Preparar datos para mostrar en la página
    if ultima_lectura:
        datos_sensores = {
            "temperatura": f"{ultima_lectura['temperatura']}",
            "humedad": f"{ultima_lectura['humedad']}",
            "estado_led": "Encendido" if ultima_lectura['estado'] == "ALERTA" else "Apagado",
            "fecha": ultima_lectura['fecha'],
            "estado": ultima_lectura['estado']
        }
    else:
        datos_sensores = {
            "temperatura": "N/D",
            "humedad": "N/D",
            "estado_led": "N/D",
            "fecha": "Sin datos",
            "estado": "N/D"
        }
    
    return render_template("index.html", 
                         data=datos_sensores, 
                         stats=estadisticas)

@app.route("/api/ultima_lectura")
def api_ultima_lectura():
    """API para obtener la última lectura (para AJAX)"""
    lectura = get_latest_reading()
    if lectura:
        return jsonify({
            "success": True,
            "data": lectura
        })
    else:
        return jsonify({
            "success": False,
            "message": "No hay datos disponibles"
        }), 404

@app.route("/api/lecturas_recientes")
def api_lecturas_recientes():
    """API para obtener lecturas recientes para gráficos"""
    limit = request.args.get('limit', 20, type=int)
    lecturas = get_recent_readings(limit)
    return jsonify({
        "success": True,
        "data": lecturas
    })

@app.route("/api/estadisticas")
def api_estadisticas():
    """API para obtener estadísticas"""
    stats = get_statistics()
    if stats:
        return jsonify({
            "success": True,
            "data": stats
        })
    else:
        return jsonify({
            "success": False,
            "message": "No hay suficientes datos"
        }), 404

@app.route("/historial")
def historial():
    """Página con historial completo"""
    lecturas = get_recent_readings(100)  # Últimas 100 lecturas
    return render_template("historial.html", lecturas=lecturas)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)