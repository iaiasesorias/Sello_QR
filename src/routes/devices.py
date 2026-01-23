from flask import Blueprint, jsonify, request, session, send_from_directory
from src.models.user import db, User # Importar User
from src.models.device import Device, DeviceFile
from src.models.device_doc import DeviceDoc
from src.models.brand import Brand
from src.models.qr_token import QrToken # Importar QrToken
from datetime import datetime, date
import os
import shutil # Importar shutil para eliminar directorios no vacíos
from werkzeug.utils import secure_filename

from flask import current_app # Añadir esta importación
# UPLOAD_FOLDER se obtendrá de current_app.config['UPLOAD_FOLDER'] en las funciones.
# La subcarpeta 'brands' se añadirá dentro de las funciones.
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

devices_bp = Blueprint("devices", __name__)

def require_auth():
    """Middleware para verificar autenticación"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401
    return None

def require_admin():
    """Middleware para verificar rol de administrador"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    user_role = session.get("user_role")
    if user_role != "admin":
        return jsonify({"error": "Acceso denegado. Se requiere rol de administrador"}), 403
    return None

@devices_bp.route("/devices", methods=["GET"])
def get_devices():
    """Obtener lista de dispositivos"""
    user_role = session.get("user_role")
    current_date = date.today()
    marca_filter = request.args.get("marca")

    query = Device.query

    # Filtrar dispositivos temporales para que no aparezcan en la lista
    query = query.filter(Device.nombre_catalogo != "Dispositivo Temporal")

    # Si no está autenticado o es auditor, solo mostrar dispositivos vigentes
    if not user_role or user_role == "auditor":
        query = query.filter(Device.fecha_vigencia <= current_date)

    if marca_filter:
        query = query.filter(Device.marca == marca_filter)

    devices = query.all()
    
    return jsonify([device.to_dict() for device in devices])

@devices_bp.route("/devices/<int:device_id>", methods=["GET"])
def get_device(device_id):
    """Obtener dispositivo específico"""
    device = Device.query.get_or_404(device_id)
    user_role = session.get("user_role")
    current_date = date.today()
    
    # Verificar si el dispositivo está vigente para usuarios no admin
    if user_role != "admin" and device.fecha_vigencia > current_date:
        return jsonify({"error": "Dispositivo no encontrado"}), 404
    
    return jsonify(device.to_dict())

@devices_bp.route("/devices", methods=["POST"])
def create_device():
    """Crear nuevo dispositivo (solo admin)"""
    admin_error = require_admin()
    if admin_error:
        return admin_error
    
    data = request.json
    
    # Validar campos requeridos
    required_fields = ["marca", "nombre_catalogo", "modelo_comercial", "modelo_tecnico", 
                      "ano_lanzamiento", "fecha_vigencia", "categoria", "subcategoria", "grupo"]
    
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Campo requerido: {field}"}), 400
    
    try:
        # Convertir fecha_vigencia de string a date
        fecha_vigencia = datetime.strptime(data["fecha_vigencia"], "%Y-%m-%d").date()
        
        device = Device(
            marca=data["marca"],
            nombre_catalogo=data["nombre_catalogo"],
            modelo_comercial=data["modelo_comercial"],
            modelo_tecnico=data["modelo_tecnico"],
            ano_lanzamiento=int(data["ano_lanzamiento"]),
            comentarios=data.get("comentarios", ""),

            fecha_vigencia=fecha_vigencia,
            categoria=data["categoria"],
            subcategoria=data["subcategoria"],
            grupo=data["grupo"],
            importador_representante=data.get("importador_representante"),
            domicilio=data.get("domicilio"),
            correo_contacto=data.get("correo_contacto"),
            tecnologia_modulacion=data.get("tecnologia_modulacion"),
            frecuencias=data.get("frecuencias"),
            ganancia_antena=data.get("ganancia_antena"),
            pire_dbm=float(data["pire_dbm"]) if "pire_dbm" in data and data["pire_dbm"] is not None else None,
            pire_mw=float(data["pire_mw"]) if "pire_mw" in data and data["pire_mw"] is not None else None
        )
        
        db.session.add(device)
        db.session.commit()

        # Crear directorio de marca y dispositivo si no existen
        base_upload_folder = current_app.config['UPLOAD_FOLDER']
        brand_folder = os.path.join(base_upload_folder, 'brands', secure_filename(device.marca))
        device_folder = os.path.join(brand_folder, secure_filename(device.nombre_catalogo))
        os.makedirs(device_folder, exist_ok=True)

        
        return jsonify(device.to_dict()), 201
        
    except ValueError as e:
        return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@devices_bp.route("/devices/<int:device_id>", methods=["PUT"])
