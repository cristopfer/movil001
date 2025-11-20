import os
from datetime import datetime
from flask_cors import CORS  
import gc

# Crear carpeta para uploads si no existe
os.makedirs('temp_uploads', exist_ok=True)

from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

from database.conexion import init_db, test_connection, close_all_connections
from database.usuario import sp_loguearse, sp_registrar_usuario, sp_aceptar_condiciones
from database.historial import sp_guardar_historial, sp_obtener_historial_usuario

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

CORS(app, supports_credentials=True)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tu-clave-secreta-aqui')
app.config['UPLOAD_FOLDER'] = 'temp_uploads'

# ✅ INICIALIZACIÓN ÚNICA de base de datos
print("🚀 Inicializando aplicación...")
try:
    # Inicializar el pool de conexiones UNA SOLA VEZ
    init_db(app)
    print("✅ Base de datos inicializada correctamente")
except Exception as e:
    print(f"❌ Error inicializando BD: {e}")

# Headers CORS manuales
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept,Origin,X-Requested-With,ngrok-skip-browser-warning')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Max-Age', '86400')
    return response

@app.route('/', methods=['OPTIONS'])
@app.route('/api/<path:path>', methods=['OPTIONS'])
def options_response(path=None):
    return jsonify({"status": "OK"}), 200

@app.route('/')
def health_check():
    """Endpoint de salud de la API"""
    db_status = "connected" if test_connection() else "disconnected"
    
    ia_status = "not_loaded"  # Siempre "not_loaded" porque se carga bajo demanda
    
    return jsonify({
        "status": "OK", 
        "message": "API funcionando",
        "database": db_status,
        "ai_model": ia_status,
        "service": "Prostate AI Backend"
    })


