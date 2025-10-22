import psycopg2
from database.conexion import get_connection, return_connection

def call_postgres_function(function_name, params=None):
    """
    Función genérica para llamar funciones de PostgreSQL
    Maneja tanto funciones que retornan tablas como valores escalares
    """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            if params:
                placeholders = ', '.join(['%s'] * len(params))
                query = f"SELECT {function_name}({placeholders})"
                cursor.execute(query, params)
            else:
                cursor.execute(f"SELECT {function_name}()")
            
            # Para funciones que retornan valores escalares
            result = cursor.fetchone()
            
            if result:
                return result[0]  # Retornar el primer valor (escalar)
            else:
                return None
                
    except psycopg2.Error as e:
        print(f"❌ Error de PostgreSQL ejecutando {function_name}: {e}")
        raise Exception(f"Error de base de datos: {e}")
    except Exception as e:
        print(f"❌ Error ejecutando función {function_name}: {e}")
        raise e
    finally:
        return_connection(connection)

def sp_loguearse(correo, password):
    """
    Loguear usuario y retornar estado
    Retorna: 0=inactivo, 1=activo, 2=bloqueado
    """
    try:
        result = call_postgres_function('sp_loguearse', [correo, password])
        return result
    except Exception as e:
        raise Exception(f"Error en login: {str(e)}")

