import streamlit as st
import pandas as pd
import os
import json

# Directorio para guardar archivos de equipos
EQUIPOS_DATA_DIR = "data_equipos"

def crear_directorio_datos():
    """Crear directorio para datos de equipos si no existe"""
    if not os.path.exists(EQUIPOS_DATA_DIR):
        os.makedirs(EQUIPOS_DATA_DIR)

def guardar_archivo_equipo(equipo_id, uploaded_file, timestamp):
    """Guardar archivo original para un equipo"""
    crear_directorio_datos()
    
    # Crear subdirectorio para el equipo si no existe
    equipo_dir = os.path.join(EQUIPOS_DATA_DIR, equipo_id)
    if not os.path.exists(equipo_dir):
        os.makedirs(equipo_dir)
    
    # Generar nombre de archivo único
    saved_filename = f"{timestamp}_{uploaded_file.name}"
    file_path = os.path.join(equipo_dir, saved_filename)
    
    # Guardar archivo original
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Registrar metadatos del archivo
    archivo_info = {
        "nombre_original": uploaded_file.name,
        "nombre_guardado": saved_filename,
        "ruta_archivo": file_path,
        "fecha_subida": timestamp
    }
    
    # Guardar metadatos en JSON
    metadatos_path = os.path.join(equipo_dir, "archivos_metadata.json")
    
    # Cargar metadatos existentes
    if os.path.exists(metadatos_path):
        with open(metadatos_path, 'r') as f:
            metadatos = json.load(f)
    else:
        metadatos = []
    
    # Añadir nuevo archivo a metadatos
    metadatos.append(archivo_info)
    
    # Guardar metadatos actualizados
    with open(metadatos_path, 'w') as f:
        json.dump(metadatos, f, indent=4)
    
    return archivo_info

def eliminar_archivo_equipo(equipo_id, indice_archivo):
    """Eliminar un archivo de un equipo y actualizar sus metadatos"""
    metadatos_path = os.path.join(EQUIPOS_DATA_DIR, equipo_id, "archivos_metadata.json")
    
    # Verificar que existe el archivo de metadatos
    if not os.path.exists(metadatos_path):
        return False, "No se encontraron archivos para este equipo."
    
    # Cargar los metadatos
    with open(metadatos_path, 'r') as f:
        metadatos = json.load(f)
    
    # Verificar que el índice es válido
    if indice_archivo < 0 or indice_archivo >= len(metadatos):
        return False, "Índice de archivo no válido."
    
    # Obtener información del archivo a eliminar
    archivo_a_eliminar = metadatos[indice_archivo]
    ruta_archivo = archivo_a_eliminar['ruta_archivo']
    
    # Eliminar el archivo físico
    try:
        if os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)
        
        # Eliminar el registro de metadatos
        metadatos.pop(indice_archivo)
        
        # Guardar metadatos actualizados
        with open(metadatos_path, 'w') as f:
            json.dump(metadatos, f, indent=4)
        
        return True, f"Archivo '{archivo_a_eliminar['nombre_original']}' eliminado correctamente."
    
    except Exception as e:
        return False, f"Error al eliminar el archivo: {e}"

def cargar_archivos_equipo(equipo_id):
    """Cargar metadatos de archivos de un equipo"""
    metadatos_path = os.path.join(EQUIPOS_DATA_DIR, equipo_id, "archivos_metadata.json")
    
    if os.path.exists(metadatos_path):
        with open(metadatos_path, 'r') as f:
            return json.load(f)
    return []

def subir_archivo():
    # Verificar autenticación
    if "equipo_id" not in st.session_state or st.session_state["role"] == "admin":
        st.warning("Esta función solo está disponible para equipos específicos.")
        return None

    # Obtener detalles del equipo
    equipo_id = st.session_state["equipo_id"]
    nombre_equipo = st.session_state["nombre_equipo"]

    st.subheader(f"📂 Subida de Archivos - {nombre_equipo}")

    # Widget para subir archivo
    uploaded_file = st.file_uploader("📤 Cargar archivo Excel", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        # Generar timestamp
        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        try:
            # Guardar archivo original
            archivo_info = guardar_archivo_equipo(equipo_id, uploaded_file, timestamp)
            
            # Leer y mostrar vista previa
            df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ Archivo '{uploaded_file.name}' guardado para {nombre_equipo}")
            
            # Vista previa
            st.write("Vista previa de los datos:")
            st.dataframe(df.head())
            
            return df
        
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
            return None
    
    # Cargar y mostrar archivos del equipo
    archivos_equipo = cargar_archivos_equipo(equipo_id)
    
    if archivos_equipo:
        st.subheader(f"📁 Archivos de {nombre_equipo}")
        
        # Selector de archivos
        opciones = [
            f"{archivo['fecha_subida']} - {archivo['nombre_original']}" 
            for archivo in archivos_equipo
        ]
        
        archivo_seleccionado = st.selectbox(
            "Selecciona un archivo para ver detalles:", 
            opciones
        )
        
        # Encontrar el archivo seleccionado
        indice = opciones.index(archivo_seleccionado)
        archivo_actual = archivos_equipo[indice]
        
        # Mostrar detalles
        st.write("Detalles del archivo:")
        st.json(archivo_actual)
        
        # Leer y mostrar vista previa del archivo
        try:
            df = pd.read_excel(archivo_actual['ruta_archivo'])
            
            st.write("Vista previa:")
            st.dataframe(df.head())
            
            col1, col2 = st.columns(2)
            
            # Botón para descargar
            with col1:
                with open(archivo_actual['ruta_archivo'], 'rb') as f:
                    st.download_button(
                        label="Descargar archivo original",
                        data=f.read(),
                        file_name=archivo_actual['nombre_original'],
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
            
            # Botón para eliminar
            with col2:
                if st.button("🗑️ Eliminar archivo", key=f"delete_{indice}"):
                    confirmacion = st.checkbox("¿Estás seguro? Esta acción no se puede deshacer.", key=f"confirm_{indice}")
                    if confirmacion:
                        exito, mensaje = eliminar_archivo_equipo(equipo_id, indice)
                        if exito:
                            st.success(mensaje)
                            st.experimental_rerun()  # Recargar la página para reflejar los cambios
                        else:
                            st.error(mensaje)
        
        except Exception as e:
            st.error(f"No se pudo leer el archivo: {e}")
    
    else:
        st.info("Aún no has subido ningún archivo.")
    
    return None