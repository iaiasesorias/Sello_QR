import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.models.device import Device, DeviceFile  # Importar modelos para crear tablas
from src.models.brand import Brand  # Importar modelo Brand
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.devices import devices_bp
from src.routes.public import public_bp
from src.routes.qr_routes import qr_bp
from src.routes.files import files_bp
from src.password_protected_downloads import password_protected_downloads_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

# Configuración para manejo de archivos
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB máximo
# Configuración para manejo de archivos
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(os.path.dirname(__file__), 'static', 'uploads'))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configurar CORS para permitir requests del frontend
CORS(app, supports_credentials=True)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(devices_bp, url_prefix='/api')
app.register_blueprint(qr_bp)  # Sin prefijo /api para las páginas públicas
app.register_blueprint(public_bp)
app.register_blueprint(files_bp, url_prefix='/api')
app.register_blueprint(password_protected_downloads_bp, url_prefix='/api')

# Ruta para servir archivos cargados desde el disco persistente
@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    # Asegurarse de que solo se sirvan archivos dentro de la carpeta de cargas
    return send_from_directory(UPLOAD_FOLDER, filename)
# Configuración de base de datos
# app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__),
# 'database', 'app.db')}"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL") or \
                                  f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Crear tablas y datos iniciales
with app.app_context():
    db.create_all()
    
    # Crear usuario administrador por defecto si no existe
    from src.models.user import User
    admin_user = User.query.filter_by(email='admin@carmona.net').first()
    if not admin_user:
        admin_user = User(email='admin@carmona.net', role='admin')
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        print("Usuario administrador creado: admin@carmona.net / admin123")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