def update_device(device_id):
    """Actualizar dispositivo (solo admin)"""
    admin_error = require_admin()
    if admin_error:
        return admin_error
    
    device = Device.query.get_or_404(device_id)
    data = request.json
    
    try:
        # Actualizar campos
        device.marca = data.get("marca", device.marca)
        old_nombre_catalogo = device.nombre_catalogo
        device.nombre_catalogo = data.get("nombre_catalogo", device.nombre_catalogo)
        # Renombrar la carpeta del dispositivo si el nombre del catálogo ha cambiado
        if old_nombre_catalogo != device.nombre_catalogo:
            base_upload_folder = current_app.config['UPLOAD_FOLDER']
            old_device_folder = os.path.join(base_upload_folder, 'brands', secure_filename(device.marca), secure_filename(old_nombre_catalogo))
            new_device_folder = os.path.join(base_upload_folder, 'brands', secure_filename(device.marca), secure_filename(device.nombre_catalogo))
            if os.path.exists(old_device_folder):
                os.rename(old_device_folder, new_device_folder)
            else:
                os.makedirs(new_device_folder, exist_ok=True)

        device.modelo_comercial = data.get("modelo_comercial", device.modelo_comercial)
        device.modelo_tecnico = data.get("modelo_tecnico", device.modelo_tecnico)
        device.ano_lanzamiento = int(data.get("ano_lanzamiento", device.ano_lanzamiento))
        device.comentarios = data.get("comentarios", device.comentarios)

        device.categoria = data.get("categoria", device.categoria)
        device.subcategoria = data.get("subcategoria", device.subcategoria)
        device.grupo = data.get("grupo", device.grupo)
        device.importador_representante = data.get("importador_representante", device.importador_representante)
        device.domicilio = data.get("domicilio", device.domicilio)
        device.correo_contacto = data.get("correo_contacto", device.correo_contacto)
        device.tecnologia_modulacion = data.get("tecnologia_modulacion", device.tecnologia_modulacion)
        device.frecuencias = data.get("frecuencias", device.frecuencias)
        device.ganancia_antena = data.get("ganancia_antena", device.ganancia_antena)
        device.pire_dbm = float(data["pire_dbm"]) if "pire_dbm" in data else device.pire_dbm
        device.pire_mw = float(data["pire_mw"]) if "pire_mw" in data else device.pire_mw
        
        if data.get("fecha_vigencia"):
            device.fecha_vigencia = datetime.strptime(data["fecha_vigencia"], "%Y-%m-%d").date()
        
        device.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(device.to_dict())
        
    except ValueError as e:
        return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@devices_bp.route("/devices/<int:device_id>", methods=["DELETE"])
