import psycopg2
from database.conexion import get_connection, return_connection

def sp_guardar_historial(correo, riesgo, area_sospechosa, probabilidad, clasificacion, recomendacion):
    """
    Guarda un análisis en el historial del usuario - VERSIÓN DEBUG
    """
    print(f"📥 Datos recibidos en sp_guardar_historial:")
    print(f"   correo: {correo}")
    print(f"   riesgo: {riesgo}")
    print(f"   area_sospechosa: {area_sospechosa}")
    print(f"   probabilidad: {probabilidad} (tipo: {type(probabilidad)})")
    print(f"   clasificacion: {clasificacion}")
    print(f"   recomendacion: {recomendacion}")
    
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # ✅ CONVERTIR probabilidad a float explícitamente
            probabilidad_float = float(probabilidad)
            
            print(f"🔍 Ejecutando función PostgreSQL...")
            cursor.execute(
                "SELECT * FROM sp_guardar_historial(%s, %s, %s, %s, %s, %s)",
                [correo, riesgo, area_sospechosa, probabilidad_float, clasificacion, recomendacion]
            )
            
            # Obtener los resultados
            result = cursor.fetchone()
            print(f"🔍 Resultado RAW de PostgreSQL: {result}")
            print(f"🔍 Tipo de resultado: {type(result)}")
            if result:
                print(f"🔍 Longitud del resultado: {len(result)}")
                for i, item in enumerate(result):
                    print(f"   [{i}] = {item} (tipo: {type(item)})")
            
            connection.commit()
            
            if result and len(result) >= 3:
                response = {
                    "mensaje": str(result[0]) if result[0] is not None else "Éxito",
                    "num_analisis": str(result[1]) if result[1] is not None else "N/A", 
                    "id_historial": int(result[2]) if result[2] is not None else 0
                }
                print(f"✅ Respuesta formateada: {response}")
                return response
            else:
                print("⚠️  Resultado inesperado, pero continuando...")
                return {
                    "mensaje": "Análisis procesado",
                    "num_analisis": "Por confirmar",
                    "id_historial": 0
                }
                
    except psycopg2.Error as e:
        connection.rollback()
        print(f"❌ Error de PostgreSQL: {e}")
        raise Exception(f"Error de base de datos: {e}")
    except Exception as e:
        connection.rollback()
        print(f"❌ Error general: {e}")
        raise e
    finally:
        return_connection(connection)

def sp_obtener_historial_usuario(correo):
    """
    Obtiene el historial de análisis filtrado por correo de usuario
    
    Args:
        correo (str): Correo del usuario (requerido)
    
    Returns:
        list: Lista de análisis del usuario ordenados por fecha descendente
    """
    print(f"📋 Obteniendo historial para usuario: {correo}")
    
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # ✅ Llamar a la función PostgreSQL con solo el parámetro correo
            cursor.execute(
                "SELECT * FROM sp_mostrar_historial_filtrado(%s)",
                [correo]
            )
            
            # Obtener todos los resultados
            results = cursor.fetchall()
            print(f"🔍 Resultados RAW de PostgreSQL: {len(results)} registros")
            
            # Convertir a lista de diccionarios
            historial = []
            for row in results:
                if len(row) >= 7:  # Según la estructura de RETURNS TABLE
                    item = {
                        "num_analisis": row[0],
                        "riesgo": row[1],
                        "area_sospechosa": row[2],
                        "probabilidad": float(row[3]) if row[3] is not None else 0.0,
                        "clasificacion": row[4],
                        "recomendacion": row[5],
                        "fecha": row[6].isoformat() if row[6] else None
                    }
                    historial.append(item)
                    print(f"   📄 {item['num_analisis']} - {item['riesgo']} - {item['fecha']}")
                else:
                    print(f"⚠️  Fila con formato inesperado: {row}")
            
            print(f"✅ Historial formateado: {len(historial)} registros")
            return historial
                
    except psycopg2.Error as e:
        print(f"❌ Error de PostgreSQL: {e}")
        # Manejar errores específicos de PostgreSQL
        if "no puede estar vacío" in str(e):
            raise Exception("El correo es requerido")
        elif "no encontrado" in str(e):
            raise Exception(f"Usuario con correo {correo} no encontrado")
        else:
            raise Exception(f"Error de base de datos: {e}")
    except Exception as e:
        print(f"❌ Error general: {e}")
        raise e
    finally:
        return_connection(connection)

