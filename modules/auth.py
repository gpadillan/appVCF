import streamlit as st
import json
import os
import base64
import pandas as pd
import numpy as np

# Archivo para guardar los usuarios y equipos
AUTH_DIR = "auth_data"
AUTH_FILE = os.path.join(AUTH_DIR, "usuarios.json")
ASSETS_DIR = "assets"

# Asegurar que los directorios existen
for directory in [AUTH_DIR, ASSETS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Ruta a la imagen del escudo
ESCUDO_PATH = os.path.join(ASSETS_DIR, "valencia.png")

# Datos iniciales de usuarios si no existe el archivo
USUARIOS_INICIALES = {
    "admin": {
        "password": "1234",
        "role": "admin",
        "nombre": "Administrador",
        "equipo_id": None # El admin no está asociado a ningún equipo específico
    },
    "valenciam": {
        "password": "vcf2024",
        "role": "equipo",
        "nombre": "Valencia Mestalla",
        "equipo_id": "mestalla"
    },
    "juvenila": {
        "password": "vcf2024",
        "role": "equipo",
        "nombre": "Juvenil A",
        "equipo_id": "juvenila"
    },
    "juvenilb": {
        "password": "vcf2024",
        "role": "equipo",
        "nombre": "Juvenil B",
        "equipo_id": "juvenilb"
    },
    "cadetea": {
        "password": "vcf2024",
        "role": "equipo",
        "nombre": "Cadete A",
        "equipo_id": "cadetea"
    },
    "cadeteb": {
        "password": "vcf2024",
        "role": "equipo",
        "nombre": "Cadete B",
        "equipo_id": "cadeteb"
    },
    "infantila": {
        "password": "vcf2024",
        "role": "equipo",
        "nombre": "Infantil A",
        "equipo_id": "infantila"
    },
    "infantilb": {
        "password": "vcf2024",
        "role": "equipo",
        "nombre": "Infantil B",
        "equipo_id": "infantilb"
    }
}

# Cargar usuarios o crear el archivo inicial
def cargar_usuarios():
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                # Si hay error en el JSON, usar los usuarios iniciales
                return USUARIOS_INICIALES
    else:
        # Si no existe el archivo, crear con usuarios iniciales
        with open(AUTH_FILE, 'w') as file:
            json.dump(USUARIOS_INICIALES, file, indent=4)
        return USUARIOS_INICIALES

# Guardar usuarios en el archivo
def guardar_usuarios(usuarios):
    with open(AUTH_FILE, 'w') as file:
        json.dump(usuarios, file, indent=4)

# Función para cargar archivos de imagen en base64
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# Función de autenticación
def login():
    """
    Controla el acceso a la aplicación mediante un sistema de login.
    Returns:
        bool: True si el usuario está autenticado, False en caso contrario.
    """
    # Cargar usuarios
    usuarios = cargar_usuarios()
    
    # Inicializar estado de sesión si no existe
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
        st.session_state["intentos"] = 0
    
    # Si ya está autenticado, devolver True
    if st.session_state["autenticado"]:
        return True
    
    # Ruta al escudo del Valencia CF (ajusta según la ubicación real)
    escudo_base64 = get_image_base64(ESCUDO_PATH)
    escudo_html = ""
    if escudo_base64:
        escudo_html = f'<img src="data:image/png;base64,{escudo_base64}" class="escudo-vcf" alt="Escudo Valencia CF">'
    else:
        # Fallback si no se encuentra la imagen
        escudo_html = '<div class="escudo-placeholder">VCF</div>'
    
    # Aplicar estilos con CSS para un diseño más elegante
    st.markdown(
        """
        <style>
        /* Ocultar elementos de Streamlit */
        #MainMenu {visibility: hidden !important;}
        header {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        /* Fondo con degradado naranja */
        .stApp {
            background: #FF6600 !important;
        }
        /* Estilos para el contenedor principal */
        .login-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding-top: 50px;
        }
        /* Estilos para el logo */
        .logo-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 30px;
        }
        .escudo-vcf {
            width: 120px;
            height: auto;
            margin-bottom: 15px;
        }
        .logo-title {
            color: white;
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 30px;
        }
        /* Estilos para el título de acceso */
        .access-title {
            color: white;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 20px;
            text-align: center;
        }
        /* Estilos para las etiquetas */
        .input-label {
            color: white;
            font-weight: 600;
            margin-bottom: 8px;
            display: block;
        }
        /* Estilos para los inputs */
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 10px 15px;
            margin-bottom: 15px;
            border: none;
            border-radius: 5px;
            background-color: white;
        }
        /* Estilos para el botón */
        div[data-testid="stButton"] > button {
            background-color: #FF9900 !important;
            color: white !important;
            font-weight: bold !important;
            width: 100% !important;
        }
        div[data-testid="stButton"] > button:hover {
            background-color: #FF7400 !important;
        }
        /* Estilos para el pie de página */
        .footer {
            position: fixed;
            bottom: 20px;
            width: 100%;
            text-align: center;
            color: white;
            font-size: 12px;
            left: 0;
        }
        /* Escudo placeholder */
        .escudo-placeholder {
            width: 100px;
            height: 100px;
            background-color: white;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: bold;
            font-size: 24px;
            color: #FF6600;
            margin-bottom: 15px;
        }
        /* Estilos para el panel de administración */
        .option-card {
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 15px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .option-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .option-title {
            color: #FF6600;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .option-description {
            color: #555;
            font-size: 14px;
        }
        /* Estilos para el header */
        .header-container {
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .header-logo {
            display: flex;
            align-items: center;
        }
        .escudo-header {
            width: 30px;
            height: auto;
            margin-right: 10px;
        }
        .escudo-placeholder-header {
            width: 30px;
            height: 30px;
            background-color: #FF6600;
            color: white;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: bold;
            font-size: 12px;
            margin-right: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Estructura HTML principal con clases CSS personalizadas
    st.markdown(
        f"""
        <div class="login-container">
            <div class="logo-container">
                {escudo_html}
                <div class="logo-title">Academia Valencia CF</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Agregamos el título "Acceso al Sistema" directamente
    st.markdown("<h3 style='text-align: center; color: white; margin-bottom: 20px;'>Acceso al Sistema</h3>", unsafe_allow_html=True)
    
    # Formulario de login
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Etiqueta de usuario
        st.markdown('<div class="input-label">Usuario</div>', unsafe_allow_html=True)
        usuario = st.text_input("", placeholder="Ingrese su usuario", key="usuario_input", label_visibility="collapsed")
        
        # Etiqueta de contraseña
        st.markdown('<div class="input-label">Contraseña</div>', unsafe_allow_html=True)
        contraseña = st.text_input("", type="password", placeholder="Ingrese su contraseña", key="password_input", label_visibility="collapsed")
        
        # Botón de inicio de sesión
        if st.button("Iniciar Sesión", type="primary"):
            if usuario in usuarios and usuarios[usuario]["password"] == contraseña:
                st.session_state["autenticado"] = True
                st.session_state["usuario"] = usuario
                st.session_state["role"] = usuarios[usuario]["role"]
                st.session_state["nombre_equipo"] = usuarios[usuario]["nombre"]
                st.session_state["equipo_actual"] = usuarios[usuario]["nombre"]
                st.session_state["equipo_id"] = usuarios[usuario]["equipo_id"]
                st.success(f"✅ Bienvenido, {usuarios[usuario]['nombre']}!")
                st.balloons() # Efecto visual de celebración
                st.rerun()
            else:
                st.session_state["intentos"] += 1
                st.error("❌ Usuario o contraseña incorrectos")
                if st.session_state["intentos"] >= 3:
                    st.warning("⚠️ Demasiados intentos fallidos. Por favor, contacta con el administrador.")
    
    # Pie de página
    st.markdown(
        """
        <div class="footer">
            © 2025 Academia Valencia CF | Todos los derechos reservados
        </div>
        """,
        unsafe_allow_html=True
    )
    
    return st.session_state["autenticado"]

# Función para mostrar el encabezado con el escudo en todas las páginas después del login
def mostrar_header():
    """
    Muestra un encabezado con el escudo del Valencia CF y el nombre de la aplicación.
    """
    # Obtener el escudo como base64
    escudo_base64 = get_image_base64(ESCUDO_PATH)
    escudo_html = ""
    if escudo_base64:
        escudo_html = f'<img src="data:image/png;base64,{escudo_base64}" class="escudo-header" alt="Escudo Valencia CF">'
    else:
        # Fallback si no se encuentra la imagen
        escudo_html = '<div class="escudo-placeholder-header">VCF</div>'
    
    # Mostrar el header
    st.markdown(
        f"""
        <div class="header-container">
            <div class="header-logo">
                {escudo_html}
                <span>Academia Valencia CF</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Pantalla principal después del login
def main_app():
    # Agregar estilos CSS para prevenir el modo oscuro
    st.markdown(
        """
        <style>
        /* Deshabilitar modo oscuro */
        html, body, .stApp {
            color-scheme: light !important;
        }
        
        /* Forzar modo claro */
        * {
            color-scheme: light !important;
        }
        
        /* Asegurar que los elementos mantengan su estilo original */
        .stApp {
            background-color: white !important;
        }
        </style>
        """, 
        unsafe_allow_html=True
    )
    
    # Resto de tu código de main_app()
    mostrar_header()
    
    # ... (código existente)
    # Mostrar header con escudo
    mostrar_header()
    
    # Resto del código de tu aplicación
    st.title(f"Bienvenido, {st.session_state['nombre_equipo']}")
    
    # Mostrar diferentes opciones según el rol
    if st.session_state["role"] == "admin":
        admin_panel()
    else:
        equipo_panel()

# Panel de administrador
def admin_panel():
    """
    Panel para el administrador con funcionalidades limitadas a visualización.
    No puede subir ni editar archivos, solo navegar y ver información.
    """
    st.subheader("Panel de Administración")
    
    # Información sobre las limitaciones
    st.info("Como administrador, puedes visualizar la información de todos los equipos pero no puedes modificar ni subir archivos.")
    
    # Menú de opciones (eliminado "Navegador de Equipos")
    option = st.selectbox(
        "Selecciona una opción:",
        ["Plantillas", "Gráficos del Partido", "Registros Individuales", "Datos Totales", "Archivos Subidos"]
    )
    
    # Mostrar contenido según la opción seleccionada
    if option == "Plantillas":
        mostrar_plantillas()
    elif option == "Gráficos del Partido":
        mostrar_graficos_partido()
    elif option == "Registros Individuales":
        mostrar_registros_individuales()
    elif option == "Datos Totales":
        mostrar_datos_totales()
    elif option == "Archivos Subidos":
        mostrar_archivos_subidos()

def mostrar_detalles_equipo(equipo_id, nombre_equipo):
    """Muestra los detalles de un equipo específico."""
    st.subheader(f"Detalles del equipo: {nombre_equipo}")
    # Aquí se mostrarían las estadísticas y datos del equipo
    # Como ejemplo, usamos datos ficticios
    st.markdown("#### Datos generales")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Partidos jugados", "15")
        st.metric("Victorias", "8")
        st.metric("Empates", "4")
    with col2:
        st.metric("Derrotas", "3")
        st.metric("Goles a favor", "24")
        st.metric("Goles en contra", "14")
    
    # Jugadores del equipo (ejemplo)
    st.markdown("#### Jugadores")
    jugadores = [
        {"nombre": "Jugador 1", "posición": "Portero", "partidos": 14},
        {"nombre": "Jugador 2", "posición": "Defensa", "partidos": 15},
        {"nombre": "Jugador 3", "posición": "Centrocampista", "partidos": 12},
        {"nombre": "Jugador 4", "posición": "Delantero", "partidos": 15},
        {"nombre": "Jugador 5", "posición": "Defensa", "partidos": 10}
    ]
    
    # Crear una tabla con los jugadores
    df = pd.DataFrame(jugadores)
    st.dataframe(df, use_container_width=True)

def mostrar_plantillas():
    """Muestra las plantillas de todos los equipos."""
    st.subheader("Plantillas")
    
    # Selector de equipo
    equipos = obtener_equipos_disponibles()
    nombres_equipos = [equipo["nombre"] for equipo in equipos]
    equipo_seleccionado = st.selectbox("Selecciona un equipo", nombres_equipos)
    
    # Encontrar el equipo seleccionado
    equipo_id = None
    for equipo in equipos:
        if equipo["nombre"] == equipo_seleccionado:
            equipo_id = equipo["id"]
            break
    
    if equipo_id:
        # Datos de ejemplo para la plantilla
        # Generar algunos datos de ejemplo
        data = {
            "Nombre": ["Jugador 1", "Jugador 2", "Jugador 3", "Jugador 4", "Jugador 5"],
            "Posición": ["Portero", "Defensa", "Centrocampista", "Delantero", "Defensa"],
            "Edad": [18, 17, 19, 18, 17],
            "Partidos": [15, 12, 14, 10, 8],
            "Goles": [0, 1, 3, 7, 0],
            "Asistencias": [0, 2, 5, 3, 1]
        }
        df = pd.DataFrame(data)
        
        # Mostrar tabla con la plantilla
        st.dataframe(df, use_container_width=True)
        
        # Añadir algunas estadísticas visuales
        st.subheader("Estadísticas por posición")
        
        # Agrupar por posición
        pos_stats = df.groupby("Posición").agg({
            "Partidos": "mean",
            "Goles": "sum",
            "Asistencias": "sum"
        }).reset_index()
        
        # Mostrar gráfico de barras para goles por posición
        st.bar_chart(pos_stats.set_index("Posición")["Goles"])

def mostrar_graficos_partido():
    """Muestra gráficos relacionados con los partidos."""
    st.subheader("Gráficos del Partido")
    
    # Selector de equipo
    equipos = obtener_equipos_disponibles()
    nombres_equipos = [equipo["nombre"] for equipo in equipos]
    equipo_seleccionado = st.selectbox("Selecciona un equipo", nombres_equipos)
    
    # Selector de partido (ejemplo)
    partidos = [
        "Partido 1 - 01/02/2025",
        "Partido 2 - 08/02/2025",
        "Partido 3 - 15/02/2025",
        "Partido 4 - 22/02/2025",
        "Partido 5 - 01/03/2025"
    ]
    partido_seleccionado = st.selectbox("Selecciona un partido", partidos)
    
    # Mostrar gráficos de ejemplo
    st.subheader(f"Estadísticas: {partido_seleccionado}")
    
    # Ejemplo de datos de posesión
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Posesión", "58%")
        st.metric("Disparos", "14")
    with col2:
        st.metric("Disparos a puerta", "7")
        st.metric("Córners", "6")
    with col3:
        st.metric("Faltas", "12")
        st.metric("Fueras de juego", "3")
    
    # Gráfico de ejemplo para la posesión por periodos
    # Datos de ejemplo para la posesión por períodos
    data = {
        "Periodo": ["0-15", "15-30", "30-45", "45-60", "60-75", "75-90"],
        "Posesión": [55, 62, 48, 60, 65, 57]
    }
    df = pd.DataFrame(data)
    
    # Mostrar gráfico de línea para la posesión
    st.subheader("Posesión por periodos")
    st.line_chart(df.set_index("Periodo"))

def mostrar_registros_individuales():
    """Muestra registros individuales de los jugadores."""
    st.subheader("Registros Individuales")
    
    # Selector de equipo
    equipos = obtener_equipos_disponibles()
    nombres_equipos = [equipo["nombre"] for equipo in equipos]
    equipo_seleccionado = st.selectbox("Selecciona un equipo", nombres_equipos)
    
    # Jugadores de ejemplo
    jugadores = ["Jugador 1", "Jugador 2", "Jugador 3", "Jugador 4", "Jugador 5"]
    jugador_seleccionado = st.selectbox("Selecciona un jugador", jugadores)
    
    # Mostrar estadísticas del jugador
    st.subheader(f"Estadísticas de {jugador_seleccionado}")
    
    # Métricas clave
    col1, col2, col3 = st.columns(3)
    
    # Datos de ejemplo
    partidos = 15
    minutos = 1250
    goles = 5
    asistencias = 3
    tarjetas_amarillas = 2
    tarjetas_rojas = 0
    
    with col1:
        st.metric("Partidos", str(partidos))
        st.metric("Minutos", str(minutos))
    with col2:
        st.metric("Goles", str(goles))
        st.metric("Asistencias", str(asistencias))
    with col3:
        st.metric("Tarjetas Amarillas", str(tarjetas_amarillas))
        st.metric("Tarjetas Rojas", str(tarjetas_rojas))
    
    # Gráfico de rendimiento por partido
    st.subheader("Rendimiento por partido")
    
    # Datos de ejemplo para el rendimiento por partido
    data = {
        "Partido": [f"Partido {i}" for i in range(1, partidos+1)],
        "Minutos": [90, 85, 90, 75, 90, 90, 45, 90, 90, 90, 75, 90, 90, 65, 85],
        "Valoración": [7.5, 6.8, 8.2, 7.0, 7.8, 6.5, 6.2, 7.5, 8.0, 7.3, 6.7, 7.9, 8.1, 7.0, 7.5]
    }
    df = pd.DataFrame(data)
    
    # Mostrar gráfico de línea para la valoración
    st.line_chart(df.set_index("Partido")["Valoración"])

def mostrar_datos_totales():
    """Muestra datos totales de todos los equipos."""
    st.subheader("Datos Totales")
    
    # Equipos disponibles
    equipos = obtener_equipos_disponibles()
    
    # Datos de ejemplo para cada equipo
    data = []
    for equipo in equipos:
        data.append({
            "Equipo": equipo["nombre"],
            "Partidos": 15,
            "Victorias": np.random.randint(5, 12),
            "Empates": np.random.randint(1, 5),
            "Derrotas": np.random.randint(1, 5),
            "Goles a favor": np.random.randint(15, 30),
            "Goles en contra": np.random.randint(10, 25)
        })
    
    df = pd.DataFrame(data)
    
    # Calcular puntos
    df["Puntos"] = df["Victorias"] * 3 + df["Empates"]
    
    # Ordenar por puntos
    df = df.sort_values("Puntos", ascending=False).reset_index(drop=True)
    
    # Mostrar tabla con la clasificación
    st.dataframe(df, use_container_width=True)
    
    # Gráfico comparativo de goles
    st.subheader("Comparativa de goles")
    
    # Preparar datos para el gráfico
    chart_data = df[["Equipo", "Goles a favor", "Goles en contra"]]
    
    # Crear gráfico de barras
    st.bar_chart(chart_data.set_index("Equipo"))

# Nueva función para mostrar archivos subidos por equipos
def mostrar_archivos_subidos():
    """Muestra los archivos subidos por los distintos equipos.
    Solo disponible para el administrador."""
    st.subheader("Archivos Subidos por Equipos")
    
    # Verificar si hay archivos subidos en la sesión
    if "archivos_subidos" not in st.session_state or not st.session_state.archivos_subidos:
        st.warning("No hay archivos subidos por los equipos.")
        return
    
    # Obtener todos los archivos subidos
    archivos = st.session_state.archivos_subidos
    
    # Filtro por equipo
    equipos_con_archivos = sorted(list(set([archivo['equipo'] for archivo in archivos if 'equipo' in archivo])))
    equipo_seleccionado = st.selectbox("Filtrar por equipo:", ["Todos"] + equipos_con_archivos)
    
    # Filtrar por equipo seleccionado
    if equipo_seleccionado != "Todos":
        archivos_filtrados = [a for a in archivos if a.get('equipo') == equipo_seleccionado]
    else:
        archivos_filtrados = archivos
    
    # Mostrar tabla de archivos
    if archivos_filtrados:
        # Crear un DataFrame para mostrar de forma ordenada
        data = []
        for archivo in archivos_filtrados:
            data.append({
                "Nombre": archivo.get('nombre_original', 'Sin nombre'),
                "Equipo": archivo.get('equipo', 'Desconocido'),
                "Fecha": archivo.get('fecha_subida', 'Desconocida'),
            })
        
        df_archivos = pd.DataFrame(data)
        st.dataframe(df_archivos, use_container_width=True)
        
        # Selección de archivo para visualizar
        nombres_archivos = [a.get('nombre_original', 'Sin nombre') for a in archivos_filtrados]
        archivo_seleccionado = st.selectbox("Selecciona un archivo para visualizar:", nombres_archivos)
        
        # Encontrar el archivo seleccionado
        archivo_info = next((a for a in archivos_filtrados if a.get('nombre_original') == archivo_seleccionado), None)
        
        if archivo_info and 'ruta' in archivo_info:
            try:
                # Leer el archivo
                if archivo_info['ruta'].endswith('.csv'):
                    df = pd.read_csv(archivo_info['ruta'])
                else:
                    df = pd.read_excel(archivo_info['ruta'])
                
                # Mostrar vista previa
                st.subheader(f"Vista previa de {archivo_seleccionado}")
                st.dataframe(df.head(10), use_container_width=True)
                
                # Opciones adicionales
                with st.expander("Análisis básico"):
                    if st.button("Estadísticas básicas"):
                        st.write(df.describe())
                    if st.button("Ver columnas"):
                        st.write(df.columns.tolist())
            except Exception as e:
                st.error(f"Error al leer el archivo: {str(e)}")
    else:
        st.info(f"No hay archivos disponibles para {equipo_seleccionado if equipo_seleccionado != 'Todos' else 'ningún equipo'}.")

# Panel de equipo
def equipo_panel():
    """Panel para usuarios de tipo equipo"""
    st.subheader(f"Panel del Equipo: {st.session_state['nombre_equipo']}")
    
    # Pestañas para las diferentes secciones del equipo
    tab1, tab2, tab3 = st.tabs(["Jugadores", "Entrenamientos", "Estadísticas"])
    
    with tab1:
        st.write("Gestión de jugadores del equipo")
        # Implementa la gestión de jugadores
    
    with tab2:
        st.write("Calendario de entrenamientos")
        # Calendario y registro de entrenamientos
    
    with tab3:
        st.write("Estadísticas del equipo")
        # Gráficos y estadísticas

# Comprobar si el usuario actual puede acceder a un equipo específico
def puede_acceder_equipo(equipo_id):
    """
    Comprueba si el usuario actual puede acceder a un equipo específico.
    El administrador puede acceder a todos los equipos.
    Los usuarios de equipo solo pueden acceder a su propio equipo.
    Args:
        equipo_id: ID del equipo al que se intenta acceder
    Returns:
        bool: True si tiene acceso, False en caso contrario
    """
    # Si no está autenticado, no tiene acceso
    if not st.session_state.get("autenticado", False):
        return False
    
    # El administrador tiene acceso a todos los equipos
    if st.session_state.get("role") == "admin":
        return True
    
    # Un equipo solo puede acceder a su propio equipo
    return st.session_state.get("equipo_id") == equipo_id

# Obtener lista de equipos disponibles
def obtener_equipos_disponibles():
    """
    Devuelve una lista de equipos disponibles según el usuario actual.
    Para el administrador, devuelve todos los equipos.
    Para un usuario de equipo, devuelve solo su equipo.
    Returns:
        list: Lista de diccionarios con información de equipos
    """
    usuarios = cargar_usuarios()
    equipos = []
    
    # Si es administrador, mostrar todos los equipos
    if st.session_state.get("role") == "admin":
        for username, user_data in usuarios.items():
            if user_data["role"] == "equipo" and user_data["equipo_id"]:
                equipos.append({
                    "id": user_data["equipo_id"],
                    "nombre": user_data["nombre"],
                    "username": username
                })
    # Si es un equipo, mostrar solo su equipo
    elif st.session_state.get("role") == "equipo" and st.session_state.get("equipo_id"):
        equipos.append({
            "id": st.session_state["equipo_id"],
            "nombre": st.session_state["nombre_equipo"],
            "username": st.session_state["usuario"]
        })
    
    return equipos

# Función principal
def main():
    # Intentar autenticar al usuario
    if login():
        # Si está autenticado, mostrar la aplicación principal
        main_app()

# Ejecutar la aplicación
if __name__ == "__main__":
    main()