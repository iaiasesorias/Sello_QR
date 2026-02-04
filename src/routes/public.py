from flask import Blueprint, render_template_string, jsonify, request, send_from_directory
from src.models.device import Device
from src.models.device_doc import DeviceDoc
import os

public_bp = Blueprint('public', __name__)

@public_bp.route('/brands')
def brand_selection():
    """Página de selección de marca"""
    return send_from_directory('static', 'brand_selection.html')

# Template HTML para la página pública del dispositivo
DEVICE_PUBLIC_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ device.marca }} {{ device.nombre_catalogo }} - Carmona QR</title>
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
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .content {
            padding: 40px;
        }
        
        .device-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .info-section {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            border-left: 4px solid #3498db;
        }
        
        .info-section h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
        }
        
        .info-item {
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .info-label {
            font-weight: 600;
            color: #555;
            min-width: 140px;
        }
        
        .info-value {
            color: #2c3e50;
            font-weight: 500;
            text-align: right;
            flex: 1;
        }
        
        .category-badge {
            background: #3498db;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 500;
        }
        
        .comments-section {
            background: #fff;
            border: 2px solid #ecf0f1;
            border-radius: 10px;
            padding: 25px;
            margin-top: 20px;
        }
        
        .comments-section h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .comment-box {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 3px solid #e74c3c;
        }
        
        .footer {
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }
        
        .info-section img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }

        
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 10px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .content {
                padding: 20px;
            }
            
            .device-info {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .info-item {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .info-value {
                text-align: left;
                margin-top: 5px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ device.marca }} {{ device.nombre_catalogo }}</h1>
            <p>Información Oficial del Dispositivo</p>
        </div>
        
        <div class="content">
            <div class="device-info">
                <div class="info-section">
                    <h3>📱 Información Básica</h3>
                    <div class="info-item">
                        <span class="info-label">Marca:</span>
                        <span class="info-value">{{ device.marca }}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Nombre Catálogo:</span>
                        <span class="info-value">{{ device.nombre_catalogo }}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Modelo Comercial:</span>
                        <span class="info-value">{{ device.modelo_comercial }}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Modelo Técnico:</span>
                        <span class="info-value">{{ device.modelo_tecnico }}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Año Lanzamiento:</span>
                        <span class="info-value">{{ device.ano_lanzamiento }}</span>
                    </div>
                </div>
                
                <div class="info-section">
                    <h3>📋 Categorización</h3>
                    <div class="info-item">
                        <span class="info-label">Categoría:</span>
                        <span class="category-badge">{{ device.categoria }}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Subcategoría:</span>
                        <span class="info-value">{{ device.subcategoria }}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Grupo:</span>
                        <span class="info-value">{{ device.grupo }}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Fecha Vigencia:</span>
                        <span class="info-value">{{ device.fecha_vigencia.strftime("%d/%m/%Y") if device.fecha_vigencia else "No especificada" }}</span>
                    </div>
                </div>
                
                <div class="info-section">
                    <h3>📸 Imagen del Dispositivo</h3>
                    <div class="info-item">
                        {% set image_found = false %}
                        {% for file in device.files %}
                            {% if file.file_type == 'imagen_referencia' and file.visibility == 'public' %}
                                <img src="{{ url_for("static", filename="uploads/" + file.file_name) }}" alt="Imagen del Dispositivo" style="max-width: 100%; height: auto; border-radius: 8px;">
                                {% set image_found = true %}
                            {% endif %}
                        {% endfor %}
                        {% if not image_found %}
                            <span class="info-value">Imagen no Disponible</span>
                        {% endif %}
                    </div>
                </div>
            </div>
            
            {% if device.comentarios %}
            <div class="comments-section">
                <h3>💬 Comentarios</h3>
                <div class="comment-box">
                    {{ device.comentarios }}
                </div>
            </div>
            {% endif %}
            
            {% if device.comentario_subtel %}
            <div class="comments-section">
                <h3>🏛️ Comentario Regulatorio SUBTEL</h3>
                <div class="comment-box">
                    {{ device.comentario_subtel }}
                </div>
            </div>
            {% endif %}
            

        </div>
        
        <div class="footer">
            <p>&copy; 2025 Sistema Carmona QR - SUBTEL Chile</p>
            <p>Información oficial de dispositivos electrónicos</p>
        </div>
    </div>
</body>
</html>
"""

@public_bp.route('/device/<int:device_id>')
def view_device(device_id):
    """Página pública para mostrar información del dispositivo"""
    device = Device.query.get_or_404(device_id)
    
    # Verificar si el dispositivo está vigente
    from datetime import datetime
    if device.fecha_vigencia and device.fecha_vigencia > datetime.now().date():
        return jsonify({
            'error': 'Dispositivo no disponible',
            'message': 'Este dispositivo aún no está vigente para consulta pública.'
        }), 404
    
    return render_template_string(DEVICE_PUBLIC_TEMPLATE, device=device)

@public_bp.route('/api/device/by-uuid/<string:device_uuid>')
def get_device_by_uuid_api(device_uuid):
    """API pública para obtener información del dispositivo por UUID"""
    device = Device.query.filter_by(uuid=device_uuid).first_or_404()
    
    # Verificar si el dispositivo está vigente
    from datetime import datetime
    if device.fecha_vigencia and device.fecha_vigencia > datetime.now().date():
        return jsonify({
            'error': 'Dispositivo no disponible',
            'message': 'Este dispositivo aún no está vigente para consulta pública.'
        }), 404
        
    return jsonify(device.to_dict())

@public_bp.route('/api/device/<int:device_id>')
def get_device_api(device_id):
    """API pública para obtener información del dispositivo en formato JSON"""
    from flask import make_response
    
    device = Device.query.get_or_404(device_id)
    
    # Verificar si el dispositivo está vigente
    from datetime import datetime
    if device.fecha_vigencia and device.fecha_vigencia > datetime.now().date():
        return jsonify({
            'error': 'Dispositivo no disponible',
            'message': 'Este dispositivo aún no está vigente para consulta pública.'
        }), 404
    
    # Usar el método to_dict() del modelo que incluye todos los campos
    device_data = device.to_dict()
    
    # Importar DeviceDoc para buscar la información de documentación
    from src.models.device_doc import DeviceDoc
    
    # Buscar la información de documentación
    device_doc = DeviceDoc.query.filter_by(
        marca=device.marca,
        nombre_catalogo=device.nombre_catalogo,
        modelo_comercial=device.modelo_comercial,
        modelo_tecnico=device.modelo_tecnico
    ).first()
    
    # Agregar los campos de device_doc a device_data si existen
    if device_doc:
        device_data['tecnologia_modulacion_doc'] = device_doc.tecnologia_modulacion_doc
        device_data['frecuencias_doc'] = device_doc.frecuencias_doc
        device_data['ganancia_antena_doc'] = device_doc.ganancia_antena_doc
        device_data['pire_dbm_doc'] = device_doc.pire_dbm_doc
        device_data['pire_mw_doc'] = device_doc.pire_mw_doc
    else:
        # Asegurar que los campos existen aunque estén vacíos
        device_data['tecnologia_modulacion_doc'] = None
        device_data['frecuencias_doc'] = None
        device_data['ganancia_antena_doc'] = None
        device_data['pire_dbm_doc'] = None
        device_data['pire_mw_doc'] = None
    
    # Filtrar solo archivos públicos
    device_data['files'] = [file.to_dict() for file in device.files if file.visibility == 'public']
    
    # Crear respuesta con headers anti-caché
    response = make_response(jsonify(device_data))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = device.updated_at.strftime('%a, %d %b %Y %H:%M:%S GMT') if device.updated_at else datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    return response




@public_bp.route('/manufacturer/<manufacturer>')
def public_manufacturer_page(manufacturer):
    """Página pública para mostrar información del fabricante"""
    from urllib.parse import unquote
    
    # Decodificar el nombre del fabricante
    decoded_manufacturer = unquote(manufacturer)
    
    # Obtener dispositivos del fabricante
    devices = Device.query.filter_by(fabricante=decoded_manufacturer).all()
    
    if not devices:
        return f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Fabricante no encontrado - Carmona QR</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0;
                    padding: 20px;
                }}
                .error-container {{
                    background: white;
                    padding: 40px;
                    border-radius: 15px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 500px;
                }}
                .error-title {{
                    color: #e74c3c;
                    font-size: 2em;
                    margin-bottom: 20px;
                }}
                .error-message {{
                    color: #666;
                    font-size: 1.2em;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1 class="error-title">Fabricante no encontrado</h1>
                <p class="error-message">No se encontraron dispositivos para el fabricante "{decoded_manufacturer}"</p>
            </div>
        </body>
        </html>
        """, 404
    
    # Generar HTML para la página del fabricante
    devices_html = ""
    for device in devices:
        devices_html += f"""
        <div class="device-card">
            <h3>{device.marca} {device.nombre_catalogo}</h3>
            <div class="device-details">
                <p><strong>Modelo Comercial:</strong> {device.modelo_comercial}</p>
                <p><strong>Modelo Técnico:</strong> {device.modelo_tecnico}</p>
                <p><strong>Año de Lanzamiento:</strong> {device.ano_lanzamiento}</p>
                <p><strong>Categoría:</strong> {device.categoria}</p>
                <p><strong>Subcategoría:</strong> {device.subcategoria}</p>
                <p><strong>Grupo:</strong> {device.grupo}</p>
                {f'<p><strong>Comentarios:</strong> {device.comentarios}</p>' if device.comentarios else ''}
                {f'<p><strong>Comentario Subtel:</strong> {device.comentario_subtel}</p>' if device.comentario_subtel else ''}
                <p><strong>Fecha de Vigencia:</strong> {device.fecha_vigencia}</p>
            </div>
        </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{decoded_manufacturer} - Carmona QR</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            
            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            
            .header {{
                background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            
            .header h1 {{
                font-size: 2.5em;
                margin-bottom: 10px;
                font-weight: 300;
            }}
            
            .header p {{
                font-size: 1.2em;
                opacity: 0.9;
            }}
            
            .content {{
                padding: 30px;
            }}
            
            .devices-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }}
            
            .device-card {{
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                border-left: 4px solid #3498db;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }}
            
            .device-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            }}
            
            .device-card h3 {{
                color: #2c3e50;
                margin-bottom: 15px;
                font-size: 1.3em;
            }}
            
            .device-details p {{
                margin-bottom: 8px;
                color: #555;
            }}
            
            .device-details strong {{
                color: #2c3e50;
            }}
            
            .stats {{
                background: #ecf0f1;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
                text-align: center;
            }}
            
            .stats h2 {{
                color: #2c3e50;
                margin-bottom: 10px;
            }}
            
            .stats p {{
                font-size: 1.1em;
                color: #555;
            }}
            
            @media (max-width: 768px) {{
                .devices-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .header h1 {{
                    font-size: 2em;
                }}
                
                .container {{
                    margin: 10px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{decoded_manufacturer}</h1>
                <p>Información de dispositivos del fabricante</p>
            </div>
            
            <div class="content">
                <div class="stats">
                    <h2>Estadísticas del Fabricante</h2>
                    <p>Total de dispositivos registrados: <strong>{len(devices)}</strong></p>
                </div>
                
                <h2>Dispositivos Registrados</h2>
                <div class="devices-grid">
                    {devices_html}
                </div>
            </div>
        </div>
    </body>
    </html>
    """

