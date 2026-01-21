from flask import Blueprint, request, send_from_directory, jsonify, abort
import os
from src.models.device import DeviceFile
from src.models.user import db
from flask import current_app

password_protected_downloads_bp = Blueprint("password_protected_downloads", __name__)

# Contraseña de ejemplo
DOWNLOAD_PASSWORD = "Carmona2025"

@password_protected_downloads_bp.route("/download-protected-file/<int:file_id>", methods=["GET"])
def download_protected_file(file_id):
    """
    Descarga un archivo, verificando si requiere contraseña.
    """
    try:
        # Buscar el archivo en la base de datos por ID
        device_file = DeviceFile.query.get(file_id)
        
        if not device_file:
            abort(404, description="Archivo no encontrado en la base de datos.")
        
        # Verificar si el archivo requiere contraseña
        if device_file.requires_password:
            password = request.args.get("password")
            if not password or password != DOWNLOAD_PASSWORD:
                abort(401, description="Contraseña incorrecta o no proporcionada.")
        
        # Obtener la ruta del archivo desde la base de datos
        file_path = device_file.file_path
        
        if not file_path:
            abort(404, description="Ruta del archivo no disponible.")
        
        # Normalizar las barras de la ruta
        file_path = file_path.replace('\\', '/')
        
        # Construir la ruta completa al archivo
        upload_folder = current_app.config['UPLOAD_FOLDER']
        full_file_path = os.path.join(upload_folder, file_path)
        full_file_path = os.path.normpath(full_file_path)
        
        # Verificar si el archivo existe
        if not os.path.exists(full_file_path):
            # Intentar rutas alternativas
            filename_only = os.path.basename(file_path)
            alt_path = os.path.join(upload_folder, filename_only)
            alt_path = os.path.normpath(alt_path)
            if os.path.exists(alt_path):
                full_file_path = alt_path
            else:
                abort(404, description="Archivo físico no encontrado.")
        
        # Obtener el directorio y nombre del archivo
        file_directory = os.path.dirname(full_file_path)
        filename = os.path.basename(full_file_path)
        
        # Usar el nombre original del archivo si está disponible
        download_name = device_file.file_name if device_file.file_name else filename
        
        return send_from_directory(
            file_directory, 
            filename, 
            as_attachment=True,
            download_name=download_name
        )
        
    except Exception as e:
        if hasattr(e, 'code'):
            raise e
        abort(500, description=f"Error interno del servidor: {str(e)}")

@password_protected_downloads_bp.route("/download-protected-file-by-path/<path:filename>", methods=["GET"])
def download_protected_file_by_path(filename):
    """
    Descarga un archivo por ruta (mantiene compatibilidad, pero siempre requiere contraseña por seguridad en esta ruta).
    """
    password = request.args.get("password")

    if not password or password != DOWNLOAD_PASSWORD:
        abort(401, description="Contraseña incorrecta o no proporcionada.")

    try:
        filename = filename.replace('\\', '/')
        safe_filename = filename.replace('..', '').replace('//', '/')
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        full_file_path = os.path.join(upload_folder, safe_filename)
        full_file_path = os.path.normpath(full_file_path)
        
        if not full_file_path.startswith(os.path.abspath(current_app.config['UPLOAD_FOLDER'])):
            abort(403, description="Acceso denegado.")
        
        if not os.path.exists(full_file_path):
            abort(404, description="Archivo no encontrado.")
        
        file_directory = os.path.dirname(full_file_path)
        basename = os.path.basename(full_file_path)
        
        return send_from_directory(file_directory, basename, as_attachment=True)
        
    except Exception as e:
        if hasattr(e, 'code'):
            raise e
        abort(500, description=f"Error interno del servidor: {str(e)}")
