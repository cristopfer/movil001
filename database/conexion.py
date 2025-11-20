import psycopg2
from psycopg2 import pool
import os
from dotenv import load_dotenv 
load_dotenv()

# Pool de conexiones para PostgreSQL
connection_pool = None

def init_db(app):
    global connection_pool
    try:
        # Leer variables de entorno y limpiar caracteres
        db_config = {
            'host': str(os.getenv('DB_HOST', 'localhost')).strip(),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': str(os.getenv('DB_USER', 'postgres')).strip(),
            'password': str(os.getenv('DB_PASSWORD', '')).strip(),
            'database': str(os.getenv('DB_NAME', 'movil')).strip(),
        }
        
        # Crear string de conexión manualmente
        connection_string = f"host='{db_config['host']}' port='{db_config['port']}' dbname='{db_config['database']}' user='{db_config['user']}' password='{db_config['password']}'"
        
        print(f"🔧 Conectando a: {db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")
        
        # Crear pool con string de conexión
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=20,
            dsn=connection_string
        )
        
        print("✅ Conexión a PostgreSQL establecida correctamente")
        
        # Test connection seguro
        conn = get_connection()
        conn.set_client_encoding('UTF8')
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()
            # Manejo seguro del string
            if db_version and db_version[0]:
                safe_version = db_version[0]
                if isinstance(safe_version, bytes):
                    safe_version = safe_version.decode('utf-8', errors='replace')
                print(f"📊 PostgreSQL conectado correctamente")
        
        return_connection(conn)
        
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        connection_pool = None

# Las demás funciones permanecen igual...
def get_connection():
    """
    Obtener una conexión del pool
    """
    if connection_pool:
        conn = connection_pool.getconn()
        # Configurar encoding en cada conexión
        conn.set_client_encoding('UTF8')
        return conn
    else:
        raise Exception("Pool de conexiones no inicializado")

def return_connection(connection):
    """
    Devolver conexión al pool
    """
    if connection_pool and connection:
        connection_pool.putconn(connection)

def close_all_connections():
    """
    Cerrar todas las conexiones del pool
    """
    if connection_pool:
        connection_pool.closeall()
        print("🔒 Todas las conexiones de PostgreSQL cerradas")

def test_connection():
    """
    Función para probar la conexión a la base de datos
    """
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
        return_connection(conn)
        return result[0] == 1
    except Exception as e:
        print(f"❌ Error probando conexión: {e}")
        return False