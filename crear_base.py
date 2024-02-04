import sqlite3
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Función para crear una base de datos SQLite y las tablas necesarias
def create_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS Folder (
        id INTEGER PRIMARY KEY,
        name TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS File (
        id INTEGER PRIMARY KEY,
        name TEXT,
        folder_id TEXT,
        file_id TEXT
    )''')

    conn.commit()
    conn.close()

# Función para subir la base de datos a Google Drive
def upload_database_to_drive():
    # Configuración de la autenticación de Google Drive
    SERVICE_ACCOUNT_FILE = 'prismatic-grail-364802-7a847bd71144.json'
    SCOPES = ['https://www.googleapis.com/auth/drive']
    FOLDER_ID = '1_V8UsygVJdZNMVpjrY_Ra8C_KBEYzyVE'

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)

    # Ruta al archivo de la base de datos SQLite local
    local_database_path = 'database.db'

    # Nombre del archivo en Google Drive
    drive_database_filename = 'database.db'

    # Subir el archivo al directorio especificado en Google Drive
    file_metadata = {
        'name': drive_database_filename,
        'parents': [FOLDER_ID]
    }

    media = MediaFileUpload(local_database_path, mimetype='application/octet-stream')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    print(f'Archivo de base de datos subido con éxito a Google Drive. File ID: {file.get("id")}')

if __name__ == '__main__':
    create_database()  # Crear la base de datos SQLite
    upload_database_to_drive()  # Subir la base de datos a Google Drive
