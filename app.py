from flask import Flask, request, flash, render_template, url_for, send_from_directory, g, redirect
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import sqlite3
import time

app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'database.db'

SERVICE_ACCOUNT_FILE = 'Coloca aquí tu archivo JSON de credenciales'
SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_ID = 'Coloca aquí tu ID de carpeta'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=credentials)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

def list_folders():
    query = f"mimeType='application/vnd.google-apps.folder' and '{FOLDER_ID}' in parents"
    response = service.files().list(q=query, spaces='drive', fields="files(id, name)").execute()
    folders = response.get('files', [])
    folders.insert(0, {'id': 'new', 'name': 'Crear nueva etiqueta'})
    return folders

def create_folder(name):
    query = f"'{FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and name='{name}'"
    response = service.files().list(q=query, spaces='drive', fields="files(id)").execute()
    existing_folders = response.get('files', [])
    
    if existing_folders:
        return existing_folders[0]['id']
    
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [FOLDER_ID]
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')

def list_files_in_folder(folder_id):
    query = f"'{folder_id}' in parents and mimeType != 'application/vnd.google-apps.folder'"
    results = service.files().list(
        q=query,
        pageSize=100,
        fields="nextPageToken, files(id, name, parents, webContentLink, description)").execute()
    items = results.get('files', [])
    return items

def upload_to_drive(filename, folder_id):
    file_metadata = {
        'name': os.path.basename(filename),
        'parents': [folder_id]
    }
    media = MediaFileUpload(filename, mimetype='application/octet-stream')
    file = service.files().create(body=file_metadata, media_body=media, fields='id, webContentLink').execute()
    return file.get('id')

# Función para eliminar un archivo local después de la carga exitosa
def delete_uploaded_file(filename):
    try:
        os.remove(filename)
    except OSError as e:
        print(f"No se pudo eliminar el archivo {filename}: {e}")

# Función para comprobar si la categoría ya existe
def check_existing_folder(name):
    query = f"'{FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and name='{name}'"
    response = service.files().list(q=query, spaces='drive', fields="files(id)").execute()
    existing_folders = response.get('files', [])
    
    if existing_folders:
        return existing_folders[0]['id']
    else:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('documento')
        label = request.form.get('label')
        new_label = request.form.get('new_label', '').strip()

        if file and (label or new_label):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)

            if new_label:
                # Comprueba si la categoría ya existe antes de crear una nueva
                existing_folder_id = check_existing_folder(new_label.upper())

                if existing_folder_id:
                    folder_id = existing_folder_id
                    flash('Carpeta ya existe en Google Drive.')
                else:
                    folder_id = create_folder(new_label.upper())  # Convierte el nombre a mayúsculas

                # Verificar asincrónicamente la existencia de la carpeta en Google Drive
                while True:
                    time.sleep(2)  # Esperar 2 segundos antes de verificar nuevamente
                    if check_existing_folder(new_label.upper()):
                        break

            elif label == 'new':
                flash('Por favor, ingrese el nombre para la nueva etiqueta.')
                return redirect(request.url)
            else:
                folder_id = label

            file_id = upload_to_drive(filename, folder_id)

            # Llamar a la función para eliminar el archivo después de la carga
            delete_uploaded_file(filename)

            # Guardar información sobre el archivo en la base de datos
            db = get_db()
            db.execute('INSERT INTO File (name, folder_id, file_id) VALUES (?, ?, ?)',
                       [file.filename, folder_id, file_id])
            db.commit()

            return redirect(url_for('index'))

        else:
            flash('Archivo y etiqueta son requeridos')

    folders = list_folders()
    return render_template('index.html', folders=folders)

@app.route('/folders', methods=['GET'])
def folders():
    folders = list_folders()
    return render_template('folders.html', folders=folders)

@app.route('/view_files_in_folder/<folder_id>', methods=['GET'])
def view_files_in_folder(folder_id):
    files = list_files_in_folder(folder_id)
    return render_template('files_in_folder.html', files=files, folder_id=folder_id)

@app.route('/search_files', methods=['POST', 'GET'])
def search_files():
    search_query = request.form.get('search_query', '').strip().lower()  # Convirtiendo la búsqueda a minúsculas

    # Lista para almacenar todos los archivos y carpetas encontrados que coincidan con la consulta de búsqueda
    all_matched_files = []
    matched_folders = []

    if search_query:
        # Buscar en la base de datos los archivos por nombre (ahora en minúsculas)
        db = get_db()
        cursor = db.execute('SELECT * FROM File WHERE LOWER(name) LIKE ?', ['%' + search_query + '%'])
        matched_files = cursor.fetchall()
        all_matched_files.extend(matched_files)

        # Obtener todas las carpetas y filtrarlas por la consulta de búsqueda
        all_folders = list_folders()  # Asume que esta función devuelve una lista de carpetas
        matched_folders = [folder for folder in all_folders if search_query in folder['name'].lower()]

    # Pasa los archivos y carpetas encontrados a la plantilla
    return render_template('search_files.html', files=all_matched_files, folders=matched_folders)

@app.route('/search_labels', methods=['POST', 'GET'])
def search_labels():
    search_query = request.form.get('search_query', '').strip().upper()  # Convertir la búsqueda a mayúsculas

    if search_query:
        # Obtén todas las etiquetas existentes
        all_folders = list_folders()  # Asume que esta función devuelve una lista de carpetas

        # Filtra las etiquetas que coincidan con la búsqueda
        matched_folders = [folder for folder in all_folders if search_query in folder['name']]

        return render_template('search_labels.html', labels=matched_folders, search_query=search_query)

    return render_template('search_labels.html', labels=[], search_query='')


@app.route('/delete_file/<folder_id>/<file_id>', methods=['GET'])
def delete_file(folder_id, file_id):
    # Elimina el archivo de Google Drive
    service.files().delete(fileId=file_id).execute()

    # Elimina la entrada correspondiente de la base de datos
    db = get_db()
    db.execute('DELETE FROM File WHERE file_id = ?', [file_id])
    db.commit()

    # Verifica si la carpeta está vacía después de eliminar el archivo
    files_in_folder = list_files_in_folder(folder_id)
    if not files_in_folder:
        # Si la carpeta está vacía, elimina la carpeta y su registro en la base de datos
        service.files().delete(fileId=folder_id).execute()
        db.execute('DELETE FROM Folder WHERE id = ?', [folder_id])
        db.commit()

    flash('Archivo eliminado con éxito.')

    # Redirige al usuario a la página deseada, por ejemplo, la vista de archivos en la carpeta
    return redirect(url_for('view_files_in_folder', folder_id=folder_id))


if __name__ == '__main__':
    app.run(debug=True)
