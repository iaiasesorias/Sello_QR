// JavaScript para la página pública de dispositivos
document.addEventListener("DOMContentLoaded", function () {
  loadDeviceInfo();
});

async function loadDeviceInfo() {
  const urlParams = new URLSearchParams(window.location.search);
  const deviceId = urlParams.get("id");
  const deviceUid = urlParams.get("uid"); // CAMBIO: leer 'uid' en lugar de 'id'

  if (!deviceId && !deviceUid) {
    showError();
    return;
  }

  try {
    // Agregar timestamp para evitar caché del navegador
    const timestamp = new Date().getTime();
    
    // Determinar el endpoint a usar
    const endpoint = deviceUid 
      ? `/api/device/by-uuid/${deviceUid}` 
      : `/api/device/${deviceId}`;
      
    const response = await fetch(`${endpoint}?_t=${timestamp}`, {
      method: "GET",
      headers: {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        Pragma: "no-cache",
        Expires: "0",
      },
    });

    if (!response.ok) {
      throw new Error("Dispositivo no encontrado");
    }

    const device = await response.json();
    console.log("Datos recibidos del servidor:", device);
    displayDevice(device);
  } catch (error) {
    console.error("Error al cargar el dispositivo:", error);
    showError();
  }
}

async function displayDevice(device) {
  // Ocultar loading
  document.getElementById("loading").style.display = "none";

  // Mostrar contenido del dispositivo
  document.getElementById("deviceContent").style.display = "block";

  // Función auxiliar para mostrar datos de forma segura
  function setElementText(
    elementId,
    value,
    defaultValue = "N/A",
    hideIfEmpty = false
  ) {
    const element = document.getElementById(elementId);
    if (element) {
      const hasValue = value !== null && value !== undefined && value !== "";
      if (hasValue) {
        element.textContent = value;
        if (hideIfEmpty) {
          element.closest(".detail-row").style.display = "flex";
        }
      } else {
        element.textContent = defaultValue;
        if (hideIfEmpty) {
          element.closest(".detail-row").style.display = "none";
        }
      }
    }
  }

  // Función auxiliar para mostrar datos numéricos con unidades
  function setElementNumericText(
    elementId,
    value,
    unit = "",
    defaultValue = "N/A",
    hideIfEmpty = false
  ) {
    const element = document.getElementById(elementId);
    if (element) {
      const hasValue = value !== null && value !== undefined && value !== "";
      if (hasValue) {
        element.textContent = `${value} ${unit}`.trim();
        if (hideIfEmpty) {
          element.closest(".detail-row").style.display = "flex";
        }
      } else {
        element.textContent = defaultValue;
        if (hideIfEmpty) {
          element.closest(".detail-row").style.display = "none";
        }
      }
    }
  }

  // Llenar información básica - campos principales
  setElementText(
    "deviceName",
    `${device.marca || ""} ${device.nombre_catalogo || ""}`.trim()
  );
  setElementText(
    "deviceCategory",
    `${device.categoria || ""} - ${device.subcategoria || ""}`
      .replace(" - ", " - ")
      .replace(/^- |^$/, "")
  );
  setElementText("deviceBrand", device.marca);
  setElementText("deviceCommercialModel", device.modelo_comercial);
  setElementText("deviceTechnicalModel", device.modelo_tecnico);
  setElementText("deviceYear", device.ano_lanzamiento);
  setElementText("deviceValidityDate", formatDate(device.fecha_vigencia));

  // Obtener la URL de la marca
  let brandUrl = device.brand_url || null; // Intentar obtenerla directamente del dispositivo
  
  if (!brandUrl && device.marca) {
    try {
      const response = await fetch(`/api/brands/${encodeURIComponent(device.marca)}/info`, {
        credentials: 'include'
      });
      if (response.ok) {
        const brandInfo = await response.json();
        brandUrl = brandInfo.url || null;
      }
    } catch (error) {
      console.error('Error al obtener la URL de la marca:', error);
    }
  }

  // Mostrar la URL de la marca si existe
  const brandUrlRow = document.getElementById("brandUrlRow");
  const deviceBrandUrl = document.getElementById("deviceBrandUrl");
  
  if (brandUrl) {
    deviceBrandUrl.innerHTML = `<a href="${brandUrl}" target="_blank">${brandUrl}</a>`;
    brandUrlRow.style.display = "flex";
  } else {
    brandUrlRow.style.display = "none";
  }

  // Categorización completa
  let fullCategory = "";
  if (device.categoria) {
    fullCategory = device.categoria;
    if (device.subcategoria) {
      fullCategory += ` → ${device.subcategoria}`;
    }
  }
  setElementText("deviceFullCategory", fullCategory);
  setElementText("deviceGroup", device.grupo);

  // Información de contacto y representación (ocultar si están vacíos)
  setElementText("deviceImporter", device.importador_representante, "N/A", true);
  setElementText("deviceAddress", device.domicilio, "N/A", true);
  setElementText("deviceContactEmail", device.correo_contacto, "N/A", true);

	    // Información técnica (llenar campos y mostrar tarjeta si hay datos)
	  const hasTechnicalData = device.tecnologia_modulacion || device.frecuencias || 
	                          device.ganancia_antena || device.pire_dbm || device.pire_mw ||
	                          device.tecnologia_modulacion_doc || device.frecuencias_doc ||
	                          device.ganancia_antena_doc || device.pire_dbm_doc || device.pire_mw_doc;
	  
	  if (hasTechnicalData) {
	    // Campos de la izquierda (device)
	    setElementText("deviceTechnology", device.tecnologia_modulacion, "N/A", false);
	    setElementText("deviceFrequencies", device.frecuencias, "N/A", false);
	    setElementText("deviceAntennaGain", device.ganancia_antena, "N/A", false);
	    setElementNumericText("devicePireDbm", device.pire_dbm, "dBm", "N/A", false);
	    setElementNumericText("devicePireMw", device.pire_mw, "mW", "N/A", false);
	    
	    // Campos de la derecha (device_doc)
	    setElementText("deviceTechnologyDoc", device.tecnologia_modulacion_doc, "N/A", false);
	    setElementText("deviceFrequenciesDoc", device.frecuencias_doc, "N/A", false);
	    setElementText("deviceAntennaGainDoc", device.ganancia_antena_doc, "N/A", false);
	    setElementText("devicePireDbmDoc", device.pire_dbm_doc, "N/A", false);
	    setElementText("devicePireMwDoc", device.pire_mw_doc, "N/A", false);
	    
	    // Mostrar la tarjeta técnica
	    document.getElementById("technicalCard").style.display = "block";
	  }

  // Actualizar icono según categoría
  updateDeviceIcon(device.categoria);

  // Actualizar título de la página
  document.title = `${
    device.marca || ""
  } ${device.nombre_catalogo || "Dispositivo"} - QR Informacion EPR`.trim();

  // Mostrar comentarios si existen
  if (device.comentarios && device.comentarios.trim()) {
    document.getElementById("deviceComments").textContent = device.comentarios;
    document.getElementById("commentsSection").style.display = "block";
  }

  // Actualizar meta tags para SEO
  updateMetaTags(device);

  // Mostrar archivos si existen
  if (device.files && device.files.length > 0) {
    displayFiles(device.files);
    document.getElementById("filesSection").style.display = "block";
  }

  // Mostrar imagen de referencia si existe
  displayDeviceImage(device);

  // Mostrar imagen técnica si existe
  displayTechnicalImage(device);

  // Log para debugging - mostrar todos los datos recibidos
  console.log("Datos del dispositivo cargados:", device);
  console.log("Campos disponibles:", Object.keys(device));
}

