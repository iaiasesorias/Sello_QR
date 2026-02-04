CREATE TABLE user (
	id INTEGER NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (email)
);
CREATE TABLE device (
	id INTEGER NOT NULL, 
	uuid VARCHAR(36) NOT NULL UNIQUE,
	marca VARCHAR(100) NOT NULL, 
	nombre_catalogo VARCHAR(200) NOT NULL, 
	modelo_comercial VARCHAR(100) NOT NULL, 
	modelo_tecnico VARCHAR(100) NOT NULL, 
	ano_lanzamiento INTEGER NOT NULL, 
	comentarios TEXT, 
	fecha_vigencia DATE NOT NULL, 
	categoria VARCHAR(50) NOT NULL, 
	subcategoria VARCHAR(50) NOT NULL, 
	grupo VARCHAR(50) NOT NULL, 
	created_at DATETIME, 
	updated_at DATETIME, fabricante VARCHAR(100), 
	PRIMARY KEY (id)
);
CREATE TABLE device_file (
	id INTEGER NOT NULL, 
	device_id INTEGER NOT NULL, 
	file_name VARCHAR(255) NOT NULL, 
	file_path VARCHAR(500), 
	file_type VARCHAR(50) NOT NULL, 
	visibility VARCHAR(10) NOT NULL, 
	external_url VARCHAR(500), 
	file_size INTEGER, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(device_id) REFERENCES device (id)
);
CREATE TABLE brands (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	url VARCHAR(500), 
	image_path VARCHAR(500), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
