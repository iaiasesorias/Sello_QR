import sqlite3
import os

def migrate_db():
    db_path = 'src/database/app.db'
    if not os.path.exists(db_path):
        print(f"Error: No se encontró la base de datos en {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Iniciando actualizaciones de la base de datos...")

    # --- Migración de la tabla 'device' (Lógica existente) ---
    try:
        # Verificar si ya se renombró o si existe la tabla vieja
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='old_device'")
        if not cursor.fetchone():
            print("Actualizando tabla 'device'...")
            cursor.execute("ALTER TABLE device RENAME TO old_device;")
            
            cursor.execute("""
                CREATE TABLE device (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    marca VARCHAR(100) NOT NULL,
                    nombre_catalogo VARCHAR(200) NOT NULL,
                    modelo_comercial VARCHAR(100) NOT NULL,
                    modelo_tecnico VARCHAR(100) NOT NULL,
                    ano_lanzamiento INTEGER NOT NULL,
                    comentarios TEXT,
                    comentario_subtel TEXT,
                    fecha_vigencia DATE NOT NULL,
                    categoria VARCHAR(50) NOT NULL,
                    subcategoria VARCHAR(50) NOT NULL,
                    grupo VARCHAR(50) NOT NULL,
                    importador_representante VARCHAR(255),
                    domicilio VARCHAR(255),
                    correo_contacto VARCHAR(255),
                    created_at DATETIME,
                    updated_at DATETIME,
                    fabricante VARCHAR(100)
                );
            """)

            cursor.execute("""
                INSERT INTO device (
                    id, marca, nombre_catalogo, modelo_comercial, modelo_tecnico,
                    ano_lanzamiento, comentarios, comentario_subtel, fecha_vigencia,
                    categoria, subcategoria, grupo, created_at, updated_at, fabricante
                )
                SELECT 
                    id, marca, nombre_catalogo, modelo_comercial, modelo_tecnico,
                    ano_lanzamiento, comentarios, comentario_subtel, fecha_vigencia,
                    categoria, subcategoria, grupo, created_at, updated_at, fabricante
                FROM old_device;
            """)
            
            cursor.execute("DROP TABLE old_device;")
            print("Tabla 'device' actualizada correctamente.")
    except sqlite3.Error as e:
        print(f"Aviso en tabla 'device': {e}")

    # --- Migración de la tabla 'device_file' (Nueva lógica) ---
    try:
        print("Verificando columna 'requires_password' en 'device_file'...")
        cursor.execute("PRAGMA table_info(device_file)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'requires_password' not in columns:
            print("Añadiendo columna 'requires_password' a la tabla 'device_file'...")
            cursor.execute("ALTER TABLE device_file ADD COLUMN requires_password BOOLEAN DEFAULT 0;")
            print("Columna 'requires_password' añadida con éxito.")
        else:
            print("La columna 'requires_password' ya existe en la tabla 'device_file'.")
            
    except sqlite3.Error as e:
        print(f"Error al actualizar la tabla 'device_file': {e}")

    conn.commit()
    conn.close()
    print("Proceso de migración finalizado.")

if __name__ == '__main__':
    migrate_db()