async function displayDeviceImage(device) {
  const deviceImage = document.getElementById("deviceImage");
  const noImagePlaceholder = document.getElementById("noImagePlaceholder");

  // Buscar específicamente el archivo con file_type 'imagen_referencia'
  let imageUrl = null;

  if (device.files && device.files.length > 0) {
    const referenceImage = device.files.find(file => file.file_type === 'imagen_referencia');
    if (referenceImage) {
      imageUrl = referenceImage.external_url || (referenceImage.file_path ? `/api/files/${referenceImage.id}` : null);
    }
  }

  if (imageUrl) {
    // Mostrar la imagen
    deviceImage.src = imageUrl;
    deviceImage.style.display = "block";
    noImagePlaceholder.style.display = "none";

    // Manejar error de carga de imagen
    deviceImage.onerror = function () {
      // Si la imagen no se puede cargar, mostrar placeholder
      deviceImage.style.display = "none";
      noImagePlaceholder.style.display = "flex";
    };

    // Cuando la imagen se carga correctamente
    deviceImage.onload = function () {
      deviceImage.style.display = "block";
      noImagePlaceholder.style.display = "none";
    };
  } else {
    // No hay imagen disponible, mostrar placeholder
    deviceImage.style.display = "none";
    noImagePlaceholder.style.display = "flex";
  }
}

