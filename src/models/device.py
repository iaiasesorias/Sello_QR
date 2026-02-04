from src.models.user import db
from datetime import datetime
import uuid

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    marca = db.Column(db.String(100), nullable=False)
    nombre_catalogo = db.Column(db.String(200), nullable=False)
    modelo_comercial = db.Column(db.String(100), nullable=False)
    modelo_tecnico = db.Column(db.String(100), nullable=False)
    ano_lanzamiento = db.Column(db.Integer, nullable=False)
    comentarios = db.Column(db.Text)

    fecha_vigencia = db.Column(db.Date, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    subcategoria = db.Column(db.String(50), nullable=False)
    grupo = db.Column(db.String(50), nullable=False)
    importador_representante = db.Column(db.String(255))
    domicilio = db.Column(db.String(255))
    correo_contacto = db.Column(db.String(255))
    tecnologia_modulacion = db.Column(db.String(255))
    frecuencias = db.Column(db.String(255))
    ganancia_antena = db.Column(db.String(255))
    pire_dbm = db.Column(db.Numeric(10, 2))
    pire_mw = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con archivos
    files = db.relationship('DeviceFile', backref='device', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Device {self.marca} {self.modelo_comercial}>'

    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'marca': self.marca,
            'nombre_catalogo': self.nombre_catalogo,
            'modelo_comercial': self.modelo_comercial,
            'modelo_tecnico': self.modelo_tecnico,
            'ano_lanzamiento': self.ano_lanzamiento,
            'comentarios': self.comentarios,
            'fecha_vigencia': self.fecha_vigencia.isoformat() if self.fecha_vigencia else None,
            'importador_representante': self.importador_representante,
            'domicilio': self.domicilio,
            'correo_contacto': self.correo_contacto,
            'tecnologia_modulacion': self.tecnologia_modulacion,
            'frecuencias': self.frecuencias,
            'ganancia_antena': self.ganancia_antena,
            'pire_dbm': float(self.pire_dbm) if self.pire_dbm is not None else 0.0,
            'pire_mw': float(self.pire_mw) if self.pire_mw is not None else 0.0,
            'categoria': self.categoria,
            'subcategoria': self.subcategoria,
            'grupo': self.grupo,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'files': [file.to_dict() for file in self.files]
        }

class DeviceFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500))
    file_type = db.Column(db.String(50), nullable=False)  # 'imagen_referencia', 'test_report', etc.
    visibility = db.Column(db.String(10), nullable=False, default='public')  # 'public' o 'private'
    external_url = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    requires_password = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<DeviceFile {self.file_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'visibility': self.visibility,
            'external_url': self.external_url,
            'file_size': self.file_size,
            'requires_password': self.requires_password,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

