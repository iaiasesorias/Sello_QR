// Global variables
let currentUser = null;
let devices = [];
let categories = [];
let isEditing = false;
let editingDeviceId = null;

// API Base URL
const API_BASE = '/api';

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
    setupEventListeners();
    animateLoginCard(); // Nueva función para la animación de aparición
});

// Función para la animación de aparición de la tarjeta de login
function animateLoginCard() {
    const loginCard = document.querySelector('.login-card');
    if (loginCard) {
        // Usar setTimeout para asegurar que la clase se añada después de que el DOM esté listo
        setTimeout(() => {
            loginCard.classList.add('visible');
        }, 50);
    }
}

// Setup event listeners
function setupEventListeners() {
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Device form
    const deviceForm = document.getElementById('deviceForm');
    if (deviceForm) {
        deviceForm.addEventListener('submit', handleDeviceSubmit);
    }
}

// Authentication functions
async function checkAuthStatus() {
    try {
        // Verificar si hay parámetros de token QR en la URL
        const urlParams = new URLSearchParams(window.location.search);
        const qrToken = urlParams.get('token');
        const brandName = urlParams.get('brand');
        
        // Si hay token QR, intentar validarlo primero
        if (qrToken && brandName) {
            const qrAuthResult = await validateQRToken(qrToken, brandName);
            if (qrAuthResult.success) {
                // GUARDAR Y LIMPIAR URL
                sessionStorage.setItem('qr_token', qrToken);
                sessionStorage.setItem('selectedBrand', brandName);
                
                // Limpiar la barra de direcciones sin recargar la página
                const newUrl = window.location.pathname;
                window.history.replaceState({}, document.title, newUrl);
                
                // Token QR válido, mostrar dashboard con acceso limitado
                currentUser = qrAuthResult.user;
                showDashboard();
                updateUserInfo();
                return;
            }
            // Si el token QR no es válido, continuar con autenticación normal
        }
        
        const response = await fetch(`${API_BASE}/auth/profile`, {
            credentials: 'include'
        });

        if (response.ok) {
            const user = await response.json();
            currentUser = user;
            
            // Verificar si se debe mostrar el formulario de nuevo dispositivo
            if (urlParams.get('action') === 'new_device') {
                showDeviceForm();
            } else {
                showDashboard();
            }
            updateUserInfo();
        } else {
            showLogin();
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
        showLogin();
    }
}

// Nueva función para validar tokens QR
async function validateQRToken(token, brandName) {
    try {
        const response = await fetch(`${API_BASE}/auth/validate-qr-token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                token: token,
                brand: brandName
            })
        });

        if (response.ok) {
            const result = await response.json();
            return {
                success: true,
                user: {
                    role: 'qr_guest',
                    brand_name: brandName,
                    access_type: 'qr',
                    authenticated: true
                }
            };
        } else {
            const error = await response.json();
            console.warn('Token QR inválido:', error.error);
            return { success: false, error: error.error };
        }
    } catch (error) {
        console.error('Error validating QR token:', error);
        return { success: false, error: 'Error de conexión' };
    }
}

async function handleLogin(e) {
    e.preventDefault();
    
    const loginButton = e.submitter;
    const originalButtonContent = loginButton.innerHTML;
    
    // 1. Mostrar animación de progreso
    loginButton.classList.add('loading');
    loginButton.innerHTML = '<span class="spinner"></span>';

    const formData = new FormData(e.target);
    const loginData = {
        email: formData.get('email'),
        password: formData.get('password')
    };

    // showLoading(true); // Reemplazado por la animación en el botón

    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(loginData)
        });

        const result = await response.json();

        if (response.ok) {
            currentUser = result.user;
            showToast("Inicio de sesión exitoso", "success");
            
            // Verificar si el usuario tiene rol 'public' y debe ser redirigido directamente
            if (result.redirect_to_brand && result.brand) {
                // Guardar la marca en sessionStorage y redirigir al panel
                sessionStorage.setItem('selectedBrand', result.brand);
                window.location.href = `index.html?brand=${encodeURIComponent(result.brand)}`;
            } else {
                // Para usuarios admin y auditor, ir a la selección de marca
                window.location.href = "brand_selection.html";
            }
        } else {
            showToast(result.error || 'Error en el inicio de sesión', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('Error de conexión', 'error');
    } finally {
        // 2. Ocultar animación de progreso y restaurar botón
        loginButton.classList.remove('loading');
        loginButton.innerHTML = originalButtonContent;
        // showLoading(false); // Reemplazado por la animación en el botón
    }
}

async function logout() {
    try {
        await fetch(`${API_BASE}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        
        currentUser = null;
        showLogin();
        showToast('Sesión cerrada exitosamente', 'success');
    } catch (error) {
        console.error('Logout error:', error);
        showToast('Error al cerrar sesión', 'error');
    }
}

// UI Navigation functions
function showLogin() {
    document.getElementById('loginSection').style.display = 'block';
    document.getElementById('dashboardSection').style.display = 'none';
    document.getElementById('deviceFormSection').style.display = 'none';
    document.getElementById('userInfo').style.display = 'none';
    
    // Asegurar que la tarjeta de login se anime al mostrar la sección
    const loginCard = document.querySelector('.login-card');
    if (loginCard) {
        loginCard.classList.remove('visible'); // Resetear para la animación
        setTimeout(() => {
            loginCard.classList.add('visible');
        }, 50);
    }
}

function showDashboard() {
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('dashboardSection').style.display = 'block';
    document.getElementById('deviceFormSection').style.display = 'none';
    document.getElementById('userInfo').style.display = 'flex';
    checkUserPermissions();
    
    // Verificar si hay una marca seleccionada en la URL o sessionStorage
    const urlParams = new URLSearchParams(window.location.search);
    const selectedBrand = urlParams.get('brand') || sessionStorage.getItem('selectedBrand');
    

                document.getElementById("categoryFilter").value = ""; // Asegura que la opción por defecto esté seleccionada
                filterDevices();

    if (selectedBrand) {
        // Mostrar indicador de marca seleccionada
        showBrandIndicator(selectedBrand);
        // Cargar dispositivos filtrados por marca
        loadDevices(selectedBrand).then(() => {
            loadCategories().then(() => {
                document.getElementById("categoryFilter").value = ""; // Asegura que la opción por defecto esté seleccionada
                filterDevices();
            });
        });
    } else {
        // Si no hay marca seleccionada, no cargar dispositivos automáticamente
        // Esto evita que se muestren todos los dispositivos al entrar a index.html directamente
        console.log("No hay marca seleccionada, esperando selección.");
        document.getElementById("devicesGrid").innerHTML = "";
    }
}

function showDeviceForm(deviceId = null) {
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('dashboardSection').style.display = 'none';
    document.getElementById('deviceFormSection').style.display = 'block';
    
    isEditing = !!deviceId;
    editingDeviceId = deviceId;
    
    const formTitle = document.getElementById('formTitle');
    const categorySection = document.getElementById('categorySection');
    
    if (isEditing) {
        formTitle.textContent = 'Editar Dispositivo';
        categorySection.style.display = 'block'; // Permitir editar categorías
        loadDeviceForEdit(deviceId);
    } else {
        formTitle.textContent = 'Nuevo Dispositivo';
        categorySection.style.display = 'block';
        resetDeviceForm();
        // Pre-llenar el campo de marca si hay una marca seleccionada
        const selectedBrand = sessionStorage.getItem("selectedBrand");
        if (selectedBrand) {
            document.getElementById("marca").value = selectedBrand;
        }
        // Cargar categorías para el formulario
        loadCategoriesForNewDevice();
    }
    
    // Los event listeners ya están configurados mediante atributos 'onchange' en el HTML
}

function updateUserInfo() {
    if (currentUser) {
        document.getElementById('userEmail').textContent = currentUser.email;
        document.getElementById('userRole').textContent = currentUser.role;
    }
}

function goToBrandSelection() {
    window.location.href = 'brand_selection.html';
}

// Device management functions
async function loadDevices(brandFilter = '') {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/devices${brandFilter ? `?marca=${encodeURIComponent(brandFilter)}` : ''}`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            devices = Array.isArray(data) ? data : [];
        } else {
            showToast('Error al cargar dispositivos', 'error');
        }
    } catch (error) {
        console.error('Error loading devices:', error);
        showToast('Error de conexión al cargar dispositivos', 'error');
    } finally {
        showLoading(false);
    }
}

function filterDevices() {
    const categoryFilter = document.getElementById("categoryFilter").value;
    const searchFilter = document.getElementById("searchFilter").value.toLowerCase();

    let filteredDevices = [...devices];

    if (categoryFilter === "") {
        // Muestra todos los dispositivos si se selecciona 'Todas las Categorías' (valor vacío)
    } else if (categoryFilter) {
        filteredDevices = filteredDevices.filter(device => device.categoria === categoryFilter);
    }

    if (searchFilter) {
        filteredDevices = filteredDevices.filter(device => 
            device.modelo_tecnico.toLowerCase().includes(searchFilter) ||
            device.modelo_comercial.toLowerCase().includes(searchFilter)
        );
    }

    renderFilteredDevices(filteredDevices);
}

function getDeviceImageHtml(device) {
    // Buscar específicamente el archivo con file_type 'imagen_referencia'
    let imageUrl = null;

    if (device.files && device.files.length > 0) {
        const referenceImage = device.files.find(file => file.file_type === 'imagen_referencia');
        if (referenceImage) {
            imageUrl = referenceImage.external_url || (referenceImage.file_path ? `/api/files/${referenceImage.id}` : null);
        }
    }

    if (imageUrl) {
        return `<img src="${imageUrl}" alt="Imagen de Referencia" class="device-reference-image" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                <div class="no-image-placeholder" style="display: none;">
                    <i class="fas fa-image"></i>
                    <p>No hay imagen</p>
                </div>`;
    } else {
        return `<div class="no-image-placeholder">
                    <i class="fas fa-image"></i>
                    <p>No hay imagen</p>
                </div>`;
    }
}

function renderFilteredDevices(filteredDevices) {
    const grid = document.getElementById("devicesGrid");

    grid.innerHTML = filteredDevices.map(device => `
        <div class="device-card" onclick="${currentUser && (currentUser.role === 'public' || currentUser.role === 'qr_guest') ? `openDeviceUrl('/static/public_device.html?uid=${device.uuid}')` : ''}">
	    <div class="device-header">
	        <class="device-title">${device.nombre_catalogo}
	    </div>
            <div class="device-header">
                <div class="device-subtitle">${device.categoria} - ${device.subcategoria}</div>
	    </div>
            <div class="device-image-container">
                ${getDeviceImageHtml(device)}
            </div>
            <div class="device-actions">
                ${currentUser && (currentUser.role !== 'public' && currentUser.role !== 'qr_guest') ? `
                <button class="btn btn-outline" onclick="openDeviceUrl('/static/public_device.html?uid=${device.uuid}')" title="Ver Página Pública">
                    <i class="fas fa-external-link-alt"></i>
                </button>
                ` : ''}
                ${currentUser && currentUser.role !== 'public' && currentUser.role !== 'qr_guest' ? `
                <button class="btn btn-outline" onclick="showDeviceQR(${device.id})" title="Código QR">
                    <i class="fas fa-qrcode"></i>
                </button>

                <button class="btn btn-outline" onclick="showDeviceForm(${device.id})" title="Editar">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-danger" onclick="deleteDevice(${device.id})" title="Eliminar">
                    <i class="fas fa-trash"></i>
                </button>
                ` : ''}

            </div>
        </div>
    `).join("");
}

async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE}/categories`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            categories = await response.json();
            populateFilters();
        }
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

function populateFilters() {
    const categoryFilter = document.getElementById("categoryFilter");
        categoryFilter.innerHTML = 
        "<option value=\"\">Seleccionar categoría</option>";
    categoryFilter.value = ""; // Asegura que 'Seleccionar categoría' sea la opción por defecto

    categories.forEach((category) => {
        const option = document.createElement("option");
        option.value = category;
        option.textContent = category;
        categoryFilter.appendChild(option);
    });
}

async function loadCategoriesForNewDevice() {
    try {
        const response = await fetch(`${API_BASE}/categories`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const categoriesData = await response.json();
            const categoriaSelect = document.getElementById("categoria");
            
            if (categoriaSelect) {
                // Limpiar opciones existentes
                categoriaSelect.innerHTML = '<option value="">Seleccionar categoría</option>';
                
                // Agregar categorías
                categoriesData.forEach(category => {
                    const option = document.createElement("option");
                    option.value = category;
                    option.textContent = category;
                    categoriaSelect.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Error loading categories for new device:', error);
    }
}

async function loadCategoriesForForm(initialCategories = []) {
    const categoriaSelect = document.getElementById("categoria");
    const subcategoriaSelect = document.getElementById("subcategoria");
    const grupoSelect = document.getElementById("grupo");

    if (!categoriaSelect) return;

    // Populate initial categories dropdown if provided
    if (initialCategories.length > 0 && categoriaSelect.options.length <= 1) { // Only populate if not already populated
        initialCategories.forEach(category => {
            const option = document.createElement("option");
            option.value = category;
            option.textContent = category;
            categoriaSelect.appendChild(option);
        });
    }

    const selectedCategoria = categoriaSelect.value;

    // Reset subcategory and group
    if (subcategoriaSelect) subcategoriaSelect.innerHTML = '<option value="">Seleccionar subcategoría</option>';
    if (grupoSelect) grupoSelect.innerHTML = '<option value="">Seleccionar grupo</option>';

    if (!selectedCategoria) return;

    try {
        const response = await fetch(`${API_BASE}/categories/${encodeURIComponent(selectedCategoria)}/subcategories`, {
            credentials: 'include'
        });

        if (response.ok) {
            const subcategories = await response.json();
            if (subcategoriaSelect) {
                subcategories.forEach(subcategory => {
                    const option = document.createElement('option');
                    option.value = subcategory;
                    option.textContent = subcategory;
                    subcategoriaSelect.appendChild(option);
                });
            }
            return subcategories;
        }
    } catch (error) {
        console.error('Error loading subcategories:', error);
    }
    return [];
}

async function loadGroups() {
    const categoriaElement = document.getElementById('categoria');
    const subcategoriaElement = document.getElementById('subcategoria');
    const grupoSelect = document.getElementById('grupo');
    
    if (!categoriaElement || !subcategoriaElement || !grupoSelect) return;
    
    const categoria = categoriaElement.value;
    const subcategoria = subcategoriaElement.value;
    
    // Reset group
    grupoSelect.innerHTML = '<option value="">Seleccionar grupo</option>';
    
    if (!categoria || !subcategoria) return;
    
    try {
        const response = await fetch(`${API_BASE}/categories/${encodeURIComponent(categoria)}/${encodeURIComponent(subcategoria)}/groups`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const groups = await response.json();
            groups.forEach(group => {
                const option = document.createElement('option');
                option.value = group;
                option.textContent = group;
                grupoSelect.appendChild(option);
            });
            return groups;
        }
    } catch (error) {
        console.error('Error loading groups:', error);
    }
    return [];
}

async function handleDeviceSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const deviceData = {
        marca: formData.get("marca"),
        nombre_catalogo: formData.get('nombre_catalogo'),
        modelo_comercial: formData.get('modelo_comercial'),
        modelo_tecnico: formData.get('modelo_tecnico'),
        ano_lanzamiento: parseInt(formData.get("ano_lanzamiento")),
        comentarios: formData.get("comentarios"),
        fecha_vigencia: formData.get("fecha_vigencia"),
        categoria: formData.get("categoria"),
        subcategoria: formData.get("subcategoria"),
        grupo: formData.get("grupo"),
        importador_representante: formData.get("importador_representante"),
        domicilio: formData.get("domicilio"),
        correo_contacto: formData.get("correo_contacto"),
        tecnologia_modulacion: formData.get("tecnologia_modulacion"),
        frecuencias: formData.get("frecuencias"),
        ganancia_antena: formData.get("ganancia_antena"),
        pire_dbm: (formData.get("pire_dbm") === null || formData.get("pire_dbm") === '') ? 0.0 : parseFloat(formData.get("pire_dbm")),
        pire_mw: (formData.get("pire_mw") === null || formData.get("pire_mw") === '') ? 0.0 : parseFloat(formData.get("pire_mw"))
    };

    // Datos específicos para la tabla device_doc
    const deviceDocData = {
        tecnologia_modulacion_doc: formData.get("tecnologia_modulacion_doc"),
        frecuencias_doc: formData.get("frecuencias_doc"),
        ganancia_antena_doc: formData.get("ganancia_antena_doc"),
        pire_dbm_doc: formData.get("pire_dbm_doc"),
        pire_mw_doc: formData.get("pire_mw_doc")
    };

    // Eliminar los campos _doc del objeto deviceData para evitar enviarlos al endpoint de devices
    // Aunque no están en el snippet anterior, se añaden aquí para robustez si el formulario los incluye.
    delete deviceData.tecnologia_modulacion_doc;
    delete deviceData.frecuencias_doc;
    delete deviceData.ganancia_antena_doc;
    delete deviceData.pire_dbm_doc;
    delete deviceData.pire_mw_doc;

    if (isEditing) {
        // For editing, include category, subcategory, and group if they are present in the form
        deviceData.categoria = formData.get("categoria");
        deviceData.subcategoria = formData.get("subcategoria");
        deviceData.grupo = formData.get("grupo");
    }
    
    showLoading(true);
    
    try {
        const url = isEditing ? `${API_BASE}/devices/${editingDeviceId}` : `${API_BASE}/devices`;
        const method = isEditing ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(deviceData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            const deviceId = isEditing ? editingDeviceId : result.id;
            
            // Guardar o actualizar los datos de device_doc
            await saveDeviceDocData(deviceId, deviceDocData);

            // Upload files if any
            await uploadDeviceFiles(deviceId, formData);
            showToast(isEditing ? 'Dispositivo actualizado exitosamente' : 'Dispositivo creado exitosamente', 'success');
            showDashboard();
        } else {
            showToast(result.error || 'Error al guardar dispositivo', 'error');
        }
    } catch (error) {
        console.error('Error saving device:', error);
        showToast('Error de conexión al guardar dispositivo', 'error');
    } finally {
        showLoading(false);
    }
}

// Nueva función para guardar los datos de device_doc
async function saveDeviceDocData(deviceId, deviceDocData) {
    try {
        const url = `${API_BASE}/device_doc/${deviceId}`;
        const method = 'PUT'; // Asumimos que siempre es una actualización o creación basada en el deviceId

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(deviceDocData)
        });

        if (!response.ok) {
            const result = await response.json();
            console.error('Error al guardar datos de device_doc:', result.error);
            showToast('Advertencia: Error al guardar datos de documentación', 'warning');
        }
    } catch (error) {
        console.error('Error de conexión al guardar datos de device_doc:', error);
        showToast('Advertencia: Error de conexión al guardar datos de documentación', 'warning');
    }
}

async function uploadDeviceFiles(deviceId, formData) {
    const filesContainer = document.getElementById('filesContainer');
    const fileGroups = filesContainer.querySelectorAll('.file-input-group');
    
    for (let i = 0; i < fileGroups.length; i++) {
        const fileType = formData.get(`file_type_${i}`);
        const visibility = formData.get(`visibility_${i}`) || 'public';
        const requiresPassword = formData.get(`requires_password_${i}`) === 'on';
        const file = formData.get(`file_${i}`);
        const externalUrl = formData.get(`external_url_${i}`);
        
        if (!fileType) continue;
        
        if (!file && !externalUrl) {
            console.warn(`No file or URL provided for file type: ${fileType}`);
            continue;
        }
        
        const uploadFormData = new FormData();
        uploadFormData.append('device_id', deviceId);
        uploadFormData.append('file_type', fileType);
        uploadFormData.append('visibility', visibility);
        uploadFormData.append('requires_password', requiresPassword);
        
        if (file && file.size > 0) {
            uploadFormData.append('file', file);
        }
        
        if (externalUrl) {
            uploadFormData.append('external_url', externalUrl);
            
            // Intentar extraer el nombre del archivo de la URL
            let fileNameFromUrl = `Documento ${fileType}`;
            try {
                const urlParts = externalUrl.split('/');
                let lastPart = urlParts.pop() || urlParts.pop();
                if (lastPart) {
                    const cleanName = lastPart.split(/[?#]/)[0];
                    if (cleanName && cleanName.includes('.')) {
                        fileNameFromUrl = cleanName;
                    }
                }
            } catch (e) {
                console.error("Error al extraer nombre de URL:", e);
            }
            
            uploadFormData.append('file_name', fileNameFromUrl);
        }
        
        try {
            const response = await fetch(`${API_BASE}/files/upload-device-files`, {
                method: 'POST',
                credentials: 'include',
                body: uploadFormData
            });
            
            if (!response.ok) {
                const error = await response.json();
                console.error(`Error uploading file ${fileType}:`, error);
                showToast(`Error al subir archivo ${fileType}: ${error.error}`, 'warning');
            }
        } catch (error) {
            console.error(`Error uploading file ${fileType}:`, error);
            showToast(`Error al subir archivo ${fileType}`, 'warning');
        }
    }
}

async function loadDeviceForEdit(deviceId) {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/devices/${deviceId}`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const device = await response.json();
            populateDeviceForm(device);
        } else {
            showToast('Error al cargar dispositivo', 'error');
            showDashboard();
        }
    } catch (error) {
        console.error('Error loading device for edit:', error);
        showToast('Error de conexión', 'error');
        showDashboard();
    } finally {
        showLoading(false);
    }
}

function populateDeviceForm(device) {
    // Set the hidden deviceId field
    const deviceIdField = document.getElementById('deviceId');
    if (deviceIdField) {
        deviceIdField.value = device.id;
    }
    
    // Populate form fields
    const marcaField = document.getElementById('marca');
    if (marcaField) marcaField.value = device.marca || '';
    
    const fabricanteField = document.getElementById('fabricante');
    if (fabricanteField) fabricanteField.value = device.fabricante || '';
    
    const nombreCatalogoField = document.getElementById('nombre_catalogo');
    if (nombreCatalogoField) nombreCatalogoField.value = device.nombre_catalogo || '';
    
    const modeloComercialField = document.getElementById('modelo_comercial');
    if (modeloComercialField) modeloComercialField.value = device.modelo_comercial || '';
    
    const modeloTecnicoField = document.getElementById('modelo_tecnico');
    if (modeloTecnicoField) modeloTecnicoField.value = device.modelo_tecnico || '';
    
    const anoLanzamientoField = document.getElementById('ano_lanzamiento');
    if (anoLanzamientoField) anoLanzamientoField.value = device.ano_lanzamiento || '';
    
    const fechaVigenciaField = document.getElementById('fecha_vigencia');
    if (fechaVigenciaField) fechaVigenciaField.value = device.fecha_vigencia || '';
    
    // Populate category fields
    const categoriaField = document.getElementById('categoria');
    if (categoriaField) categoriaField.value = device.categoria || '';
    
    const subcategoriaField = document.getElementById('subcategoria');
    if (subcategoriaField) subcategoriaField.value = device.subcategoria || '';
    
    const grupoField = document.getElementById('grupo');
    if (grupoField) grupoField.value = device.grupo || '';
    
    // Load categories for editing
    loadCategoriesForNewDevice().then(async () => {
        // Set the category value after loading
        if (categoriaField && device.categoria) {
            categoriaField.value = device.categoria;
            // Trigger loadCategoriesForForm manually to return a promise
            await loadCategoriesForForm();
            
            if (subcategoriaField && device.subcategoria) {
                subcategoriaField.value = device.subcategoria;
                // Trigger loadGroups manually to return a promise
                await loadGroups();
                
                if (grupoField && device.grupo) {
                    grupoField.value = device.grupo;
                }
            }
        }
    });
    
    const comentariosField = document.getElementById('comentarios');
    if (comentariosField) comentariosField.value = device.comentarios || '';
    


    const importadorRepresentanteField = document.getElementById('importador_representante');
    if (importadorRepresentanteField) importadorRepresentanteField.value = device.importador_representante || '';

    const domicilioField = document.getElementById('domicilio');
    if (domicilioField) domicilioField.value = device.domicilio || '';

    const correoContactoField = document.getElementById('correo_contacto');
    if (correoContactoField) correoContactoField.value = device.correo_contacto || '';

    const tecnologiaModulacionField = document.getElementById('tecnologia_modulacion');
    if (tecnologiaModulacionField) tecnologiaModulacionField.value = device.tecnologia_modulacion || '';

    const frecuenciasField = document.getElementById('frecuencias');
    if (frecuenciasField) frecuenciasField.value = device.frecuencias || '';

    const gananciaAntenaField = document.getElementById('ganancia_antena');
    if (gananciaAntenaField) gananciaAntenaField.value = device.ganancia_antena || '';

        const pireDbmField = document.getElementById('pire_dbm');
    if (pireDbmField) pireDbmField.value = device.pire_dbm === null ? 0.0 : device.pire_dbm;

        const pireMwField = document.getElementById('pire_mw');
    if (pireMwField) pireMwField.value = device.pire_mw === null ? 0.0 : device.pire_mw;
    
    // Load files if any
    renderExistingFiles(device.files);
}

function renderExistingFiles(files) {
    const filesContainer = document.getElementById('filesContainer');
    filesContainer.innerHTML = files.map(file => {
        // Lógica para determinar el nombre a mostrar
        let nameToDisplay = file.file_name || file.filename;
        
        if (!nameToDisplay && file.external_url) {
            try {
                const urlParts = file.external_url.split('/');
                let lastPart = urlParts.pop() || urlParts.pop();
                if (lastPart) {
                    const cleanName = lastPart.split(/[?#]/)[0];
                    if (cleanName && cleanName.includes('.')) {
                        nameToDisplay = cleanName;
                    }
                }
            } catch (e) {
                console.error("Error al extraer nombre de URL:", e);
            }
        }
        
        if (!nameToDisplay) {
            nameToDisplay = file.file_type ? file.file_type.replace('_', ' ').toUpperCase() : 'Archivo';
        }

        return `
        <div class="file-input-group">
            <div class="file-input-header">
                <span class="file-input-title">${nameToDisplay}</span>
                <button type="button" class="btn btn-danger" onclick="deleteFile(${file.id})" title="Eliminar Archivo">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            <div class="file-input-grid">
                <div class="form-group">
                    <label>Tipo:</label>
                    <span>${file.file_type.replace('_', ' ')}</span>
                </div>
                <div class="form-group">
                    <label>Visibilidad:</label>
                    <span>${file.visibility === 'public' ? 'Público' : 'Privado'}</span>
                </div>
                <div class="form-group">
                    <label>Password:</label>
                    <span class="badge ${file.requires_password ? 'badge-warning' : 'badge-info'}">
                        <i class="fas ${file.requires_password ? 'fa-lock' : 'fa-lock-open'}"></i>
                        ${file.requires_password ? 'Habilitado' : 'No habilitado'}
                    </span>
                </div>
                ${file.external_url ? `
                    <div class="form-group">
                        <label>URL Externa:</label>
                        <a href="${file.external_url}" target="_blank">${file.external_url}</a>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    }).join('');
}

async function deleteDevice(deviceId) {
    if (!confirm('¿Estás seguro de que deseas eliminar este dispositivo?')) {
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/devices/${deviceId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (response.ok) {
            showToast('Dispositivo eliminado exitosamente', 'success');
            const responseData = await response.json();
            const marcaFiltrada = responseData.marca || sessionStorage.getItem('selectedBrand');
            await loadDevices(marcaFiltrada);
            filterDevices();
        } else {
            showToast('Error al eliminar dispositivo', 'error');
        }
    } catch (error) {
        console.error('Error deleting device:', error);
        showToast('Error de conexión al eliminar dispositivo', 'error');
    } finally {
        showLoading(false);
    }
}

async function deleteFile(fileId) {
    if (!confirm('¿Estás seguro de que deseas eliminar este archivo?')) {
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/files/${fileId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (response.ok) {
            showToast('Archivo eliminado exitosamente', 'success');
            // Reload device for edit to refresh files
            // Se añade una pequeña espera para asegurar que la base de datos se haya actualizado antes de recargar.
if (isEditing && editingDeviceId) {
	                // Esperar un breve momento para asegurar la consistencia del backend antes de recargar.
	                setTimeout(() => {
	                    loadDeviceForEdit(editingDeviceId);
	                }, 200);
	            }
        } else {
            showToast('Error al eliminar archivo', 'error');
        }
    } catch (error) {
        console.error('Error deleting file:', error);
        showToast('Error de conexión al eliminar archivo', 'error');
    } finally {
        showLoading(false);
    }
}

function resetDeviceForm() {
    document.getElementById('deviceForm').reset();
    document.getElementById('filesContainer').innerHTML = '';
}

function addFileInput() {
    const filesContainer = document.getElementById('filesContainer');
    const fileIndex = filesContainer.children.length;
    
    const fileInputHTML = `
        <div class="file-input-group" data-index="${fileIndex}">
            <div class="file-input-row">
                <div class="form-group">
                    <label>Tipo de Archivo *</label>
                    <select name="file_type_${fileIndex}" required>
                        <option value="">Seleccionar tipo</option>
                        <option value="imagen_referencia">Imagen de Referencia</option>
                        <option value="imagen_tecnica">Imagen Técnica</option>
                        <option value="test_report">Test Report</option>
                        <option value="imagenes_externas">Imágenes Externas</option>
                        <option value="imagenes_internas">Imágenes Internas</option>
                        <option value="diagrama_bloques">Diagrama de Bloques</option>
                        <option value="ganancia_antena">Ganancia de Antena</option>
                        <option value="guia_usuario">Guía de Usuario</option>
                        <option value="otros_documentos">Otros Documentos</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Visibilidad</label>
                    <select name="visibility_${fileIndex}">
                        <option value="public">Público</option>
                        <option value="private">Privado</option>
                    </select>
                </div>
                <div class="form-group" style="display: flex; align-items: center; gap: 10px; padding-top: 25px;">
                    <input type="checkbox" name="requires_password_${fileIndex}" id="requires_password_${fileIndex}" style="width: 20px; height: 20px;">
                    <label for="requires_password_${fileIndex}" style="margin-bottom: 0;">Ticket Habilitación (Password)</label>
                </div>
                <button type="button" class="btn btn-danger btn-sm" onclick="removeFileInput(${fileIndex})">
                    <i class="fas fa-trash"></i> Eliminar
                </button>
            </div>
            <div class="file-input-row">
                <div class="form-group">
                    <label>Archivo (PDF/ZIP/Imágenes, máx 15MB)</label>
                    <input type="file" name="file_${fileIndex}" accept=".pdf,.zip,.jpg,.jpeg,.png,.gif,.webp,.bmp">
                </div>
                <div class="form-group">
                    <label>O URL Externa</label>
                    <input type="url" name="external_url_${fileIndex}" placeholder="https://ejemplo.com/documento.pdf">
                </div>
            </div>
        </div>
    `;
    
    filesContainer.insertAdjacentHTML('beforeend', fileInputHTML);
}

function removeFileInput(index) {
    const fileGroup = document.querySelector(`[data-index="${index}"]`);
    if (fileGroup) {
        fileGroup.remove();
    }
}

// Filter functions
function filterDevices() {
    const categoryFilter = document.getElementById('categoryFilter').value;
    const searchFilter = document.getElementById('searchFilter').value.toLowerCase();
    
    let filteredDevices = [...devices];
    
    if (categoryFilter === "") {
        // Muestra todos los dispositivos si se selecciona 'Todas las Categorías' (valor vacío)
    } else if (categoryFilter) {
        filteredDevices = filteredDevices.filter(device => device.categoria === categoryFilter);
    }
    
    if (searchFilter) {
        filteredDevices = filteredDevices.filter(device => 
            device.modelo_tecnico.toLowerCase().includes(searchFilter) ||
            device.modelo_comercial.toLowerCase().includes(searchFilter)
        );
    }
    
    renderFilteredDevices(filteredDevices);
}

// Utility functions
function showLoading(show) {
    document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'check-circle' : 
                 type === 'error' ? 'exclamation-circle' : 
                 'exclamation-triangle';
    
    toast.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Remove toast after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES');
}


// Funciones para códigos QR
async function showDeviceQR(deviceId) {
    try {
        showLoading(true);
        
        const response = await fetch(`${API_BASE}/devices/${deviceId}/qr`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Error al obtener el código QR');
        }
        
        const data = await response.json();
        
        // Crear modal para mostrar el QR
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal qr-modal">
                <div class="modal-header">
                    <h3>Código QR del Dispositivo</h3>
                    <button class="modal-close" onclick="closeModal(this)">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="qr-container">
                        <div class="device-qr-info">
                            <h4>${data.device.marca} ${data.device.nombre_catalogo}</h4>
                        </div>
                        <div class="qr-code-container">
                            <img src="${data.qr_code}" alt="Código QR" class="qr-code-image">
                        </div>
                        <div class="qr-url-info">
                            <p><strong>URL del dispositivo:</strong></p>
                            <div class="url-container">
                                <input type="text" value="${data.device_url}" readonly class="url-input" id="deviceUrl${deviceId}">
                                <button class="btn btn-outline btn-sm" onclick="copyToClipboard('deviceUrl${deviceId}')">
                                    <i class="fas fa-copy"></i> Copiar
                                </button>
                            </div>
                        </div>
                        <div class="qr-actions">
                            <button class="btn btn-primary" onclick="downloadQR('${data.qr_code}', '${data.device.marca}_${data.device.modelo_comercial}_QR')">
                                <i class="fas fa-download"></i> Descargar QR
                            </button>                            <button class="btn btn-outline" onclick="openDeviceUrl(\'/static/public_device.html?uid=${data.device.uuid}\')">                                <i class="fas fa-external-link-alt"></i> Ver Página Pública
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al cargar el código QR', 'error');
    } finally {
        showLoading(false);
    }
}

function closeModal(button) {
    const modal = button.closest('.modal-overlay');
    if (modal) {
        modal.remove();
    }
}

function copyToClipboard(inputId) {
    const input = document.getElementById(inputId);
    input.select();
    input.setSelectionRange(0, 99999); // Para móviles
    
    try {
        document.execCommand('copy');
        showToast('URL copiada al portapapeles', 'success');
    } catch (err) {
        console.error('Error al copiar:', err);
        showToast('Error al copiar la URL', 'error');
    }
}

function downloadQR(qrDataUrl, filename) {
    const link = document.createElement('a');
    link.download = `${filename}.png`;
    link.href = qrDataUrl;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('Código QR descargado', 'success');
}

function openDeviceUrl(url) {
    window.open(url, '_blank');
}


// Function to show manufacturer QR
async function showManufacturerQR(deviceId) {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/devices/${deviceId}/manufacturer-qr`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const qrData = await response.json();
            
            // Create modal for QR display
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.innerHTML = `
                <div class="modal-content qr-modal">
                    <div class="modal-header">
                        <h2><i class="fas fa-industry"></i> Código QR del Fabricante</h2>
                        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="qr-info">
                            <h3>${qrData.manufacturer}</h3>
                            <p>Dispositivo: ${qrData.device_info.marca} ${qrData.device_info.nombre_catalogo}</p>
                            <p>URL: <a href="${qrData.manufacturer_url}" target="_blank">${qrData.manufacturer_url}</a></p>
                        </div>
                        <div class="qr-code-container">
                            <img src="${qrData.qr_code}" alt="Código QR del Fabricante" class="qr-code-image">
                        </div>
                        <div class="qr-actions">
                            <button class="btn btn-primary" onclick="downloadQRImage('${qrData.qr_code}', 'qr_fabricante_${qrData.manufacturer.replace(/[^a-zA-Z0-9]/g, '_')}.png')">
                                <i class="fas fa-download"></i>
                                Descargar QR
                            </button>
                            <button class="btn btn-outline" onclick="window.open('${qrData.manufacturer_url}', '_blank')">
                                <i class="fas fa-external-link-alt"></i>
                                Ver Página
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Close modal when clicking outside
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    modal.remove();
                }
            });
            
        } else {
            const error = await response.json();
            showToast(error.error || 'Error al generar código QR del fabricante', 'error');
        }
    } catch (error) {
        console.error('Error showing manufacturer QR:', error);
        showToast('Error de conexión al generar código QR', 'error');
    } finally {
        showLoading(false);
    }
}


// Función para mostrar indicador de marca seleccionada
function showBrandIndicator(brandName) {
    // Crear o actualizar el indicador de marca
    let brandIndicator = document.getElementById('brandIndicator');
    
    if (!brandIndicator) {
        brandIndicator = document.createElement('div');
        brandIndicator.id = 'brandIndicator';
        brandIndicator.className = 'brand-indicator';
        
        // Insertar después del header del dashboard
        const dashboardHeader = document.querySelector('.dashboard-header');
        if (dashboardHeader) {
            dashboardHeader.insertAdjacentElement('afterend', brandIndicator);
        }
    }
    
    brandIndicator.innerHTML = `
        <div class="brand-indicator-content">
            <div class="brand-info">
                <i class="fas fa-tag"></i>
                <span class="brand-label">Marca:</span>
                <span class="brand-name">${brandName}</span>
            </div>
            <div class="brand-actions">
                <button class="btn btn-outline btn-sm" onclick="goToBrandSelection()" id="changeBrandButton">
                    <i class="fas fa-exchange-alt"></i>
                    Cambiar Marca
                </button>
            </div>
        </div>
    `;
    
    // Mostrar imagen de la marca en el panel de administración
    checkUserPermissions();
    const brandImageContainer = document.getElementById('brandImageContainer');
    const brandImage = document.getElementById('brandImage');
    
    if (brandImageContainer && brandImage) {
        const brandImageUrl = `/api/brands/${encodeURIComponent(brandName)}/image`;
        brandImage.src = brandImageUrl;
        brandImage.onerror = function() {
            brandImageContainer.style.display = 'none';
        };
        brandImage.onload = function() {
            brandImageContainer.style.display = 'block';
        };
    }
    
    // Agregar estilos si no existen
    if (!document.getElementById("brandIndicatorStyles")) {
        const styles = document.createElement('style');
        styles.id = 'brandIndicatorStyles';
        styles.textContent = `
            .brand-indicator {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1rem 2rem;
                margin: 1rem 0;
                border-radius: 10px;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            
            .brand-indicator-content {
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 1rem;
            }
            
            .brand-info {
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .brand-label {
                font-weight: 500;
                opacity: 0.9;
            }
            
            .brand-name {
                font-weight: bold;
                font-size: 1.1rem;
                background: rgba(255,255,255,0.2);
                padding: 0.3rem 0.8rem;
                border-radius: 15px;
            }
            
            .brand-actions {
                display: flex;
                gap: 0.5rem;
            }
            
            .brand-indicator .btn {
                background: rgba(255,255,255,0.2);
                border-color: rgba(255,255,255,0.3);
                color: white;
                font-size: 0.9rem;
                padding: 0.5rem 1rem;
            }
            
            .brand-indicator .btn:hover {
                background: rgba(255,255,255,0.3);
                border-color: rgba(255,255,255,0.5);
                transform: translateY(-1px);
            }
            
            @media (max-width: 768px) {
                .brand-indicator-content {
                    flex-direction: column;
                    text-align: center;
                }
                
                .brand-actions {
                    justify-content: center;
                }
            }
        `;
        document.head.appendChild(styles);
    }
    checkUserPermissions();
}

// Función para ir a la página de selección de marca
function goToBrandSelection() {
    window.location.href = '/brand_selection.html';
}

// Función para limpiar el filtro de marca
function clearBrandFilter() {
    // Limpiar sessionStorage
    sessionStorage.removeItem('selectedBrand');
    
    // Remover parámetro de la URL
    const url = new URL(window.location);
    url.searchParams.delete('brand');
    window.history.replaceState({}, '', url);
    
    // Ocultar indicador de marca
    const brandIndicator = document.getElementById('brandIndicator');
    if (brandIndicator) {
        brandIndicator.remove();
    }
    
    // Recargar dispositivos sin filtro
    loadDevices().then(() => {
        // Limpiar filtro de marca en el select
        const brandFilter = document.getElementById('brandFilter');
        if (brandFilter) {
            brandFilter.value = '';
        }
        filterDevices();
    });
}

// Función para verificar autenticación antes de mostrar selección de marca
async function checkAuthForBrandSelection() {
    try {
        const response = await fetch(`${API_BASE}/auth/profile`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            // Si no está autenticado, redirigir al login
            window.location.href = '/';
            return false;
        }
        
        return true;
    } catch (error) {
        console.error('Error al verificar autenticación:', error);
        window.location.href = '/';
        return false;
    }
}



function checkUserPermissions() {
    const newDeviceButtonContainer = document.getElementById('newDeviceButtonContainer');
    const changeBrandButton = document.getElementById("changeBrandButton");

    // Usuarios con acceso limitado: 'public' y 'qr_guest'
    if (currentUser && (currentUser.role === 'public' || currentUser.role === 'qr_guest')) {
        if (newDeviceButtonContainer) {
            newDeviceButtonContainer.style.display = 'none';
        }
        if (changeBrandButton) {
            changeBrandButton.style.display = 'none';
        }
        
        // Para usuarios QR, mostrar mensaje informativo
        if (currentUser.role === 'qr_guest') {
            showQRAccessNotification();
        }
    } else {
        if (newDeviceButtonContainer) {
            newDeviceButtonContainer.style.display = 'block';
        }
        if (changeBrandButton) {
            changeBrandButton.style.display = 'block'; // O el display original que tuviera
        }
    }
}

// Nueva función para mostrar notificación de acceso QR
function showQRAccessNotification() {
    // Crear notificación temporal si no existe
    if (!document.getElementById('qrAccessNotification')) {
        const notification = document.createElement('div');
        notification.id = 'qrAccessNotification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            z-index: 1000;
            font-size: 14px;
            max-width: 300px;
            animation: slideIn 0.3s ease-out;
        `;
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-qrcode" style="font-size: 18px;"></i>
                <div>
                    <strong>Acceso por QR</strong><br>
                    <small>Vista de solo lectura para ${currentUser.brand_name}</small>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="background: none; border: none; color: white; font-size: 16px; cursor: pointer; margin-left: auto;">
                    ×
                </button>
            </div>
        `;
        
        // Agregar animación CSS si no existe
        if (!document.getElementById('qrNotificationStyles')) {
            const styles = document.createElement('style');
            styles.id = 'qrNotificationStyles';
            styles.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(styles);
        }
        
        document.body.appendChild(notification);
        
        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
}