async function displayTechnicalImage(device) {
  const technicalImage = document.getElementById("technicalImage");
  const technicalImageContainer = document.getElementById("technicalImageContainer");

  // Buscar específicamente el archivo con file_type 'imagen_tecnica'
  let imageUrl = null;

  if (device.files && device.files.length > 0) {
    const techImageFile = device.files.find(file => file.file_type === 'imagen_tecnica');
    if (techImageFile) {
      imageUrl = techImageFile.external_url || (techImageFile.file_path ? `/api/files/${techImageFile.id}` : null);
    }
  }

  if (imageUrl) {
    technicalImage.src = imageUrl;
    technicalImageContainer.style.display = "block";
    
    technicalImage.onerror = function() {
      technicalImageContainer.style.display = "none";
    };
  } else {
    technicalImageContainer.style.display = "none";
  }
}

async function findDeviceImageInFolder(device) {
  const brandFolder = device.marca ? device.marca.toUpperCase() : "";
  const modelFolder = device.nombre_catalogo || device.modelo_comercial || "";

  if (!brandFolder || !modelFolder) {
    return null;
  }

  // Intentar obtener la lista de archivos en la carpeta del modelo
  try {
    const folderPath = `/static/uploads/brands/${brandFolder}/${modelFolder}/`;

    // Intentar diferentes métodos para encontrar imágenes
    const imageExtensions = ["jpg", "jpeg", "png", "gif", "webp"];
    const commonImageNames = [
      "Telefono",
      "telefono",
      "TELEFONO",
      "imagen",
      "Imagen",
      "IMAGEN",
      "photo",
      "Photo",
      "PHOTO",
      "device",
      "Device",
      "DEVICE",
      "producto",
      "Producto",
      "PRODUCTO",
      modelFolder,
      modelFolder.toLowerCase(),
      modelFolder.toUpperCase(),
    ];

    // Primero intentar con nombres comunes
    for (const imageName of commonImageNames) {
      for (const ext of imageExtensions) {
        const imageUrl = `${folderPath}${imageName}.${ext}`;
        if (await checkImageExists(imageUrl)) {
          return imageUrl;
        }
      }
    }

    // Si no encuentra con nombres comunes, intentar con una petición al servidor
    // para obtener la lista de archivos (esto requeriría un endpoint en el backend)
    const imageUrl = await findFirstImageInDirectory(folderPath);
    if (imageUrl) {
      return imageUrl;
    }
  } catch (error) {
    console.log("Error buscando imagen en carpeta:", error);
  }

  return null;
}

async function checkImageExists(imageUrl) {
  try {
    const response = await fetch(imageUrl, { method: "HEAD" });
    return response.ok;
  } catch (error) {
    return false;
  }
}

async function findFirstImageInDirectory(folderPath) {
  try {
    // Intentar obtener la lista de archivos del directorio
    // Esto requiere un endpoint en el backend que liste los archivos
    const response = await fetch(
      `/api/directory-files?path=${encodeURIComponent(folderPath)}`
    );

    if (response.ok) {
      const files = await response.json();
      const imageExtensions = ["jpg", "jpeg", "png", "gif", "webp"];

      // Buscar el primer archivo de imagen
      const imageFile = files.find((file) => {
        const extension = file.toLowerCase().split(".").pop();
        return imageExtensions.includes(extension);
      });

      if (imageFile) {
        return folderPath + imageFile;
      }
    }
  } catch (error) {
    console.log("No se pudo obtener la lista de archivos del directorio:", error);
  }

  // Si no hay endpoint disponible, intentar con patrones comunes de nombres
  const imageExtensions = ["jpg", "jpeg", "png", "gif"];
  const possibleNames = [
    "1",
    "2",
    "3",
    "img1",
    "img2",
    "image1",
    "image2",
    "front",
    "back",
    "side",
    "main",
    "principal",
  ];

  for (const name of possibleNames) {
    for (const ext of imageExtensions) {
      const imageUrl = `${folderPath}${name}.${ext}`;
      if (await checkImageExists(imageUrl)) {
        return imageUrl;
      }
    }
  }

  return null;
}

