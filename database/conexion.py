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
        # Obtener configuración directamente
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'movil'),
            'sslmode': os.getenv('DB_SSLMODE', 'prefer')
        }
        
        print(f"🔧 Conectando a: {db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")
        
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=20,
            **db_config
        )
        print("✅ Conexión a PostgreSQL establecida correctamente")
        
        # Test connection
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()
            print(f"📊 PostgreSQL version: {db_version[0]}")
        return_connection(conn)
        
    except psycopg2.OperationalError as e:
        print(f"❌ Error de conexión a PostgreSQL: {e}")
        raise e
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        raise e

def get_connection():
    """
    Obtener una conexión del pool
    """
    if connection_pool:
        return connection_pool.getconn()
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