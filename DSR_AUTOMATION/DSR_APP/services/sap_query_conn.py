import platform
import pyodbc
from django.conf import settings
from .. models import DSR
import time






def create_connection(database, retry_count=3, retry_interval=5):
    """
    Create a connection to the database with retry logic.
    
    :param database: Name of the database ('NBFI' or 'EPC').
    :param retry_count: Number of times to retry the connection.
    :param retry_interval: Time in seconds between retries.
    :return: Database connection object or None if connection fails.
    """
    server = settings.DB_SERVER
    user = settings.DB_USER
    password = settings.DB_PASSWORD

    if database == 'NBFI':
        database = settings.DB_DATABASE_NBFI
    elif database == 'EPC':
        database = settings.DB_DATABASE_EPC
    elif database == 'EPCTEST':
        database = 'Z_EPC_SBOTEST'
    elif database == 'NBFITEST':
        database = 'Z_NBFI_SBOTEST'
    else:
        print("No valid database found!")
        return None

    driver = "HDBODBC" if platform.architecture()[0] == "64bit" else "HDBODBC32"
    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVERNODE={server};"
        f"UID={user};"
        f"PWD={password};"
        f"CS={database};"
    )

    for attempt in range(1, retry_count + 1):
        try:
            connection = pyodbc.connect(connection_string)
            print("Connection successful!")
            return connection
        except pyodbc.Error as e:
            print(f"Connection attempt {attempt} failed: {e}")
            if attempt < retry_count:
                print(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                print("Max retry attempts reached. Connection failed.")
                return None


def execute_query(query, database, retry_count=3, retry_interval=5):
    """
    Execute a SQL query with automatic reconnection and retry logic.
    Ensures the database connection is properly closed.
    """
    for attempt in range(1, retry_count + 1):
        connection = create_connection(database)
        if connection:
            try:
                with connection.cursor() as cursor:  # Ensures cursor closes automatically
                    cursor.execute(query)
                    columns = [column[0] for column in cursor.description]  # Get column names
                    results = cursor.fetchall()  # Fetch all rows
                    data = [dict(zip(columns, row)) for row in results]
                    print("Query executed successfully!")
                    return data
            except pyodbc.OperationalError as e:
                print(f"Database operation failed (attempt {attempt}): {e}")
                if "2006" in str(e) or "2013" in str(e):
                    print("Detected lost connection. Retrying...")
                    time.sleep(retry_interval)
                else:
                    break
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                break
            finally:
                connection.close()  # Ensure connection is always closed
        else:
            print(f"Failed to establish connection on attempt {attempt}. Retrying...")
            time.sleep(retry_interval)
    
    print("All retry attempts failed.")
    return None


