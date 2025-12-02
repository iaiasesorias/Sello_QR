
import os
from flask import Blueprint, jsonify, request, session, send_file
from werkzeug.utils import secure_filename
from src.models.user import db
from src.models.device import Device, DeviceFile

files_bp = Blueprint('files', __name__)

# Ruta base de la aplicación para construir rutas relativas
from flask import current_app # Añadir esta importación

# Rutas relativas a BASE_DIR
# La ruta relativa ahora será solo la subcarpeta dentro de UPLOAD_FOLDER

# Rutas absolutas para uso interno del servidor
# UPLOAD_FOLDER se obtendrá de current_app.config['UPLOAD_FOLDER'] en las funciones.
UPLOAD_FOLDER_DEVICES = 'brands' # Subcarpeta dentro de UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"pdf", "zip", "jpg", "jpeg", "png", "gif"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB
MAX_TOTAL_SIZE = 150 * 1024 * 1024  # 150MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_device_upload_folder_relative(brand_name, device_name):
    """Obtener la ruta de subida relativa para archivos de un dispositivo específico"""
    return os.path.join(UPLOAD_FOLDER_DEVICES, secure_filename(brand_name), secure_filename(device_name))

def require_admin():
    """Middleware para verificar rol de administrador"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'No autenticado'}), 401
    
    user_role = session.get('user_role')
    if user_role != 'admin':
        return jsonify({'error': 'Acceso denegado. Se requiere rol de administrador'}), 403
    return None

@files_bp.route('/files/upload-brand-logo', methods=['POST'])
def upload_brand_logo():
    """Subir logo de marca"""
    admin_error = require_admin()
    if admin_error:
        return admin_error
    
    if 'file' not in request.files:
        return jsonify({'error': 'No se encontró archivo'}), 400
    
    file = request.files['file']
    brand_name = request.form.get('brand_name')
    
    if not brand_name:
        return jsonify({'error': 'brand_name es requerido'}), 400
    
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó archivo'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
    
    # Verificar tamaño del archivo
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': f'Archivo muy grande. Máximo {MAX_FILE_SIZE // (1024*1024)}MB'}), 400
    
    # Crear directorio de marca si no existe
    base_upload_folder = current_app.config['UPLOAD_FOLDER']
    brand_folder_absolute = os.path.join(base_upload_folder, UPLOAD_FOLDER_DEVICES, secure_filename(brand_name))
    os.makedirs(brand_folder_absolute, exist_ok=True)
    
    # Generar nombre único para el archivo del logo
    filename = f"{secure_filename(brand_name)}.{file.filename.rsplit('.', 1)[1].lower()}"
    file_path_absolute = os.path.join(brand_folder_absolute, filename)
    file_path_relative = os.path.join(UPLOAD_FOLDER_DEVICES, secure_filename(brand_name), filename)
    
    try:
        file.save(file_path_absolute)
        return jsonify({
            'message': 'Logo de marca subido exitosamente',
            'file_path': file_path_relative, # Almacenar ruta relativa
            'file_name': filename,
            'brand_name': brand_name
        }), 201
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error interno del servidor al guardar archivo: {str(e)}"}), 500

@files_bp.route('/files/upload-device-files', methods=['POST'])
def upload_device_files():
    """Subir archivos para un dispositivo específico"""
    admin_error = require_admin()
    if admin_error:
        return admin_error
    
    if 'file' not in request.files:
        return jsonify({'error': 'No se encontró archivo'}), 400
    
    file = request.files['file']
    device_id = request.form.get('device_id')
    file_type = request.form.get('file_type')
    visibility = request.form.get('visibility', 'public')
    external_url = request.form.get('external_url')
    
    if not device_id or not file_type:
        return jsonify({'error': 'device_id y file_type son requeridos'}), 400
    
    # Verificar que el dispositivo existe
    device = Device.query.get(device_id)
    if not device:
        return jsonify({'error': 'Dispositivo no encontrado'}), 404
    
    # Si se proporciona URL externa, no necesitamos archivo
    if external_url:
        device_file = DeviceFile(
            device_id=device_id,
            file_name=request.form.get('file_name', 'Documento externo'),
            file_type=file_type,
            visibility=visibility,
            external_url=external_url
        )
        
        db.session.add(device_file)
        db.session.commit()
        
        return jsonify(device_file.to_dict()), 201
    
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó archivo'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
    
    # Verificar tamaño del archivo
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': f'Archivo muy grande. Máximo {MAX_FILE_SIZE // (1024*1024)}MB'}), 400
    
    # Verificar tamaño total de archivos del dispositivo
    total_size = sum([f.file_size or 0 for f in device.files if f.file_size])
    if total_size + file_size > MAX_TOTAL_SIZE:
        return jsonify({'error': f'Tamaño total de archivos excede el límite de {MAX_TOTAL_SIZE // (1024*1024)}MB'}), 400
    
    # Crear directorio de marca y dispositivo si no existen usando la nueva función
    device_folder_relative = get_device_upload_folder_relative(device.marca, device.nombre_catalogo)
    base_upload_folder = current_app.config['UPLOAD_FOLDER']
    device_folder_absolute = os.path.join(base_upload_folder, device_folder_relative)
    os.makedirs(device_folder_absolute, exist_ok=True)
    
    # Generar nombre único para el archivo
    filename = secure_filename(file.filename)
    file_path_absolute = os.path.join(device_folder_absolute, filename)
    file_path_relative = os.path.join(device_folder_relative, filename)
    
    try:
        file.save(file_path_absolute)
        
        device_file = DeviceFile(
            device_id=device_id,
            file_name=filename,
            file_path=file_path_relative, # Almacenar ruta relativa
            file_type=file_type,
            visibility=visibility,
            file_size=file_size
        )
        
        db.session.add(device_file)
        db.session.commit()
        
        return jsonify(device_file.to_dict()), 201
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error interno del servidor al guardar archivo: {str(e)}"}), 500

@files_bp.route('/files/upload', methods=['POST'])
def upload_file():
    """Subir archivo para un dispositivo (ruta original mantenida para compatibilidad)"""
    admin_error = require_admin()
    if admin_error:
        return admin_error
    
    if 'file' not in request.files:
        return jsonify({'error': 'No se encontró archivo'}), 400
    
    file = request.files['file']
    device_id = request.form.get('device_id')
    file_type = request.form.get('file_type')
    visibility = request.form.get('visibility', 'public')
    external_url = request.form.get('external_url')
    
    if not device_id or not file_type:
        return jsonify({'error': 'device_id y file_type son requeridos'}), 400
    
    # Verificar que el dispositivo existe
    device = Device.query.get(device_id)
    if not device:
        return jsonify({'error': 'Dispositivo no encontrado'}), 404
    
    # Si se proporciona URL externa, no necesitamos archivo
    if external_url:
        device_file = DeviceFile(
            device_id=device_id,
            file_name=request.form.get('file_name', 'Documento externo'),
            file_type=file_type,
            visibility=visibility,
            external_url=external_url
        )
        
        db.session.add(device_file)
        db.session.commit()
        
        return jsonify(device_file.to_dict()), 201
    
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó archivo'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
    
    # Verificar tamaño del archivo
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': f'Archivo muy grande. Máximo {MAX_FILE_SIZE // (1024*1024)}MB'}), 400
    
    # Verificar tamaño total de archivos del dispositivo
    total_size = sum([f.file_size or 0 for f in device.files if f.file_size])
    if total_size + file_size > MAX_TOTAL_SIZE:
        return jsonify({'error': f'Tamaño total de archivos excede el límite de {MAX_TOTAL_SIZE // (1024*1024)}MB'}), 400
    
    # Crear directorio de marca y dispositivo si no existen
    device_folder_relative = get_device_upload_folder_relative(device.marca, device.nombre_catalogo)
    base_upload_folder = current_app.config['UPLOAD_FOLDER']
    device_folder_absolute = os.path.join(base_upload_folder, device_folder_relative)
    os.makedirs(device_folder_absolute, exist_ok=True)
    
    # Generar nombre único para el archivo
    filename = secure_filename(file.filename)
    file_path_absolute = os.path.join(device_folder_absolute, filename)
    file_path_relative = os.path.join(device_folder_relative, filename)
    try:
        file.save(file_path_absolute)
        
        device_file = DeviceFile(
            device_id=device_id,
            file_name=filename,
            file_path=file_path_relative, # Almacenar ruta relativa
            file_type=file_type,
            visibility=visibility,
            file_size=file_size
        )
        
        db.session.add(device_file)
        db.session.commit()
        
        return jsonify(device_file.to_dict()), 201
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error interno del servidor al guardar archivo: {str(e)}"}), 500

@files_bp.route('/files/<int:file_id>', methods=['GET'])
def download_file(file_id):
    """Descargar archivo"""
    device_file = DeviceFile.query.get_or_404(file_id)
    user_role = session.get('user_role')
    
    # Verificar permisos de visibilidad
    if device_file.visibility == 'private' and not user_role:
        return jsonify({'error': 'Acceso denegado'}), 403
    
    # Si es URL externa, redirigir
    if device_file.external_url:
        return jsonify({'external_url': device_file.external_url})
    
    # Construir la ruta absoluta para servir el archivo
    base_upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path_absolute = os.path.join(base_upload_folder, device_file.file_path)

    if not device_file.file_path or not os.path.exists(file_path_absolute):
        return jsonify({'error': 'Archivo no encontrado'}), 404
    
    return send_file(file_path_absolute, as_attachment=True, download_name=device_file.file_name)

@files_bp.route('/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Eliminar archivo"""
    admin_error = require_admin()
    if admin_error:
        return admin_error
    
    device_file = DeviceFile.query.get_or_404(file_id)
    
    # Eliminar archivo físico si existe
    if device_file.file_path:
        base_upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path_absolute = os.path.join(base_upload_folder, device_file.file_path)
    if os.path.exists(file_path_absolute):
        try:
            os.remove(file_path_absolute)
        except Exception as e:
            print(f"Error al eliminar archivo físico: {e}")
    
    db.session.delete(device_file)
    db.session.commit()
    
    return '', 204

@files_bp.route('/files/<int:file_id>', methods=['PUT'])
def update_file(file_id):
    """Actualizar metadatos de archivo"""
    admin_error = require_admin()
    if admin_error:
        return admin_error
    
    device_file = DeviceFile.query.get_or_404(file_id)
    data = request.json
    
    device_file.file_name = data.get('file_name', device_file.file_name)
    device_file.visibility = data.get('visibility', device_file.visibility)
    device_file.external_url = data.get('external_url', device_file.external_url)
    
    db.session.commit()
    
    return jsonify(device_file.to_dict())

@files_bp.route('/file-types', methods=['GET'])
def get_file_types():
    """Obtener tipos de archivo disponibles"""
    file_types = [
        'imagen_referencia',
        'test_report',
        'imagenes_externas',
        'imagenes_internas',
        'diagrama_bloques',
        'ganancia_antena',
        'guia_usuario',
        'otros_documentos'
    ]
    return jsonify(file_types)


