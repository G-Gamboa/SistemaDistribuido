import mysql.connector
from mysql.connector import Error
import configparser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_connection():
    config = configparser.ConfigParser()
    config.read('server/config.ini')
    
    try:
        connection = mysql.connector.connect(
            host=config['mysql']['host'],
            database=config['mysql']['database'],
            user=config['mysql']['user'],
            password=config['mysql']['password'],
            port=config['mysql']['port']
        )
        logger.info("Conexión a MySQL establecida correctamente")
        return connection
    except Error as e:
        logger.error(f"Error al conectar a MySQL: {e}")
        return None

def execute_query(query, params=None, fetch=False):
    conn = create_connection()
    if conn is None:
        return None
        
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchall()
            return result
        else:
            conn.commit()
            return cursor.rowcount
            
    except Error as e:
        logger.error(f"Error en consulta SQL: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()