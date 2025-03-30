import streamlit as st
import os
import json
from PIL import Image
from datetime import datetime
import base64

# Constantes - Reemplaza la importación de modules.player_utils
PLAYERS_DATA_DIR = "players_data"
PLAYERS_FILE = os.path.join(PLAYERS_DATA_DIR, "players.json")
PLAYERS_PHOTOS_DIR = os.path.join(PLAYERS_DATA_DIR, "photos")

# Crear directorios si no existen
os.makedirs(PLAYERS_DATA_DIR, exist_ok=True)
os.makedirs(PLAYERS_PHOTOS_DIR, exist_ok=True)

# Ruta al escudo
ESCUDO_PATH = os.path.join("assets", "valencia.png")

# Función para cargar jugadores de la plantilla
def cargar_jugadores_plantilla():
    if not os.path.exists(PLAYERS_FILE):
        return []
    
    try:
        with open(PLAYERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

# Función para guardar jugadores en la plantilla
def guardar_jugadores_plantilla(jugadores):
    with open(PLAYERS_FILE, 'w') as f:
        json.dump(jugadores, f, indent=4)

# Función para obtener un jugador por su ID
def obtener_jugador_por_id(jugador_id):
    jugadores = cargar_jugadores_plantilla()
    for jugador in jugadores:
        if jugador.get('id') == jugador_id:
            return jugador
    return None

# Función para obtener la foto de un jugador
def obtener_foto_jugador(jugador_id):
    """
    Busca la foto de un jugador, primero por ID y luego por nombre si no la encuentra.
    """
    # Primero intenta buscar por ID (el método original)
    for ext in ['jpg', 'jpeg', 'png']:
        ruta_foto = os.path.join(PLAYERS_PHOTOS_DIR, f"{jugador_id}.{ext}")
        if os.path.exists(ruta_foto):
            return ruta_foto
    
    # Si no la encuentra, busca el nombre del jugador en la lista de jugadores
    jugadores = cargar_jugadores_plantilla()
    for jugador in jugadores:
        if jugador['id'] == jugador_id and 'nombre' in jugador:
            # Buscar por nombre
            nombre = jugador['nombre']
            for ext in ['jpg', 'jpeg', 'png']:
                ruta_foto = os.path.join(PLAYERS_PHOTOS_DIR, f"{nombre}.{ext}")
                if os.path.exists(ruta_foto):
                    return ruta_foto
    
    return None

# Función para convertir una imagen a base64
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# Funciones de compatibilidad (puedes eliminarlas eventualmente)
def cargar_jugadores():
    return cargar_jugadores_plantilla()

def guardar_jugadores(jugadores):
    guardar_jugadores_plantilla(jugadores)

def obtener_jugador(jugador_id):
    return obtener_jugador_por_id(jugador_id)

# Función para obtener el nombre del equipo actual del usuario
def obtener_equipo_actual():
    # Si es admin, devuelve None para indicar que puede ver todos los equipos
    if st.session_state.get("role") == "admin":
        return None
    # Si es un equipo, devuelve el nombre del equipo
    return st.session_state.get("nombre_equipo")

# Función para mostrar un card de jugador
def mostrar_card_jugador(jugador):
    # Obtener escudo como base64
    escudo_base64 = get_image_base64(ESCUDO_PATH)
    
    # Estilo CSS para el card
    card_style = """
    <style>
    .jugador-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s;
    }
    .jugador-card:hover {
        transform: translateY(-5px);
    }
    .jugador-foto {
        width: 100%;
        height: 200px;
        border-radius: 10px;
        margin-bottom: 10px;
        object-fit: cover;
    }
    .jugador-nombre {
        font-size: 18px;
        font-weight: bold;
        margin: 0;
        color: #ff9800;
    }
    .escudo-temporada {
        width: 45px;
        height: 45px;
        border-radius: 50%;
        background-color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 10px;
        border: 2px solid #ff9800;
        overflow: hidden;
    }
    .escudo-img {
        width: 35px;
        height: 35px;
        object-fit: contain;
    }
    .jugador-posicion {
        color: #666;
        font-size: 14px;
        margin: 5px 0;
    }
    .jugador-equipo {
        color: #333;
        font-size: 14px;
        margin: 5px 0;
        font-weight: bold;
    }
    .jugador-temporada-info {
        color: #666;
        font-size: 14px;
        margin: 5px 0;
    }
    .jugador-info {
        display: flex;
        align-items: center;
    }
    .jugador-acciones {
        display: flex;
        justify-content: space-between;
        margin-top: 10px;
    }
    .no-foto {
        height: 200px;
        background-color: #f0f0f0;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 10px;
        color: #999;
    }
    .escudo-container {
        position: relative;
    }
    .escudo-placeholder {
        width: 45px;
        height: 45px;
        border-radius: 50%;
        background-color: #ff9800;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 10px;
    }
    </style>
    """
    
    # Ruta de la foto
    tiene_foto = False
    foto_path = ""
    if 'foto' in jugador and jugador['foto']:
        foto_path = os.path.join(PLAYERS_PHOTOS_DIR, jugador['foto'])
        tiene_foto = os.path.exists(foto_path)
    
    # Crear columna para cada card
    with st.container():
        st.markdown(card_style, unsafe_allow_html=True)
        
        # Container para el card
        card_container = st.container()
        
        with card_container:
            # Foto del jugador
            if tiene_foto:
                st.image(foto_path, use_container_width=True)
            else:
                st.markdown(
                    '<div class="no-foto">Sin foto</div>',
                    unsafe_allow_html=True
                )
            
            # Información del jugador
            col1, col2 = st.columns([1, 3])
            with col1:
                # Mostrar solo el escudo sin la temporada superpuesta
                if escudo_base64:
                    st.markdown(
                        f'''
                        <div class="escudo-container">
                            <div class="escudo-temporada">
                                <img src="data:image/png;base64,{escudo_base64}" class="escudo-img" alt="Escudo VCF">
                            </div>
                        </div>
                        ''',
                        unsafe_allow_html=True
                    )
                else:
                    # Fallback si no se encuentra la imagen del escudo
                    st.markdown(
                        '<div class="escudo-placeholder">VCF</div>',
                        unsafe_allow_html=True
                    )
            with col2:
                st.markdown(
                    f'<p class="jugador-nombre">{jugador["nombre"]}</p>',
                    unsafe_allow_html=True
                )
                # Mostrar equipo
                st.markdown(
                    f'<p class="jugador-equipo">{jugador.get("equipo", "")}</p>',
                    unsafe_allow_html=True
                )
                # Mostrar posición
                st.markdown(
                    f'<p class="jugador-posicion">{jugador["posicion"]}</p>',
                    unsafe_allow_html=True
                )
                # Mostrar temporada
                st.markdown(
                    f'<p class="jugador-temporada-info">Temporada: {jugador.get("temporada", "")}</p>',
                    unsafe_allow_html=True
                )
            
            # Botones de acción
            col1, col2 = st.columns(2)
            with col1:
                # Solo mostrar botón de editar si:
                # 1. Es admin, o
                # 2. Es el entrenador del equipo del jugador
                equipo_actual = obtener_equipo_actual()
                puede_editar = (equipo_actual is None) or (jugador.get("equipo") == equipo_actual)
                
                if puede_editar and st.button("✏️ Editar", key=f"edit_{jugador['id']}"):
                    st.session_state["jugador_editar"] = jugador['id']
                    st.rerun()
            with col2:
                # Solo mostrar botón de eliminar si:
                # 1. Es admin, o
                # 2. Es el entrenador del equipo del jugador
                if puede_editar and st.button("❌ Eliminar", key=f"delete_{jugador['id']}"):
                    eliminar_jugador(jugador['id'])
                    st.success(f"Jugador {jugador['nombre']} eliminado")
                    st.rerun()

# Función para eliminar un jugador
def eliminar_jugador(jugador_id):
    jugadores = cargar_jugadores()
    jugador = None
    
    # Encontrar el jugador
    for j in jugadores:
        if j['id'] == jugador_id:
            jugador = j
            break
    
    if jugador:
        # Verificar que el usuario tiene permiso para eliminar este jugador
        equipo_actual = obtener_equipo_actual()
        if equipo_actual is not None and jugador.get("equipo") != equipo_actual:
            st.error("No tienes permiso para eliminar jugadores de otros equipos.")
            return False
        
        # Eliminar foto si existe
        if 'foto' in jugador and jugador['foto']:
            foto_path = os.path.join(PLAYERS_PHOTOS_DIR, jugador['foto'])
            if os.path.exists(foto_path):
                os.remove(foto_path)
        
        # Eliminar de la lista
        jugadores = [j for j in jugadores if j['id'] != jugador_id]
        guardar_jugadores(jugadores)
        return True
    
    return False

# Función para mostrar la plantilla actual
def mostrar_plantilla():
    jugadores = cargar_jugadores()
    
    # Filtrar jugadores según el rol del usuario
    equipo_actual = obtener_equipo_actual()
    
    # Si no es admin, filtrar por equipo automáticamente
    if equipo_actual is not None:
        jugadores = [j for j in jugadores if j.get("equipo") == equipo_actual]
    
    if not jugadores:
        st.info("No hay jugadores en la plantilla. Añade jugadores en la pestaña 'Añadir Jugador'.")
        return
    
    st.subheader("Plantilla Actual")
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        # Filtro por posición
        posiciones = ["Todas"] + sorted(list(set(j["posicion"] for j in jugadores)))
        posicion_filtro = st.selectbox("Filtrar por posición:", posiciones)
    
    with col2:
        # Filtro por equipo (solo para admin)
        if equipo_actual is None:  # Es admin
            equipos = ["Todos", "Valencia Mestalla", "Juvenil A", "Juvenil B", "Cadete A", "Cadete B", "Infantil A", "Infantil B"]
            equipo_filtro = st.selectbox("Filtrar por equipo:", equipos)
        else:
            # Para usuarios de equipo, mostrar su equipo como información
            st.markdown(f"**Equipo: {equipo_actual}**")
            equipo_filtro = equipo_actual  # Siempre filtrado por su equipo
    
    # Buscar jugador
    busqueda = st.text_input("Buscar jugador:", "")
    
    # Aplicar filtros
    jugadores_filtrados = jugadores
    
    # Filtro por posición
    if posicion_filtro != "Todas":
        jugadores_filtrados = [j for j in jugadores_filtrados if j["posicion"] == posicion_filtro]
    
    # Filtro por equipo (solo para admin)
    if equipo_actual is None and equipo_filtro != "Todos":
        jugadores_filtrados = [j for j in jugadores_filtrados if j.get("equipo", "") == equipo_filtro]
    
    # Filtro por búsqueda
    if busqueda:
        busqueda = busqueda.lower()
        jugadores_filtrados = [j for j in jugadores_filtrados if 
                              busqueda in j["nombre"].lower() or 
                              busqueda in j.get("equipo", "").lower()]
    
    # Mostrar jugadores en cards
    if not jugadores_filtrados:
        st.warning("No se encontraron jugadores con los filtros aplicados.")
    else:
        st.write(f"Mostrando {len(jugadores_filtrados)} jugadores")
        
        # Mostrar en grid (3 columnas)
        cols = st.columns(3)
        for i, jugador in enumerate(jugadores_filtrados):
            col_idx = i % 3
            with cols[col_idx]:
                mostrar_card_jugador(jugador)

# Función para agregar un nuevo jugador
def agregar_jugador():
    # Verificar si es administrador
    if st.session_state.get("role") == "admin":
        st.warning("Como administrador, no puedes añadir ni editar jugadores. Esta funcionalidad está reservada para los equipos.")
        return
    
    # Obtener el equipo actual del usuario
    equipo_actual = obtener_equipo_actual()
    if equipo_actual is None:
        st.error("No se puede determinar tu equipo. Contacta con el administrador.")
        return
    
    # Si hay un jugador para editar, cargar sus datos
    jugador_editar = None
    if "jugador_editar" in st.session_state and st.session_state["jugador_editar"]:
        jugador_id = st.session_state["jugador_editar"]
        jugador_editar = obtener_jugador(jugador_id)
        
        # Verificar que el usuario puede editar este jugador
        if jugador_editar and jugador_editar.get("equipo") != equipo_actual:
            st.error("No puedes editar jugadores de otros equipos.")
            st.session_state["jugador_editar"] = None
            return
            
        if jugador_editar:
            st.subheader(f"Editar Jugador: {jugador_editar['nombre']}")
        else:
            st.session_state["jugador_editar"] = None
    
    if not jugador_editar:
        st.subheader("Añadir Nuevo Jugador")
    
    # Formulario para datos del jugador
    with st.form(key="jugador_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre:", value=jugador_editar['nombre'] if jugador_editar else "")
            
            # Lista de temporadas
            temporadas = ["23/24", "24/25", "25/26", "26/27", "27/28"]
            temporada_default = jugador_editar.get('temporada', "24/25") if jugador_editar else "24/25"
            temporada_index = temporadas.index(temporada_default) if temporada_default in temporadas else 1
            temporada = st.selectbox("Temporada:", temporadas, index=temporada_index)
        
        with col2:
            # Mostrar el equipo del entrenador (no seleccionable)
            st.markdown(f"**Equipo:** {equipo_actual}")
            equipo = equipo_actual  # Forzar el equipo del entrenador
            
            # Lista de posiciones
            posiciones = ["Portero", "Defensa", "Centrocampista", "Delantero"]
            posicion_default = jugador_editar.get('posicion', posiciones[0]) if jugador_editar else posiciones[0]
            posicion_index = posiciones.index(posicion_default) if posicion_default in posiciones else 0
            posicion = st.selectbox("Posición:", posiciones, index=posicion_index)
        
        # Subir foto
        st.write("Foto del jugador:")
        foto_file = st.file_uploader("Seleccionar imagen", type=["jpg", "jpeg", "png"])
        
        # Variables para control de la foto
        mantener_foto = False
        
        # Mostrar foto actual si existe
        if jugador_editar and 'foto' in jugador_editar and jugador_editar['foto']:
            foto_path = os.path.join(PLAYERS_PHOTOS_DIR, jugador_editar['foto'])
            if os.path.exists(foto_path):
                st.image(foto_path, width=200, caption="Foto actual")
                mantener_foto = st.checkbox("Mantener foto actual", value=True)
        
        # Botones de acción
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Guardar")
        
        with col2:
            if jugador_editar:
                cancel_button = st.form_submit_button("Cancelar Edición")
                if cancel_button:
                    st.session_state["jugador_editar"] = None
                    st.rerun()
    
    # Procesar el formulario
    if submit_button:
        if not nombre:
            st.error("Por favor, completa todos los campos obligatorios.")
            return
        
        # Crear ID único
        import uuid
        jugador_id = jugador_editar['id'] if jugador_editar else str(uuid.uuid4())
        
        # Procesar foto
        foto_filename = ""
        if foto_file:
            # Guardar nueva foto
            extension = foto_file.name.split(".")[-1]
            foto_filename = f"{jugador_id}.{extension}"
            foto_path = os.path.join(PLAYERS_PHOTOS_DIR, foto_filename)
            
            with open(foto_path, "wb") as f:
                f.write(foto_file.getbuffer())
            
            # Redimensionar si es necesario
            try:
                img = Image.open(foto_path)
                if img.width > 800 or img.height > 800:
                    img.thumbnail((800, 800))
                    img.save(foto_path)
            except Exception as e:
                st.error(f"Error al procesar la imagen: {e}")
        elif jugador_editar and 'foto' in jugador_editar and jugador_editar['foto'] and mantener_foto:
            # Mantener foto existente
            foto_filename = jugador_editar['foto']
        
        # Crear o actualizar jugador
        jugador = {
            "id": jugador_id,
            "nombre": nombre,
            "equipo": equipo,         # Asignar automáticamente al equipo del entrenador
            "temporada": temporada,   # Cambiado de dorsal a temporada
            "posicion": posicion,
            "foto": foto_filename,
            "fecha_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Guardar en la lista
        jugadores = cargar_jugadores()
        
        if jugador_editar:
            # Actualizar jugador existente
            jugadores = [j for j in jugadores if j['id'] != jugador_id]  # Eliminar el existente
            jugadores.append(jugador)  # Añadir el actualizado
            st.success(f"Jugador {nombre} actualizado correctamente")
            st.session_state["jugador_editar"] = None
        else:
            # Añadir nuevo jugador
            jugadores.append(jugador)
            st.success(f"Jugador {nombre} añadido correctamente")
        
        guardar_jugadores(jugadores)
        st.rerun()

# Página de plantilla
def plantilla_page():
    st.title("⚽ Plantilla del Valencia CF")
    
    # Inicializar variables de estado si no existen
    if "jugador_editar" not in st.session_state:
        st.session_state["jugador_editar"] = None
    
    # Pestañas para ver o añadir jugadores
    tab1, tab2 = st.tabs(["Ver Plantilla", "Añadir Jugador"])
    
    # Pestaña 1: Ver plantilla
    with tab1:
        mostrar_plantilla()
    
    # Pestaña 2: Añadir jugador
    with tab2:
        agregar_jugador()
        
    # Añadir un botón para volver al menú principal
    if st.button("⬅️ Volver al Menú Principal"):
        st.session_state["menu_seleccionado"] = "inicio"
        if "jugador_editar" in st.session_state:
            st.session_state["jugador_editar"] = None
        st.rerun()