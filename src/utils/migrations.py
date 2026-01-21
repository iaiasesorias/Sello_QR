import sqlite3
import os

def run_migrations(app):
    """
    Ejecuta migraciones automáticas de la base de datos al iniciar la aplicación.
    """
    # Obtener la ruta de la base de datos desde la configuración de Flask
    # La URI suele ser 'sqlite:////ruta/al/archivo.db'
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if 'sqlite:///' in db_uri:
        db_path = db_uri.replace('sqlite:///', '')
    else:
        # Ruta por defecto si no se encuentra en la configuración
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'app.db')

    if not os.path.exists(db_path):
        print(f"[MIGRATION] Base de datos no encontrada en {db_path}. Se creará al iniciar.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # --- Migración: Añadir 'requires_password' a 'device_file' ---
        cursor.execute("PRAGMA table_info(device_file)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'requires_password' not in columns:
            print("[MIGRATION] Añadiendo columna 'requires_password' a 'device_file'...")
            cursor.execute("ALTER TABLE device_file ADD COLUMN requires_password BOOLEAN DEFAULT 0")
            conn.commit()
            print("[MIGRATION] Columna 'requires_password' añadida con éxito.")
        
        # --- Migración: Añadir 'fabricante' a 'device' (si no existe) ---
        cursor.execute("PRAGMA table_info(device)")
        device_columns = [column[1] for column in cursor.fetchall()]
        if 'fabricante' not in device_columns:
            print("[MIGRATION] Añadiendo columna 'fabricante' a 'device'...")
            cursor.execute("ALTER TABLE device ADD COLUMN fabricante VARCHAR(100)")
            conn.commit()
            print("[MIGRATION] Columna 'fabricante' añadida con éxito.")

        conn.close()
    except Exception as e:
        print(f"[MIGRATION] Error durante la migración automática: {e}")