function updateDeviceIcon(category) {
  const iconElement = document.getElementById("deviceIcon");
  let iconClass = "fas fa-mobile-alt"; // Default

  switch (category.toLowerCase()) {
    case "computador":
      iconClass = "fas fa-laptop";
      break;
    case "tablet":
      iconClass = "fas fa-tablet-alt";
      break;
    case "teléfono celular":
      iconClass = "fas fa-mobile-alt";
      break;
    case "reloj inteligente":
      iconClass = "fas fa-clock";
      break;
    case "gafas y visores":
      iconClass = "fas fa-glasses";
      break;
    case "audio":
      iconClass = "fas fa-headphones";
      break;
    case "tv & home":
      iconClass = "fas fa-tv";
      break;
    case "accesorios":
      iconClass = "fas fa-plug";
      break;
    default:
      iconClass = "fas fa-microchip";
  }

  iconElement.className = iconClass;
}

function displayFiles(files) {
  const filesList = document.getElementById("filesList");
  filesList.innerHTML = "";

  // 1. Filtrar archivos que son 'IMAGEN_REFERENCIA'
  const Files = files.filter(file => file.file_type !== 'imagen_referencia');

  if (!Files || Files.length === 0) {
    const noFilesMessage = document.createElement("p");
    noFilesMessage.className = "no-files-message";
    noFilesMessage.textContent =
      "No hay archivos adjuntos disponibles para este dispositivo.";
    filesList.appendChild(noFilesMessage);
    return;
  }

  Files.forEach((file, index) => {
    const fileItem = document.createElement("div");
    fileItem.className = "file-item";

    // Icono del archivo según el tipo
    const fileIcon = document.createElement("i");
    fileIcon.className = getFileIcon(file.file_type || file.filename);

    // Información del archivo
    const fileInfo = document.createElement("div");
    fileInfo.className = "file-info";

    const fileMainInfo = document.createElement("div");
    fileMainInfo.className = "file-main-info";

    const fileName = document.createElement("div");
    fileName.className = "file-name";
    
    // Priorizar el nombre real del archivo
    let nameToDisplay = file.file_name || file.filename || file.original_filename;
    
    // Si no hay nombre pero hay una URL externa, intentar extraerlo de la URL
    if (!nameToDisplay && file.external_url) {
        try {
            // Obtener la parte final de la URL después de la última barra
            const urlParts = file.external_url.split('/');
            let lastPart = urlParts.pop() || urlParts.pop(); // Manejar posibles barras finales
            
            // Eliminar parámetros de consulta (?...) o fragmentos (#...)
            if (lastPart) {
                const cleanName = lastPart.split(/[?#]/)[0];
                // Solo usar si parece un nombre de archivo (tiene extensión)
                if (cleanName && cleanName.includes('.')) {
                    nameToDisplay = cleanName;
                }
            }
        } catch (e) {
            console.error("Error al extraer nombre de URL:", e);
        }
    }
    
    // Si no hay nombre pero hay ruta local, extraerlo de la ruta
    if (!nameToDisplay && file.file_path) {
        nameToDisplay = file.file_path.split(/[/\\]/).pop();
    }
    
    // Si sigue sin haber nombre, usar el tipo de archivo o un genérico
    if (!nameToDisplay) {
        nameToDisplay = file.file_type ? formatFileType(file.file_type) : `Archivo ${index + 1}`;
    }
    
    fileName.textContent = nameToDisplay;

    const fileMetaRow = document.createElement("div");
    fileMetaRow.className = "file-meta-row";

    const fileType = document.createElement("span");
    fileType.className = "file-type-badge";
    fileType.textContent = formatFileType(file.file_type);

    // Indicador de Password
    const passwordIndicator = document.createElement("span");
    passwordIndicator.className = "password-badge";
    if (file.requires_password) {
      passwordIndicator.innerHTML = '<i class="fas fa-lock"></i> Protegido';
      passwordIndicator.classList.add("protected");
    } else {
      passwordIndicator.innerHTML = '<i class="fas fa-lock-open"></i> Público';
      passwordIndicator.classList.add("public");
    }

    const fileDetails = document.createElement("div");
    fileDetails.className = "file-extra-details";

    if (file.upload_date || file.created_at) {
      const fileDate = document.createElement("span");
      fileDate.className = "file-date";
      fileDate.innerHTML = `<i class="far fa-calendar-alt"></i> ${formatDate(file.upload_date || file.created_at)}`;
      fileDetails.appendChild(fileDate);
    }

    if (file.file_size && file.file_size > 0) {
      const fileSize = document.createElement("span");
      fileSize.className = "file-size";
      fileSize.innerHTML = `<i class="fas fa-hdd"></i> ${formatFileSize(file.file_size)}`;
      fileDetails.appendChild(fileSize);
    }

    fileMainInfo.appendChild(fileName);
    
    fileMetaRow.appendChild(fileType);
    fileMetaRow.appendChild(passwordIndicator);
    if (fileDetails.children.length > 0) {
        fileMetaRow.appendChild(fileDetails);
    }
    
    fileInfo.appendChild(fileMainInfo);
    fileInfo.appendChild(fileMetaRow);

    // Botones de acción
    const fileActions = document.createElement("div");
    fileActions.className = "file-actions";

    // Botón de descarga/visualización
    if (file.file_path || file.external_url) {
      const downloadBtn = document.createElement("button");
      downloadBtn.className = "file-action-btn download-btn";
      
      if (file.external_url) {
        downloadBtn.innerHTML = '<i class="fas fa-external-link-alt"></i> Abrir Enlace';
        downloadBtn.onclick = () => {
          if (file.requires_password) {
            showPasswordModal(file.id, true, file.external_url);
          } else {
            window.open(file.external_url, '_blank');
          }
        };
      } else {
        downloadBtn.innerHTML = '<i class="fas fa-download"></i> Descargar';
        downloadBtn.onclick = () => {
          if (file.requires_password) {
            showPasswordModal(file.id);
          } else {
            window.open(`/api/download-protected-file/${encodeURIComponent(file.id)}`, '_blank');
          }
        };
      }
      fileActions.appendChild(downloadBtn);
    }

    // MODIFICACIÓN: No mostrar botón de vista previa para imágenes de referencia
    // ya que la imagen se muestra desplegada en la tarjeta de imagen de referencia
    if (
      isPreviewable(file.file_type || file.filename) &&
      !isImageFile(file.file_type || file.filename)
    ) {
      const previewBtn = document.createElement("button");
      previewBtn.className = "file-action-btn preview-btn";
      previewBtn.innerHTML = '<i class="fas fa-eye"></i> Vista previa';
      previewBtn.onclick = () => previewFile(file);
      fileActions.appendChild(previewBtn);
    }

    // Ensamblar el elemento del archivo
    fileItem.appendChild(fileIcon);
    fileItem.appendChild(fileInfo);
    fileItem.appendChild(fileActions);

    filesList.appendChild(fileItem);
  });
}

function getFileIcon(fileIdentifier) {
  const extension = (fileIdentifier.split(".").pop() || "").toLowerCase();
  const mimeType = fileIdentifier.toLowerCase();

  if (mimeType.includes("pdf")) return "fas fa-file-pdf";
  if (mimeType.includes("image") || [".jpg", ".jpeg", ".png", ".gif"].includes(extension)) return "fas fa-file-image";
  if (mimeType.includes("video")) return "fas fa-file-video";
  if (mimeType.includes("audio")) return "fas fa-file-audio";
  if (mimeType.includes("zip") || mimeType.includes("rar")) return "fas fa-file-archive";
  if (mimeType.includes("word")) return "fas fa-file-word";
  if (mimeType.includes("excel")) return "fas fa-file-excel";
  if (mimeType.includes("powerpoint")) return "fas fa-file-powerpoint";
  if (mimeType.includes("text") || extension === "txt") return "fas fa-file-alt";

  return "fas fa-file"; // Icono por defecto
}

function formatFileType(fileType) {
  if (!fileType) return "Desconocido";
  
  const types = {
    'imagen_referencia': 'Imagen de Referencia',
    'test_report': 'Test Report',
    'imagenes_externas': 'Imágenes Externas',
    'imagenes_internas': 'Imágenes Internas',
    'diagrama_bloques': 'Diagrama de Bloques',
    'ganancia_antena': 'Ganancia de Antena',
    'guia_usuario': 'Guía de Usuario',
    'otros_documentos': 'Otros Documentos',
    'imagen_tecnica': 'Imagen Técnica'
  };

  return types[fileType] || fileType.split("/").pop().toUpperCase();
}

function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

function formatDate(dateString) {
  if (!dateString) return "N/A";
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString("es-ES", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  } catch (e) {
    return dateString; // Devolver el string original si no se puede parsear
  }
}

function isPreviewable(fileIdentifier) {
  const mimeType = fileIdentifier.toLowerCase();
  return (
    mimeType.includes("image") ||
    mimeType.includes("pdf") ||
    mimeType.includes("text")
  );
}

function isImageFile(fileIdentifier) {
    const mimeType = fileIdentifier.toLowerCase();
    return mimeType.includes("image");
}

function previewFile(file) {
  // Lógica para la vista previa (modal, etc.)
  alert(`Vista previa para: ${file.filename}`);
}

function showError() {
  document.getElementById("loading").style.display = "none";
  document.getElementById("errorContent").style.display = "block";
}

function updateMetaTags(device) {
    // Actualizar meta título
    const metaTitle = document.querySelector("meta[name=\"title\"]");
    if (metaTitle) {
        metaTitle.content = `${device.marca || ""} ${device.nombre_catalogo || "Dispositivo"}`.trim();
    }

    // Actualizar meta descripción
    const metaDescription = document.querySelector("meta[name=\"description\"]");
    if (metaDescription) {
        metaDescription.content = `Información oficial del dispositivo ${device.marca || ""} ${device.modelo_comercial || ""}`.trim();
    }
}



// ===== MODAL DE CONTRASEÑA PARA DESCARGA SEGURA =====

function showPasswordModal(fileId, isExternal = false, externalUrl = '') {
  // Crear el modal si no existe
  let modal = document.getElementById('passwordModal');
  if (!modal) {
    createPasswordModal();
    modal = document.getElementById('passwordModal');
  }
  
  // Limpiar el campo de contraseña
  const passwordInput = document.getElementById('passwordInput');
  passwordInput.value = '';
  
  // Configurar el botón de descarga para este archivo específico
  const downloadButton = document.getElementById('modalDownloadBtn');
  const modalTitle = modal.querySelector('h3');
  
  if (isExternal) {
    modalTitle.innerHTML = '<i class="fas fa-lock"></i> Enlace Protegido';
    downloadButton.innerHTML = '<i class="fas fa-external-link-alt"></i> Abrir Enlace';
    downloadButton.onclick = () => downloadWithPassword(fileId, true, externalUrl);
  } else {
    modalTitle.innerHTML = '<i class="fas fa-lock"></i> Descarga Protegida';
    downloadButton.innerHTML = '<i class="fas fa-download"></i> Descargar';
    downloadButton.onclick = () => downloadWithPassword(fileId);
  }
  
  // Mostrar el modal
  modal.style.display = 'flex';
  
  // Enfocar el campo de contraseña
  setTimeout(() => passwordInput.focus(), 100);
}

function createPasswordModal() {
  // Crear el HTML del modal
  const modalHTML = `
    <div id="passwordModal" class="password-modal">
      <div class="password-modal-content">
        <div class="password-modal-header">
          <h3><i class="fas fa-lock"></i> Descarga Protegida</h3>
          <button class="password-modal-close" onclick="closePasswordModal()">&times;</button>
        </div>
        <div class="password-modal-body">
          <p>Contenido restringido. Solicitar información a SUBTEL (Password):</p>
          <div class="password-input-container">
            <input type="password" id="passwordInput" placeholder="Contraseña" autocomplete="off">
            <button type="button" class="password-toggle" onclick="togglePasswordVisibility()">
              <i class="fas fa-eye" id="passwordToggleIcon"></i>
            </button>
          </div>
          <div id="passwordError" class="password-error" style="display: none;">
            <i class="fas fa-exclamation-triangle"></i>
            <span>Contenido restringido. solicitar información a SUBTEL.</span>
          </div>
        </div>
        <div class="password-modal-footer">
          <button class="password-modal-btn password-modal-btn-secondary" onclick="closePasswordModal()">
            <i class="fas fa-times"></i> Cancelar
          </button>
          <button id="modalDownloadBtn" class="password-modal-btn password-modal-btn-primary">
            <i class="fas fa-download"></i> Descargar
          </button>
        </div>
      </div>
    </div>
  `;
  
  // Agregar el modal al body
  document.body.insertAdjacentHTML('beforeend', modalHTML);
  
  // Agregar event listener para cerrar con Escape
  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
      closePasswordModal();
    }
  });
  
  // Agregar event listener para enviar con Enter
  document.getElementById('passwordInput').addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
      document.getElementById('modalDownloadBtn').click();
    }
  });
  
  // Cerrar modal al hacer clic fuera de él
  document.getElementById('passwordModal').addEventListener('click', function(event) {
    if (event.target === this) {
      closePasswordModal();
    }
  });
}

