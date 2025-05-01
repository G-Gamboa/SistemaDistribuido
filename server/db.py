import mysql.connector
from mysql.connector import Error
import configparser
import logging
from pathlib import Path
import time

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_connection(retries=3, delay=1):
    config = configparser.ConfigParser()
    config.read(Path(__file__).parent.parent / 'server/config/config.ini')
    
    for attempt in range(retries):
        try:
            connection = mysql.connector.connect(
                host=config['mysql']['host'],
                database=config['mysql']['database'],
                user=config['mysql']['user'],
                password=config['mysql']['password'],
                port=config['mysql']['port'],
                autocommit=True,
                connection_timeout=5
            )
            logger.info("Conexión a MySQL establecida correctamente")
            return connection
        except Error as e:
            logger.error(f"Intento {attempt + 1} de {retries}: Error al conectar a MySQL - {e}")
            if attempt == retries - 1:
                raise
            time.sleep(delay)

def execute_query(query, params=None, fetch=False, retries=2):
    for attempt in range(retries):
        conn = None
        try:
            conn = create_connection()
            if conn is None:
                raise Exception("No se pudo establecer conexión a la base de datos")
                
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, params or ())
                
                if fetch:
                    result = cursor.fetchall()
                    return result
                return cursor.rowcount
                
        except Error as e:
            logger.error(f"Error en consulta (intento {attempt + 1}): {query[:100]}... - {e}")
            if attempt == retries - 1:
                raise
            time.sleep(1)
        finally:
            if conn and conn.is_connected():
                conn.close()