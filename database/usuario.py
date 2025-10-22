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
                # Para funciones con parámetros
                placeholders = ', '.join(['%s'] * len(params))
                query = f"SELECT * FROM {function_name}({placeholders})"
                cursor.execute(query, params)
            else:
                # Para funciones sin parámetros
                cursor.execute(f"SELECT * FROM {function_name}()")
            
            # Obtener descripción de las columnas para determinar el tipo de retorno
            description = cursor.description
            
            if description:  # Si retorna una tabla (múltiples columnas)
                columns = [desc[0] for desc in description]
                rows = cursor.fetchall()
                # Convertir a lista de diccionarios
                result = []
                for row in rows:
                    result.append(dict(zip(columns, row)))
                return result
            else:  # Si retorna un valor escalar
                result = cursor.fetchone()
                return result[0] if result else None
                
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