def delete_device(device_id):
    """Eliminar dispositivo (solo admin)"""
    admin_error = require_admin()
    if admin_error:
        return admin_error
    
    device = Device.query.get_or_404(device_id)
    # Obtener la marca y el nombre del catálogo del dispositivo antes de eliminarlo
    device_marca = device.marca
    device_nombre_catalogo = device.nombre_catalogo

    # Buscar y eliminar el registro asociado en DeviceDoc
    device_doc = DeviceDoc.query.filter_by(
        marca=device.marca,
        nombre_catalogo=device.nombre_catalogo,
        modelo_comercial=device.modelo_comercial,
        modelo_tecnico=device.modelo_tecnico
    ).first()
    
    if device_doc:
        db.session.delete(device_doc)

    db.session.delete(device)
    db.session.commit()

    # Eliminar la carpeta del dispositivo si existe y está vacía
    base_upload_folder = current_app.config['UPLOAD_FOLDER']
    device_folder = os.path.join(base_upload_folder, 'brands', secure_filename(device_marca), secure_filename(device_nombre_catalogo))
    if os.path.exists(device_folder) and not os.listdir(device_folder):
        os.rmdir(device_folder)

    
    return jsonify({"message": "Dispositivo eliminado exitosamente", "marca": device_marca}), 200

@devices_bp.route("/categories", methods=["GET"])
def get_categories():
    """Obtener categorías disponibles"""
    categories = [
        "Computador",
        "Tablet",
        "Teléfono celular",
        "Reloj Inteligente",
        "Gafas y Visores",
        "Audio",
        "TV & Home",
        "Accesorios",
	"Modems",
	"Router",
        "Otros"
    ]
    return jsonify(categories)

@devices_bp.route("/categories/<category>/subcategories", methods=["GET"])
def get_subcategories(category):
    """Obtener subcategorías para una categoría"""
    # Ejemplo de subcategorías - en un caso real esto vendría de la base de datos
    subcategories_map = {
        "Computador": ["Computador A", "Computador B", "Laptop", "Desktop"],
        "Tablet": ["Tablet A", "Tablet B", "iPad", "Android Tablet"],
        "Teléfono celular": ["Smartphone", "Feature Phone"],
        "Reloj Inteligente": ["Smart Watch", "Fitness Tracker"],
        "Gafas y Visores": ["VR Headset", "AR Glasses"],
        "Audio": ["Auriculares", "Accesorios", "Micrófonos", "Parlantes", "Soundbar", "Tornamesas", "Otros"],
        "TV & Home": ["Smart TV", "Streaming Device", "Home Assistant"],
        "Accesorios": ["Cargadores", "Cables", "Fundas"],
	"Modems": ["Inalámbricos", "Fibra óptica", "Cableados", "DSL", "Dial-Up"],
	"Router": ["Inalámbricos (Wi-Fi)", "Cableados", "Móviles"],
        "Otros": ["Otros dispositivos"]
    }
    
    subcategories = subcategories_map.get(category, [])
    return jsonify(subcategories)

@devices_bp.route("/categories/<category>/<subcategory>/groups", methods=["GET"])
def get_groups(category, subcategory):
    """Obtener grupos para una subcategoría"""
    # Ejemplo de grupos - en un caso real esto vendría de la base de datos
    current_year = datetime.now().year
    groups = [str(year) for year in range(current_year, current_year - 10, -1)]
    return jsonify(groups)