function closePasswordModal() {
  const modal = document.getElementById('passwordModal');
  if (modal) {
    modal.style.display = 'none';
    // Limpiar mensajes de error
    const errorDiv = document.getElementById('passwordError');
    if (errorDiv) {
      errorDiv.style.display = 'none';
    }
    // Limpiar el campo de contraseña
    const passwordInput = document.getElementById('passwordInput');
    if (passwordInput) {
      passwordInput.value = '';
    }
  }
}

function togglePasswordVisibility() {
  const passwordInput = document.getElementById('passwordInput');
  const toggleIcon = document.getElementById('passwordToggleIcon');
  
  if (passwordInput.type === 'password') {
    passwordInput.type = 'text';
    toggleIcon.className = 'fas fa-eye-slash';
  } else {
    passwordInput.type = 'password';
    toggleIcon.className = 'fas fa-eye';
  }
}

function downloadWithPassword(fileId, isExternal = false, externalUrl = '') {
  const passwordInput = document.getElementById('passwordInput');
  const password = passwordInput.value.trim();
  const errorDiv = document.getElementById('passwordError');
  const downloadBtn = document.getElementById('modalDownloadBtn');
  
  // Ocultar error previo
  errorDiv.style.display = 'none';
  
  if (!password) {
    showPasswordError('Contenido restringido. Solicitar información a SUBTEL.');
    return;
  }
  
  // Mostrar estado de carga
  const originalText = downloadBtn.innerHTML;
  downloadBtn.innerHTML = isExternal ? '<i class="fas fa-spinner fa-spin"></i> Verificando...' : '<i class="fas fa-spinner fa-spin"></i> Descargando...';
  downloadBtn.disabled = true;
  
  // URL para verificar la contraseña (usamos el endpoint de descarga con HEAD)
  const verifyUrl = `/api/download-protected-file/${encodeURIComponent(fileId)}?password=${encodeURIComponent(password)}`;
  
  // Verificar si la contraseña es correcta usando fetch
  fetch(verifyUrl, { method: 'GET' })
    .then(async response => {
      if (response.ok) {
        // Si la respuesta es exitosa, proceder
        if (isExternal) {
          window.open(externalUrl, '_blank');
        } else {
          window.open(verifyUrl, '_blank');
        }
        closePasswordModal();
      } else if (response.status === 401) {
        // Contraseña incorrecta
        showPasswordError('Contenido restringido.');
      } else {
        // Intentar obtener el mensaje de error del servidor
        try {
          const errorData = await response.json();
          showPasswordError(errorData.description || 'Error al procesar la solicitud.');
        } catch (e) {
          showPasswordError('Error al procesar la solicitud. Por favor, inténtalo de nuevo.');
        }
      }
    })
    .catch(error => {
      console.error('Error al verificar la contraseña:', error);
      // En caso de error de red, mostrar error al usuario en lugar de abrir a ciegas
      showPasswordError('Error de conexión. Por favor, verifica tu internet.');
    })
    .finally(() => {
      // Restaurar el botón
      downloadBtn.innerHTML = originalText;
      downloadBtn.disabled = false;
    });
}

function showPasswordError(message) {
  const errorDiv = document.getElementById('passwordError');
  const errorSpan = errorDiv.querySelector('span');
  errorSpan.textContent = message;
  errorDiv.style.display = 'flex';
  
  // Enfocar el campo de contraseña
  const passwordInput = document.getElementById('passwordInput');
  passwordInput.focus();
  passwordInput.select();
}
