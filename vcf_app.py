import streamlit as st
import pandas as pd
import numpy as np
import os
import uuid
import glob
from datetime import datetime
import modules.graficos as graficos
from modules.auth import login
from modules.plantilla import plantilla_page
from modules.equipos import mostrar_navegador_equipos, mostrar_panel_equipo
from modules.individuales import pagina_registros_individuales
from modules.total import pagina_datos_totales
from modules.pdf_export import download_session_charts

# Configuración de la página
st.set_page_config(
    page_title="Academia Valencia CF",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Directorios para archivos
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Directorios para equipos (uno por equipo)
def crear_directorios_equipos():
    """Crea directorios para cada equipo si no existen"""
    equipos = ["Valencia Mestalla", "Juvenil A", "Juvenil B", "Cadete A", "Cadete B", "Infantil A", "Infantil B"]
    for equipo in equipos:
        equipo_dir = os.path.join(UPLOAD_DIR, equipo.lower().replace(" ", "_"))
        os.makedirs(equipo_dir, exist_ok=True)

# Crear directorios al iniciar
crear_directorios_equipos()

# Función para escanear archivos en el directorio
def escanear_archivos():
    """Escanea los directorios de equipos y reconstruye la lista de archivos"""
    archivos = []
    
    # Obtener todos los archivos Excel del directorio principal
    archivos_admin = glob.glob(os.path.join(UPLOAD_DIR, "*.xlsx")) + glob.glob(os.path.join(UPLOAD_DIR, "*.xls"))
    for archivo in archivos_admin:
        nombre = os.path.basename(archivo)
        archivos.append({
            'id': str(uuid.uuid4()),
            'nombre_original': nombre,
            'ruta': archivo,
            'fecha_subida': datetime.fromtimestamp(os.path.getmtime(archivo)).strftime("%Y-%m-%d %H:%M:%S"),
            'equipo': 'admin'
        })
    
    # Obtener archivos por equipo
    equipos = ["Valencia Mestalla", "Juvenil A", "Juvenil B", "Cadete A", "Cadete B", "Infantil A", "Infantil B"]
    for equipo in equipos:
        equipo_slug = equipo.lower().replace(" ", "_")
        equipo_dir = os.path.join(UPLOAD_DIR, equipo_slug)
        if os.path.exists(equipo_dir):
            archivos_equipo = glob.glob(os.path.join(equipo_dir, "*.xlsx")) + glob.glob(os.path.join(equipo_dir, "*.xls"))
            for archivo in archivos_equipo:
                nombre = os.path.basename(archivo)
                archivos.append({
                    'id': str(uuid.uuid4()),
                    'nombre_original': nombre,
                    'ruta': archivo,
                    'fecha_subida': datetime.fromtimestamp(os.path.getmtime(archivo)).strftime("%Y-%m-%d %H:%M:%S"),
                    'equipo': equipo
                })
    
    return archivos

# Función para guardar archivos subidos
def guardar_archivo(uploaded_file, equipo=None):
    # Conservar el nombre original del archivo
    filename = uploaded_file.name
    
    # Determinar el equipo asociado
    equipo_asociado = equipo if equipo else st.session_state.get("equipo_actual", "admin")
    
    # Determinar la ruta donde se guardará el archivo
    if equipo_asociado == "admin":
        file_path = os.path.join(UPLOAD_DIR, filename)
    else:
        equipo_slug = equipo_asociado.lower().replace(" ", "_")
        equipo_dir = os.path.join(UPLOAD_DIR, equipo_slug)
        os.makedirs(equipo_dir, exist_ok=True)
        file_path = os.path.join(equipo_dir, filename)
    
    # Comprobar si el archivo ya existe
    if os.path.exists(file_path):
        return file_path, f"El archivo {filename} ya existe."
    
    # Guardar el archivo
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Reconstruir la lista de archivos
    st.session_state.archivos_subidos = escanear_archivos()
    
    return file_path, f"✅ Archivo {filename} guardado correctamente."

# Función para la página de inicio
def mostrar_inicio():
    st.title("Bienvenido a la Aplicación de Análisis del Valencia CF")
    
    # Mostrar contenido diferente según el tipo de usuario
    if st.session_state.get("usuario", "") == "admin":
        st.info("Como administrador, tienes acceso a todos los equipos y sus análisis.")
        st.write("Utiliza el navegador de equipos para acceder a la información de cada equipo.")
        
        # Botones para acciones rápidas
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Ver Navegador de Equipos", key="inicio_nav_equipos"):
                st.session_state["menu_seleccionado"] = "navegador_equipos"
                st.rerun()
        with col2:
            if st.button("Gestionar Plantilla", key="inicio_plantilla"):
                st.session_state["menu_seleccionado"] = "plantilla"
                st.rerun()
        with col3:
            if st.button("Ver Datos Totales", key="inicio_datos_totales"):
                st.session_state["menu_seleccionado"] = "datos_totales"
                st.rerun()
    else:
        # Para usuarios de equipo
        equipo_actual = st.session_state.get("equipo_actual", "")
        st.info(f"Has iniciado sesión como: {equipo_actual}")
        st.write("Utiliza el menú lateral para navegar por las diferentes secciones.")
        
        # Tarjeta del equipo
        st.subheader("Tu Equipo")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Ver Gráficos de Partido", key="inicio_graficos"):
                st.session_state["menu_seleccionado"] = "graficos_partido"
                st.rerun()
        with col2:
            if st.button("Registros Individuales", key="inicio_individuales"):
                st.session_state["menu_seleccionado"] = "registros_individuales"
                st.rerun()
        with col3:
            if st.button("Ver Datos Totales", key="inicio_datos_totales"):
                st.session_state["menu_seleccionado"] = "datos_totales"
                st.rerun()

# Función para mostrar la página de subir archivo
def pagina_subir_archivo():
    st.title("Subir Archivo")
    
    # Si es admin, mostrar selector de equipo
    equipo_seleccionado = None
    if st.session_state.get("usuario", "") == "admin":
        equipos = ["Valencia Mestalla", "Juvenil A", "Juvenil B", "Cadete A", "Cadete B", "Infantil A", "Infantil B"]
        equipo_seleccionado = st.selectbox("Selecciona el equipo", equipos)
    
    # Subida de archivo
    uploaded_file = st.file_uploader("Selecciona un archivo Excel", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        st.write("Archivo subido:", uploaded_file.name)
        if st.button("Guardar Archivo"):
            file_path, message = guardar_archivo(uploaded_file, equipo_seleccionado)
            st.success(message)
            
    # Asegurarse de que tenemos la lista de archivos
    if "archivos_subidos" not in st.session_state:
        st.session_state.archivos_subidos = escanear_archivos()
            
    # Mostrar archivos subidos
    st.subheader("Archivos Subidos")
    
    # Filtrar archivos por equipo si no es admin
    archivos_a_mostrar = st.session_state.archivos_subidos
    if st.session_state.get("usuario", "") != "admin":
        equipo_actual = st.session_state.get("equipo_actual", "")
        archivos_a_mostrar = [archivo for archivo in archivos_a_mostrar if archivo['equipo'] == equipo_actual]
    elif equipo_seleccionado:
        # Si es admin y ha seleccionado un equipo, mostrar solo los archivos de ese equipo
        archivos_a_mostrar = [archivo for archivo in archivos_a_mostrar if archivo['equipo'] == equipo_seleccionado]
    
    if not archivos_a_mostrar:
        st.info("No hay archivos subidos.")
    else:
        for i, archivo in enumerate(archivos_a_mostrar):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"{i+1}. {archivo['nombre_original']} ({archivo['equipo']})")
            with col2:
                st.write(f"Subido: {archivo['fecha_subida']}")
            with col3:
                if st.button("Eliminar", key=f"del_{archivo['id']}"):
                    # Eliminar el archivo
                    try:
                        os.remove(archivo['ruta'])
                        st.success(f"Archivo {archivo['nombre_original']} eliminado correctamente.")
                    except Exception as e:
                        st.error(f"Error al eliminar el archivo: {str(e)}")
                    
                    # Reescanear el directorio para actualizar la lista
                    st.session_state.archivos_subidos = escanear_archivos()
                    st.rerun()
    
    # Botón para volver atrás
    if st.button("Atrás"):
        # Si venimos del panel de equipo, volver a él
        if st.session_state.get("ver_archivos_equipo", False):
            st.session_state["ver_archivos_equipo"] = False
            st.session_state["menu_seleccionado"] = "navegador_equipos"
            st.session_state["ver_panel_equipo"] = True
        else:
            # Si no, volver al menú principal
            st.session_state["menu_seleccionado"] = "inicio"
        st.rerun()

# Función para los gráficos de partido
def pagina_graficos_partido():
    st.title("Gráficos del Partido")
    
    # Asegurarse de que tenemos la lista de archivos actualizada
    st.session_state.archivos_subidos = escanear_archivos()
    
    # Determinar qué archivos mostrar según el usuario
    archivos_a_mostrar = []
    if st.session_state.get("usuario", "") == "admin":
        # Si viene de un equipo específico, mostrar solo los archivos de ese equipo
        if st.session_state.get("equipo_seleccionado", ""):
            equipo = st.session_state["equipo_seleccionado"]
            archivos_a_mostrar = [a for a in st.session_state.archivos_subidos if a['equipo'] == equipo]
        else:
            # Si no, mostrar todos
            archivos_a_mostrar = st.session_state.archivos_subidos
    else:
        # Para usuarios normales, solo mostrar sus archivos
        equipo_actual = st.session_state.get("equipo_actual", "")
        archivos_a_mostrar = [a for a in st.session_state.archivos_subidos if a['equipo'] == equipo_actual]
    
    # Verificar si hay archivos para mostrar
    if not archivos_a_mostrar:
        st.warning("No hay archivos disponibles para analizar. Por favor, sube algunos archivos primero.")
        if st.button("Ir a Subir Archivos"):
            st.session_state["menu_seleccionado"] = "subir_archivo"
            st.rerun()
        return
    
    # Selector de archivo
    nombres_archivos = [archivo['nombre_original'] for archivo in archivos_a_mostrar]
    archivo_seleccionado = st.selectbox("Selecciona un archivo para analizar", nombres_archivos)
    
    # Encontrar la ruta del archivo seleccionado
    archivo_info = next((a for a in archivos_a_mostrar if a['nombre_original'] == archivo_seleccionado), None)
    
    if archivo_info:
        ruta_archivo = archivo_info['ruta']
        
        # Cargar el archivo Excel
        try:
            df = pd.read_excel(ruta_archivo)
            st.success(f"Archivo {archivo_seleccionado} cargado correctamente")
            
            # Visualizaciones en pestañas
            tabs = st.tabs(["Red de Pases", "Matriz de Pases", "Faltas", "Tiros", "Recuperaciones", "Pases Específicos"])
            
            with tabs[0]:
                graficos.red_de_pases(df)
            
            with tabs[1]:
                graficos.matriz_de_pases(df)
            
            with tabs[2]:
                graficos.faltas_valencia(df)
            
            with tabs[3]:
                graficos.tiros_valencia(df)
            
            with tabs[4]:
                graficos.recuperaciones_valencia(df)
                
            with tabs[5]:
                graficos.pases_especificos(df)
            
            # Agregar botón para exportar todos los gráficos en un solo PDF
            st.markdown("---")
            st.subheader("Exportar informe completo")
                
            col1, col2 = st.columns([1, 2])
            with col1:
                if st.button("📊 Generar PDF con todos los gráficos", key="export_all_charts"):
                    try:
                        equipo_nombre = archivo_info.get('equipo', 'Valencia CF')
                        download_btn = download_session_charts(equipo_nombre, archivo_seleccionado, df)
                        st.markdown(download_btn, unsafe_allow_html=True)
                        st.success("Informe completo generado. Haz clic en el botón para descargar.")
                    except Exception as e:
                        st.error(f"Error al generar el PDF: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
                
        except Exception as e:
            st.error(f"Error al cargar el archivo: {str(e)}")
    
    # Botón para volver atrás
    if st.button("Atrás"):
        # Si venimos del panel de equipo, volver a él
        if st.session_state.get("ver_graficos_equipo", False):
            st.session_state["ver_graficos_equipo"] = False
            st.session_state["menu_seleccionado"] = "navegador_equipos"
            st.session_state["ver_panel_equipo"] = True
        else:
            # Si no, volver al menú principal
            st.session_state["menu_seleccionado"] = "inicio"
        st.rerun()

# Función principal
def main():
    # Inicializar variables de sesión si no existen
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    
    if "menu_seleccionado" not in st.session_state:
        st.session_state.menu_seleccionado = "inicio"
    
    # Escanear los archivos al iniciar
    if "archivos_subidos" not in st.session_state:
        st.session_state.archivos_subidos = escanear_archivos()
    
    # Comprobar autenticación
    if not st.session_state.autenticado:
        login()
        return
    
    # Sidebar con navegación
    with st.sidebar:
        # Mostrar logo del Valencia CF (usando la URL directa)
        st.image("https://upload.wikimedia.org/wikipedia/en/thumb/c/ce/Valenciacf.svg/1200px-Valenciacf.svg.png", width=100)
        
        st.title("Valencia CF App")
        
        # Mostrar información del usuario actual
        if st.session_state.get("usuario", "") == "admin":
            st.info("Conectado como: Administrador")
            if st.session_state.get("equipo_seleccionado", ""):
                st.write(f"Equipo seleccionado: {st.session_state['equipo_seleccionado']}")
        else:
            st.info(f"Conectado como: {st.session_state.get('equipo_actual', '')}")
        
        # Menú de navegación
        st.subheader("Menú")
        if st.button("🏠 Inicio"):
            st.session_state.menu_seleccionado = "inicio"
            # Limpiar estados de redirección
            for key in ["ver_graficos_equipo", "ver_archivos_equipo", "ver_individuales_equipo", "ver_panel_equipo"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        if st.button("⚽ Plantilla"):
            st.session_state.menu_seleccionado = "plantilla"
            st.rerun()
        
        if st.button("📊 Navegador de Equipos"):
            st.session_state.menu_seleccionado = "navegador_equipos"
            # Limpiar estados específicos
            for key in ["ver_graficos_equipo", "ver_archivos_equipo", "ver_individuales_equipo"]:
                if key in st.session_state:
                    del st.session_state[key]
            if "ver_panel_equipo" in st.session_state:
                del st.session_state["ver_panel_equipo"]
            st.rerun()
        
        if st.button("📁 Subir Archivo"):
            st.session_state.menu_seleccionado = "subir_archivo"
            if "ver_archivos_equipo" in st.session_state:
                del st.session_state["ver_archivos_equipo"]
            st.rerun()
        
        if st.button("📈 Gráficos del Partido"):
            st.session_state.menu_seleccionado = "graficos_partido"
            if "ver_graficos_equipo" in st.session_state:
                del st.session_state["ver_graficos_equipo"]
            st.rerun()
            
        if st.button("📋 Registros Individuales"):
            st.session_state.menu_seleccionado = "registros_individuales"
            if "ver_individuales_equipo" in st.session_state:
                del st.session_state["ver_individuales_equipo"]
            st.rerun()
        
        if st.button("📊 Datos Totales"):
            st.session_state.menu_seleccionado = "datos_totales"
            st.rerun()
        
        # Botón para cerrar sesión
        if st.button("🔒 Cerrar Sesión"):
            # Limpiar variables de sesión
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            st.rerun()
    
    # Contenido principal según la selección del menú
    if st.session_state.menu_seleccionado == "inicio":
        mostrar_inicio()
    
    elif st.session_state.menu_seleccionado == "plantilla":
        plantilla_page()
    
    elif st.session_state.menu_seleccionado == "navegador_equipos":
        if st.session_state.get("ver_panel_equipo", False):
            mostrar_panel_equipo()
        else:
            mostrar_navegador_equipos()
    
    elif st.session_state.menu_seleccionado == "subir_archivo":
        pagina_subir_archivo()
    
    elif st.session_state.menu_seleccionado == "graficos_partido":
        pagina_graficos_partido()
        
    elif st.session_state.menu_seleccionado == "registros_individuales":
        pagina_registros_individuales()
        
    elif st.session_state.menu_seleccionado == "datos_totales":
        pagina_datos_totales()

# Ejecutar la aplicación
if __name__ == "__main__":
    main()