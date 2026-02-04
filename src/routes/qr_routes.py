from flask import Blueprint, request, jsonify, session, render_template_string
from src.models.user import db
from src.models.device import Device
from src.models.qr_token import QrToken
import qrcode
import io
import base64
from urllib.parse import urljoin

qr_bp = Blueprint("qr", __name__)

def require_auth():
    """Middleware para verificar autenticación"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "No autenticado"}), 401
    return None

@qr_bp.route("/api/devices/<int:device_id>/qr", methods=["GET"])
def generate_device_qr(device_id):
    """Generar código QR para un dispositivo específico"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    device = Device.query.get_or_404(device_id)
    
    # Crear la URL para la página de datos del dispositivo
    base_url = request.url_root
    # USAR UUID EN LA URL
    device_url = urljoin(base_url, f"public_device.html?uid={device.uuid}")
    
    # Generar código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(device_url)
    qr.make(fit=True)
    
    # Crear imagen QR
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir a base64 para enviar como respuesta
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    return jsonify({
        "qr_code": f"data:image/png;base64,{img_base64}",
        "device_url": device_url,
        "device": device.to_dict()
    })

@qr_bp.route("/device-info/<int:device_id>", methods=["GET"])
def device_info_page(device_id):
    """Página pública con información completa del dispositivo"""
    device = Device.query.get_or_404(device_id)
    
    # Template HTML para mostrar la información del dispositivo
    template = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ device.marca }} {{ device.nombre_catalogo }} - Información del Dispositivo</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem 0;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 0 1rem;
        }
        
        .device-card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
            margin-bottom: 2rem;
        }
        
        .device-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }
        
        .device-header h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .device-header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .device-content {
            padding: 2rem;
        }
        
        .info-section {
            margin-bottom: 2rem;
        }
        
        .info-section h2 {
            color: #667eea;
            font-size: 1.3rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 0.5rem;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }
        
        .info-item {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .info-item label {
            font-weight: 600;
            color: #555;
            display: block;
            margin-bottom: 0.3rem;
        }
        
        .info-item span {
            color: #333;
            font-size: 1rem;
        }
        
        .comments-section {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 8px;
            margin-top: 1rem;
        }
        
        .comments-section h3 {
            color: #667eea;
            margin-bottom: 0.5rem;
        }
        
        .comment-text {
            background: white;
            padding: 1rem;
            border-radius: 6px;
            margin-bottom: 1rem;
            border-left: 3px solid #667eea;
        }
        
        .footer {
            text-align: center;
            color: white;
            margin-top: 2rem;
        }
        
        .footer p {
            opacity: 0.8;
        }
        
        .back-button {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 0.8rem 1.5rem;
            text-decoration: none;
            border-radius: 8px;
            margin-bottom: 1rem;
            transition: background 0.3s;
        }
        
        .back-button:hover {
            background: #5a6fd8;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 0 0.5rem;
            }
            
            .device-header h1 {
                font-size: 1.5rem;
            }
            
            .device-content {
                padding: 1rem;
            }
            
            .info-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <button onclick="window.close()" class="back-button" style="border: none; cursor: pointer;">
            <i class="fas fa-times"></i> Cerrar
        </button>
        
        <div class="device-card">
            <div class="device-header">
                <h1>{{ device.marca }} {{ device.nombre_catalogo }}</h1>
                <p>Información Completa del Dispositivo</p>
            </div>
            
            <div class="device-content">
                <!-- Información Básica -->
                <div class="info-section">
                    <h2><i class="fas fa-info-circle"></i> Información Básica</h2>
                    <div class="info-grid">
                        <div class="info-item">
                            <label>Marca:</label>
                            <span>{{ device.marca }}</span>
                        </div>
                        <div class="info-item">
                            <label>Nombre de Catálogo:</label>
                            <span>{{ device.nombre_catalogo }}</span>
                        </div>
                        <div class="info-item">
                            <label>Modelo Comercial:</label>
                            <span>{{ device.modelo_comercial }}</span>
                        </div>
                        <div class="info-item">
                            <label>Modelo Técnico:</label>
                            <span>{{ device.modelo_tecnico }}</span>
                        </div>
                        <div class="info-item">
                            <label>Año de Lanzamiento:</label>
                            <span>{{ device.ano_lanzamiento }}</span>
                        </div>
                        <div class="info-item">
                            <label>Fecha de Vigencia:</label>
                            <span>{{ device.fecha_vigencia }}</span>
                        </div>
                    </div>
                </div>
                
                <!-- Categorización -->
                <div class="info-section">
                    <h2><i class="fas fa-tags"></i> Categorización</h2>
                    <div class="info-grid">
                        <div class="info-item">
                            <label>Categoría:</label>
                            <span>{{ device.categoria }}</span>
                        </div>
                        <div class="info-item">
                            <label>Subcategoría:</label>
                            <span>{{ device.subcategoria }}</span>
                        </div>
                        <div class="info-item">
                            <label>Grupo:</label>
                            <span>{{ device.grupo }}</span>
                        </div>
                    </div>
                </div>
                
                <!-- Imagen del Dispositivo -->
                <div class="info-section">
                    <h2><i class="fas fa-camera"></i> Imagen del Dispositivo</h2>
                    <div class="image-container" style="text-align: center; padding: 1rem;">
                        {% set image_found = false %}
                        {% for file in device.files %}
                            {% if file.file_type == 'imagen_referencia' and file.visibility == 'public' %}
                                <img src="{{ url_for('static', filename='uploads/' + file.file_name) }}" alt="Imagen del Dispositivo" style="max-width: 100%; max-height: 300px; height: auto; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                                {% set image_found = true %}
                            {% endif %}
                        {% endfor %}
                        {% if not image_found %}
                            <div class="no-image" style="background: #f8f9fa; padding: 2rem; border-radius: 8px; color: #666;">
                                <i class="fas fa-image" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                                <p>Imagen no Disponible</p>
                            </div>
                        {% endif %}
                    </div>
                </div>
                
                <!-- Comentarios -->
                {% if device.comentarios or device.comentario_subtel %}
                <div class="info-section">
                    <h2><i class="fas fa-comment"></i> Comentarios</h2>
                    <div class="comments-section">
                        {% if device.comentarios %}
                        <h3>Comentarios Generales:</h3>
                        <div class="comment-text">{{ device.comentarios }}</div>
                        {% endif %}
                        
                        {% if device.comentario_subtel %}
                        <h3>Comentario Regulatorio SUBTEL:</h3>
                        <div class="comment-text">{{ device.comentario_subtel }}</div>
                        {% endif %}
                    </div>
                </div>
                {% endif %}
                
                <!-- Información de Registro -->
                <div class="info-section">
                    <h2><i class="fas fa-clock"></i> Información de Registro</h2>
                    <div class="info-grid">
                        <div class="info-item">
                            <label>Fecha de Creación:</label>
                            <span>{{ device.created_at.strftime('%d/%m/%Y %H:%M') if device.created_at else 'No disponible' }}</span>
                        </div>
                        <div class="info-item">
                            <label>Última Actualización:</label>
                            <span>{{ device.updated_at.strftime('%d/%m/%Y %H:%M') if device.updated_at else 'No disponible' }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>&copy; 2024 Carmona QR - Sistema de Gestión de Dispositivos Electrónicos</p>
        </div>
    </div>
</body>
</html>
    """
    
    return render_template_string(template, device=device)



@qr_bp.route("/api/brands/<brand_name>/generate-qr-token", methods=["POST"])
def generate_brand_qr_token(brand_name):
    """Generar token QR para acceso directo a marca"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    # Verificar que el usuario tenga permisos para generar tokens de esta marca
    user_role = session.get('user_role')
    if user_role not in ['admin', 'auditor']:
        return jsonify({"error": "Sin permisos para generar tokens QR"}), 403
    
    try:
        # Crear token para la marca
        qr_token = QrToken.create_brand_token(brand_name, expires_hours=438000)
        
        # Generar URL con token
        base_url = request.url_root
        brand_url = f"{base_url}index.html?brand={brand_name}&token={qr_token.token}"
        
        return jsonify({
            "token": qr_token.token,
            "brand_url": brand_url,
            "expires_at": qr_token.expires_at.isoformat(),
            "brand_name": brand_name
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Error generando token: {str(e)}"}), 500

@qr_bp.route("/api/brands/<brand_name>/qr-with-token", methods=["GET"])
def get_brand_qr_with_token(brand_name):
    """Obtener código QR con token para acceso directo a marca"""
    auth_error = require_auth()
    if auth_error:
        return auth_error
    
    # Verificar permisos
    user_role = session.get('user_role')
    if user_role not in ['admin', 'auditor']:
        return jsonify({"error": "Sin permisos para generar QR con token"}), 403
    
    try:
        # Buscar token existente válido o crear uno nuevo
        existing_token = QrToken.query.filter_by(
            brand_name=brand_name, 
            token_type='brand',
            used=False
        ).first()
        
        if existing_token and existing_token.is_valid():
            qr_token = existing_token
        else:
            # Crear nuevo token
            qr_token = QrToken.create_brand_token(brand_name, expires_hours=438000)
        
        # Generar URL con token
        base_url = request.url_root
        brand_url = f"{base_url}index.html?brand={brand_name}&token={qr_token.token}"
        
        # Generar código QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(brand_url)
        qr.make(fit=True)
        
        # Crear imagen QR
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a base64
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        return jsonify({
            "qr_code": f"data:image/png;base64,{img_base64}",
            "brand_url": brand_url,
            "token": qr_token.token,
            "expires_at": qr_token.expires_at.isoformat(),
            "brand_name": brand_name
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Error generando QR: {str(e)}"}), 500
