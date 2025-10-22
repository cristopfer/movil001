from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

from database.conexion import init_db, test_connection, close_all_connections
from database.usuario import sp_loguearse, sp_registrar_usuario

app = Flask(__name__)

# Configuración
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tu-clave-secreta-aqui')

# Headers CORS manuales
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/', methods=['OPTIONS'])
@app.route('/api/<path:path>', methods=['OPTIONS'])
def options_response(path=None):
    return jsonify({"status": "OK"}), 200

@app.route('/')
def health_check():
    """Endpoint de salud de la API"""
    db_status = "connected" if test_connection() else "disconnected"
    return jsonify({
        "status": "OK", 
        "message": "API funcionando",
        "database": db_status,
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
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Inicializar la base de datos al iniciar el servidor
    try:
        init_db(app)
        print("✅ Backend inicializado correctamente")
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)