@devices_bp.route("/brands", methods=["GET"])
def get_brands():
    """Obtener lista de marcas únicas"""
    try:
        # Obtener marcas únicas de la base de datos
        brands = db.session.query(Device.marca).distinct().all()
        brand_list = [brand[0] for brand in brands if brand[0]]  # Filtrar valores None
        brand_list.sort()  # Ordenar alfabéticamente
        
        return jsonify(brand_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@devices_bp.route("/brands", methods=["POST"])
def create_brand():
    """Crear nueva marca (solo admin)"""
    admin_error = require_admin()
    if admin_error:
        return admin_error
    
    # Usar request.form para datos de formulario y request.files para archivos
    marca = request.form.get("marca")
    url = request.form.get("url")  # Capturar la URL
    user = request.form.get("user")  # Capturar el usuario
    password = request.form.get("password")  # Capturar la contraseña
    image = request.files.get("image")
    
    if not marca:
        return jsonify({"error": "Campo requerido: marca"}), 400
    
    if not user:
        return jsonify({"error": "Campo requerido: usuario"}), 400
    
    if not password:
        return jsonify({"error": "Campo requerido: contraseña"}), 400
    
    marca = marca.strip()
    user = user.strip()
    
    if not marca:
        return jsonify({"error": "El nombre de la marca no puede estar vacío"}), 400
    
    if not user:
        return jsonify({"error": "El usuario no puede estar vacío"}), 400
    
    try:
        # Verificar si la marca ya existe en la tabla Brand
        existing_brand = Brand.query.filter(Brand.name == marca).first()
        if existing_brand:
            return jsonify({"error": "La marca ya existe"}), 400
        
        # Verificar si la marca ya existe en Device (para compatibilidad)
        existing_device_brand = db.session.query(Device.marca).filter(Device.marca == marca).first()
        if existing_device_brand:
            return jsonify({"error": "La marca ya existe"}), 400
        
        # Verificar si el usuario ya existe
        existing_user = User.query.filter_by(email=user).first()
        if existing_user:
            return jsonify({"error": "El usuario ya existe"}), 400
        
        # Crear la carpeta de la marca
        base_upload_folder = current_app.config['UPLOAD_FOLDER']
        brand_upload_folder = os.path.join(base_upload_folder, 'brands', secure_filename(marca))
        os.makedirs(brand_upload_folder, exist_ok=True)
        
        # Crear un dispositivo temporal para mantener compatibilidad
        temp_device = Device(
            marca=marca,
            nombre_catalogo="Dispositivo Temporal",
            modelo_comercial="Temporal",
            modelo_tecnico="Temporal",
            ano_lanzamiento=2024,
            fecha_vigencia=date.today(),
            categoria="Otros",
            subcategoria="Otros",
            grupo="2024",
            comentarios="Dispositivo temporal creado para registrar la marca"
        )
        db.session.add(temp_device)
        db.session.flush() # Para obtener el ID del dispositivo temporal

        image_path_relative = None
        # Guardar la imagen si existe
        if image and allowed_file(image.filename):
            file_extension = image.filename.rsplit(".", 1)[1].lower()
            filename = secure_filename(f"{marca}.{file_extension}")
            image_path_full = os.path.join(brand_upload_folder, filename)
            image.save(image_path_full)
            image_path_relative = os.path.join("brands", secure_filename(marca), filename)

            # Guardar la ruta de la imagen en la tabla DeviceFile
            new_device_file = DeviceFile(
                device_id=temp_device.id,
                file_name=filename,
                file_path=image_path_relative,
                file_type="imagen_marca",
                visibility="public"
            )
            db.session.add(new_device_file)
        
        # Crear el usuario con rol "public" y asociar la marca
        new_user = User(email=user, role="public", brand_name=marca)
        new_user.set_password(password)
        db.session.add(new_user)
        
        # Crear la marca en la nueva tabla Brand
        new_brand = Brand(
            name=marca,
            url=url.strip() if url else None,
            image_path=image_path_relative # Usar la ruta relativa de la imagen
        )
        
        db.session.add(new_brand)
        
        db.session.commit()
        
        return jsonify({"message": "Marca y usuario creados exitosamente", "marca": marca, "usuario": user}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@devices_bp.route("/brands/<brand_name>", methods=["PUT"])
def update_brand(brand_name):
    """Actualizar marca (solo admin)"""
    admin_error = require_admin()
    if admin_error:
        return admin_error
    
    new_marca = request.form.get("newMarca")
    url = request.form.get("url")  # Capturar la URL
    image = request.files.get("image")

    if not new_marca:
        return jsonify({"error": "Campo requerido: newMarca"}), 400

    new_marca = new_marca.strip()

    if not new_marca:
        return jsonify({"error": "El nuevo nombre de la marca no puede estar vacío"}), 400

    try:
        # Buscar la marca en la tabla Brand
        brand = Brand.query.filter(Brand.name == brand_name).first()
        
        # Si no existe en Brand, buscar el dispositivo temporal para compatibilidad
        temp_device = Device.query.filter(Device.marca == brand_name, Device.nombre_catalogo == "Dispositivo Temporal").first()
        
        if not brand and not temp_device:
            return jsonify({"error": "Marca no encontrada"}), 404

        # Verificar si el nuevo nombre de marca ya existe (excluyendo la marca actual)
        if new_marca != brand_name:
            existing_brand = Brand.query.filter(Brand.name == new_marca).first()
            if existing_brand:
                return jsonify({"error": "El nuevo nombre de marca ya existe"}), 400
            
            existing_device_brand = db.session.query(Device.marca).filter(Device.marca == new_marca).first()
            if existing_device_brand:
                return jsonify({"error": "El nuevo nombre de marca ya existe"}), 400

        # Renombrar la carpeta de la marca si el nombre ha cambiado
        base_upload_folder = current_app.config['UPLOAD_FOLDER']
        old_brand_folder = os.path.join(base_upload_folder, 'brands', secure_filename(brand_name))
        new_brand_folder = os.path.join(base_upload_folder, 'brands', secure_filename(new_marca))
        
        if new_marca != brand_name and os.path.exists(old_brand_folder):
            os.rename(old_brand_folder, new_brand_folder)
        elif new_marca != brand_name and not os.path.exists(new_brand_folder):
            os.makedirs(new_brand_folder, exist_ok=True)
        
        # Actualizar la marca en la tabla Brand
        if brand:
            brand.name = new_marca
            if url is not None:
                brand.url = url.strip() if url else None
            brand.updated_at = datetime.utcnow()
            
            # Actualizar la ruta de la imagen si existe
            if brand.image_path:
                # Reconstruir la nueva ruta relativa
                old_filename = os.path.basename(brand.image_path)
                new_image_path_relative = os.path.join( "src", "static", "uploads", "brands", secure_filename(new_marca), old_filename)
                brand.image_path = new_image_path_relative
        
        # Actualizar la marca en la tabla Device (para todos los dispositivos, incluyendo el temporal)
        devices_to_update = Device.query.filter(Device.marca == brand_name).all()
        for device in devices_to_update:
            device.marca = new_marca
            device.updated_at = datetime.utcnow()
            
        # Actualizar la marca en la tabla User
        users_to_update = User.query.filter(User.brand_name == brand_name).all()
        for user in users_to_update:
            user.brand_name = new_marca
            
        # Manejar la actualización de la imagen
        if image and allowed_file(image.filename):
            # Obtener la ruta absoluta base del proyecto
            base_upload_folder = current_app.config['UPLOAD_FOLDER']
            
            # 1. Eliminar la imagen anterior si existe
            if brand and brand.image_path:
                old_image_path_full = os.path.join(base_upload_folder, brand.image_path)
                if os.path.exists(old_image_path_full):
                    os.remove(old_image_path_full)
            
            # 2. Guardar la nueva imagen
            file_extension = image.filename.rsplit(".", 1)[1].lower()
            filename = secure_filename(f"{new_marca}.{file_extension}")
            image_path_full = os.path.join(new_brand_folder, filename)
            image.save(image_path_full)
            image_path_relative = os.path.join("brands", secure_filename(new_marca), filename)
            
            # 3. Actualizar la ruta en Brand
            if brand:
                brand.image_path = image_path_relative
            
            # 4. Actualizar la ruta en DeviceFile (solo para el dispositivo temporal)
            if temp_device:
                device_file = DeviceFile.query.filter_by(device_id=temp_device.id, file_type="imagen_marca").first()
                if device_file:
                    device_file.file_name = filename
                    device_file.file_path = image_path_relative
                else:
                    # Si no existe, crearlo
                    new_device_file = DeviceFile(
                        device_id=temp_device.id,
                        file_name=filename,
                        file_path=image_path_relative,
                        file_type="imagen_marca",
                        visibility="public"
                    )
                    db.session.add(new_device_file)

        db.session.commit()
        
        return jsonify({"message": "Marca actualizada exitosamente", "marca": new_marca}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@devices_bp.route("/brands/<brand_name>", methods=["DELETE"])
def delete_brand(brand_name):
    """Eliminar marca (solo admin)"""
    admin_error = require_admin()
    if admin_error:
        return admin_error
    
    try:
        # 1. Buscar todos los dispositivos de la marca (incluyendo el temporal)
        devices_to_delete = Device.query.filter(Device.marca == brand_name).all()
        
        if not devices_to_delete:
            # Si no hay dispositivos, verificar si existe en la tabla Brand
            brand_to_delete = Brand.query.filter(Brand.name == brand_name).first()
            if not brand_to_delete:
                return jsonify({"error": "Marca no encontrada"}), 404
        
        # 2. Eliminar usuarios asociados a la marca
        users_to_delete = User.query.filter(User.brand_name == brand_name).all()
        for user in users_to_delete:
            db.session.delete(user)
            
        # 3. Eliminar imágenes de marca asociadas y los dispositivos
        for device in devices_to_delete:
            # El tipo de archivo correcto es "imagen_marca"
            brand_images = DeviceFile.query.filter_by(device_id=device.id, file_type="imagen_marca").all()
            for img in brand_images:
                # Construir la ruta completa para eliminar el archivo
                if img.file_path:
                    base_upload_folder = current_app.config['UPLOAD_FOLDER']
                    full_path = os.path.join(base_upload_folder, img.file_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                db.session.delete(img)

            # Eliminar el dispositivo
            db.session.delete(device)

        # 4. Eliminar tokens QR asociados a la marca
        qr_tokens_to_delete = QrToken.query.filter(QrToken.brand_name == brand_name).all()
        for token in qr_tokens_to_delete:
            db.session.delete(token)

        # 5. Eliminar la marca de la tabla Brand
        brand_to_delete = Brand.query.filter(Brand.name == brand_name).first()
        if brand_to_delete:
            db.session.delete(brand_to_delete)
        
        db.session.commit()

        # 5. Eliminar la carpeta de la marca (incluyendo su contenido)
        base_upload_folder = current_app.config['UPLOAD_FOLDER']
        brand_folder = os.path.join(base_upload_folder, 'brands', secure_filename(brand_name))
        if os.path.exists(brand_folder):
            shutil.rmtree(brand_folder) # Elimina el directorio y todo su contenido
        
        return jsonify({"message": f"Marca \"{brand_name}\", usuarios asociados, dispositivos y carpeta de uploads eliminados exitosamente"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@devices_bp.route("/brands/<brand_name>/image", methods=["GET"])
def get_brand_image(brand_name):
    """Servir la imagen de una marca"""
    try:
        # Buscar la marca en la tabla Brand para obtener la ruta de la imagen
        brand = Brand.query.filter(Brand.name == brand_name).first()
        
        if not brand or not brand.image_path:
            # Para compatibilidad, buscar el dispositivo temporal asociado a la marca
            temp_device = Device.query.filter(Device.marca == brand_name, Device.nombre_catalogo == "Dispositivo Temporal").first()
            if not temp_device:
                return jsonify({"error": "Marca no encontrada"}), 404

            brand_image = DeviceFile.query.filter_by(device_id=temp_device.id, file_type="imagen_marca").first()
            
            base_upload_folder = current_app.config['UPLOAD_FOLDER']
            if not brand_image or not brand_image.file_path or not os.path.exists(os.path.join(base_upload_folder, brand_image.file_path)):
                return jsonify({"error": "Imagen no encontrada para esta marca"}), 404
            
            # Usar la ruta de DeviceFile
            image_path = brand_image.file_path
        else:
            # Usar la ruta de Brand
            image_path = brand.image_path
            
        # La ruta relativa es: src/static/uploads/brands/MARCA/imagen.ext
        # Necesitamos el directorio base (UPLOAD_FOLDER) y el nombre del archivo
        base_upload_folder = current_app.config['UPLOAD_FOLDER']
        brand_folder = os.path.join(base_upload_folder, 'brands', secure_filename(brand_name))
        filename = os.path.basename(image_path)
        
        return send_from_directory(brand_folder, filename)
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@devices_bp.route("/device_doc/<int:device_id>", methods=["PUT"])
def update_device_doc(device_id):
    """Actualizar o crear la información de documentación de un dispositivo (solo admin)"""
    admin_error = require_admin()
    if admin_error:
        return admin_error
    
    data = request.json
    
    # 1. Obtener el dispositivo principal para obtener los campos de identificación
    device = Device.query.get_or_404(device_id)
    
    # 2. Buscar si ya existe una entrada en DeviceDoc para este dispositivo
    # Asumimos que la combinación de los campos de identificación es única para el dispositivo
    device_doc = DeviceDoc.query.filter_by(
        marca=device.marca,
        nombre_catalogo=device.nombre_catalogo,
        modelo_comercial=device.modelo_comercial,
        modelo_tecnico=device.modelo_tecnico
    ).first()
    
    try:
        if device_doc:
            # Actualizar campos
            device_doc.tecnologia_modulacion_doc = data.get("tecnologia_modulacion_doc", device_doc.tecnologia_modulacion_doc)
            device_doc.frecuencias_doc = data.get("frecuencias_doc", device_doc.frecuencias_doc)
            device_doc.ganancia_antena_doc = data.get("ganancia_antena_doc", device_doc.ganancia_antena_doc)
            device_doc.pire_dbm_doc = data.get("pire_dbm_doc", device_doc.pire_dbm_doc)
            device_doc.pire_mw_doc = data.get("pire_mw_doc", device_doc.pire_mw_doc)
        else:
            # Crear nueva entrada
            device_doc = DeviceDoc(
                marca=device.marca,
                nombre_catalogo=device.nombre_catalogo,
                modelo_comercial=device.modelo_comercial,
                modelo_tecnico=device.modelo_tecnico,
                tecnologia_modulacion_doc=data.get("tecnologia_modulacion_doc"),
                frecuencias_doc=data.get("frecuencias_doc"),
                ganancia_antena_doc=data.get("ganancia_antena_doc"),
                pire_dbm_doc=data.get("pire_dbm_doc"),
                pire_mw_doc=data.get("pire_mw_doc")
            )
            db.session.add(device_doc)
            
        db.session.commit()
        
        return jsonify({"message": "Información de documentación actualizada exitosamente"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@devices_bp.route("/brands/<brand_name>/info", methods=["GET"])
def get_brand_info(brand_name):
    """Obtener información completa de una marca"""
    try:
        # Buscar la marca en la tabla Brand
        brand = Brand.query.filter(Brand.name == brand_name).first()
        
        if brand:
            return jsonify({
                "name": brand.name,
                "url": brand.url,
                "image_path": brand.image_path,
                "created_at": brand.created_at.isoformat() if brand.created_at else None,
                "updated_at": brand.updated_at.isoformat() if brand.updated_at else None
            })
        else:
            # Para compatibilidad, buscar en dispositivos temporales
            temp_device = Device.query.filter(Device.marca == brand_name, Device.nombre_catalogo == "Dispositivo Temporal").first()
            if temp_device:
                return jsonify({
                    "name": brand_name,
                    "url": None,  # Las marcas antiguas no tienen URL
                    "image_path": None,
                    "created_at": None,
                    "updated_at": None
                })
            else:
                return jsonify({"error": "Marca no encontrada"}), 404
                
    except Exception as e:
        return jsonify({"error": str(e)}), 500

