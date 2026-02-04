import sqlite3
import uuid
import os

db_path = os.path.join('src', 'database', 'app.db')

def migrate():
    if not os.path.exists(db_path):
        print(f"Error: No se encontró la base de datos en {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Añadir la columna uuid si no existe
        print("Añadiendo columna 'uuid' a la tabla 'device'...")
        try:
            cursor.execute("ALTER TABLE device ADD COLUMN uuid VARCHAR(36)")
            conn.commit()
            print("Columna 'uuid' añadida exitosamente.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("La columna 'uuid' ya existe.")
            else:
                raise e

        # 2. Generar UUIDs para los registros existentes que no tengan uno
        cursor.execute("SELECT id FROM device WHERE uuid IS NULL")
        devices = cursor.fetchall()
        
        if devices:
            print(f"Generando UUIDs para {len(devices)} dispositivos...")
            for (device_id,) in devices:
                new_uuid = str(uuid.uuid4())
                cursor.execute("UPDATE device SET uuid = ? WHERE id = ?", (new_uuid, device_id))
            conn.commit()
            print("UUIDs generados exitosamente.")
        else:
            print("No hay dispositivos sin UUID.")

        # 3. (Opcional) Hacer la columna UNIQUE y NOT NULL
        # En SQLite, para cambiar una columna a NOT NULL UNIQUE después de crearla, 
        # a menudo es necesario recrear la tabla, pero para este caso de uso, 
        # asegurar que todos tengan valor es suficiente por ahora.
        
        print("Migración completada con éxito.")

    except Exception as e:
        print(f"Error durante la migración: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