@app.route('/api/db-status')
def db_status():
    """Endpoint para verificar estado de la base de datos"""
    try:
        if test_connection():
            return jsonify({
                "status": "connected",
                "message": "Conexión a PostgreSQL establecida correctamente"
            })
        else:
            return jsonify({
                "status": "disconnected",
                "message": "Error de conexión a PostgreSQL"
            }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    """Endpoint para login de usuario"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "OK"}), 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No se recibieron datos JSON"
            }), 400
            
        correo = data.get('correo')
        password = data.get('password')
        
        if not correo or not password:
            return jsonify({
                "success": False,
                "error": "Correo y password son requeridos"
            }), 400
        
        # Llamar a la función de PostgreSQL
        estado = sp_loguearse(correo, password)
        
        # Interpretar el estado
        if estado == 1:
            mensaje_estado = "Login exitoso"
        elif estado == 0:
            mensaje_estado = "Cuenta inactiva. Debe aceptar los términos y condiciones."
        elif estado == 2:
            mensaje_estado = "Cuenta bloqueada. Contacte al administrador."
        else:
            mensaje_estado = "Estado desconocido"
        
        return jsonify({
            "success": True,
            "message": "Login exitoso",
            "estado": estado,
            "mensaje_estado": mensaje_estado,
            "user": {
                "correo": correo,
                "estado": estado
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 401

@app.route('/api/register', methods=['POST', 'OPTIONS'])
def register():
    """Endpoint para registro de nuevo usuario"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "OK"}), 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No se recibieron datos JSON"
            }), 400
            
        nombre = data.get('nombre')
        correo = data.get('correo')
        password = data.get('password')
        
        # Validar campos requeridos
        if not nombre or not correo or not password:
            return jsonify({
                "success": False,
                "error": "Nombre, correo y password son requeridos"
            }), 400
        
        # Validar longitud mínima de password
        if len(password) < 6:
            return jsonify({
                "success": False,
                "error": "La contraseña debe tener al menos 6 caracteres"
            }), 400
        
        # Llamar a la función de PostgreSQL
        resultado = sp_registrar_usuario(nombre, correo, password)
        
        if resultado == 1:
            return jsonify({
                "success": True,
                "message": "Usuario registrado exitosamente",
                "user": {
                    "nombre": nombre,
                    "correo": correo,
                    "estado": 0  # Estado inactivo por defecto
                }
            }), 201
        else:
            return jsonify({
                "success": False,
                "error": "Error desconocido al registrar usuario"
            }), 500
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/accept-terms', methods=['POST', 'OPTIONS'])
def accept_terms():
    """Endpoint para aceptar términos y condiciones"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "OK"}), 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No se recibieron datos JSON"
            }), 400
            
        correo = data.get('correo')
        password = data.get('password')
        
        if not correo or not password:
            return jsonify({
                "success": False,
                "error": "Correo y password son requeridos"
            }), 400
        
        # Llamar a la función de PostgreSQL
        resultado = sp_aceptar_condiciones(correo, password)
        
        if resultado == 1:
            return jsonify({
                "success": True,
                "message": "Términos y condiciones aceptados exitosamente. Cuenta activada.",
                "user": {
                    "correo": correo,
                    "estado": 1  # Estado activo
                }
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Error desconocido al aceptar términos y condiciones"
            }), 500
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    
@app.route('/api/guardar_analisis', methods=['POST', 'OPTIONS'])
def guardar_analisis():
    """Endpoint para guardar un análisis en el historial"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "OK"}), 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No se recibieron datos JSON"
            }), 400
            
        # Obtener datos del request
        correo = data.get('correo')
        riesgo = data.get('riesgo')
        area_sospechosa = data.get('area_sospechosa')
        probabilidad = data.get('probabilidad')
        clasificacion = data.get('clasificacion')
        recomendacion = data.get('recomendacion')
        
        print(f"📥 Datos recibidos en endpoint:")
        print(f"   probabilidad: {probabilidad} (tipo: {type(probabilidad)})")
        
        # Validar campos requeridos
        campos_requeridos = ['correo', 'riesgo', 'area_sospechosa', 'probabilidad', 'clasificacion']
        for campo in campos_requeridos:
            if not data.get(campo):
                return jsonify({
                    "success": False,
                    "error": f"El campo '{campo}' es requerido"
                }), 400
        
        # Convertir probabilidad a float
        try:
            # ✅ Asegurar que sea float
            if isinstance(probabilidad, str):
                probabilidad = float(probabilidad.replace('%', ''))
            else:
                probabilidad = float(probabilidad)
        except (ValueError, TypeError) as e:
            return jsonify({
                "success": False,
                "error": f"La probabilidad debe ser un número válido: {e}"
            }), 400
        
        print(f"🔧 Probabilidad convertida: {probabilidad} (tipo: {type(probabilidad)})")
        
        # Llamar a la función PostgreSQL
        resultado = sp_guardar_historial(
            correo=correo,
            riesgo=riesgo,
            area_sospechosa=area_sospechosa,
            probabilidad=probabilidad,
            clasificacion=clasificacion,
            recomendacion=recomendacion or ""
        )
        
        return jsonify({
            "success": True,
            "message": resultado["mensaje"],
            "data": {
                "num_analisis": resultado["num_analisis"],
                "id_historial": resultado["id_historial"]
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error en endpoint guardar_analisis: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    
@app.route('/api/historial_usuario', methods=['POST', 'OPTIONS'])  # ✅ Asegúrate que tenga POST
def historial_usuario():
    """Endpoint para obtener historial por usuario"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "OK"}), 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No se recibieron datos JSON"
            }), 400
            
        correo = data.get('correo')
        
        if not correo:
            return jsonify({
                "success": False,
                "error": "El correo es requerido"
            }), 400
        
        # Llamar a la función PostgreSQL
        historial = sp_obtener_historial_usuario(correo)
        
        return jsonify({
            "success": True,
            "message": f"Se encontraron {len(historial)} análisis",
            "data": historial,
            "count": len(historial)
        }), 200
        
    except Exception as e:
        print(f"❌ Error en historial_usuario: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

# Manejo de errores global
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint no encontrado"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Error interno del servidor"
    }), 500

# Cerrar conexiones al apagar la app
import atexit
@atexit.register
def shutdown():
    close_all_connections()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print("🚀 Iniciando servidor sin cargar modelo de IA...")
    print("📝 Modelo de IA: Se cargará bajo demanda cuando se use /api/analizar")
    
    #app.run(host='0.0.0.0', port=port, debug=debug)
    app.run(host='192.168.100.23', port=port, debug=False)