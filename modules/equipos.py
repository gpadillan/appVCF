import streamlit as st
import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import base64

# Constantes
EQUIPOS_DATA_DIR = "equipos_data"
EQUIPOS_FILE = os.path.join(EQUIPOS_DATA_DIR, "equipos.json")
ASSETS_DIR = "assets"
ESCUDO_PATH = os.path.join(ASSETS_DIR, "valencia.png")  # Ruta al escudo

# Crear directorio si no existe
os.makedirs(EQUIPOS_DATA_DIR, exist_ok=True)

# Función para obtener imagen en base64
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# Función para cargar datos de equipos
def cargar_equipos():
    if not os.path.exists(EQUIPOS_FILE):
        # Crear una estructura inicial
        equipos_iniciales = {
            "Infantil": [
                {"nombre": "Infantil A", "categoria": "Infantil", "entrenador": "Entrenador IA", "num_jugadores": 18},
                {"nombre": "Infantil B", "categoria": "Infantil", "entrenador": "Entrenador IB", "num_jugadores": 18}
            ],
            "Cadete": [
                {"nombre": "Cadete A", "categoria": "Cadete", "entrenador": "Entrenador CA", "num_jugadores": 20},
                {"nombre": "Cadete B", "categoria": "Cadete", "entrenador": "Entrenador CB", "num_jugadores": 20}
            ],
            "Juvenil": [
                {"nombre": "Juvenil A", "categoria": "Juvenil", "entrenador": "Entrenador JA", "num_jugadores": 22},
                {"nombre": "Juvenil B", "categoria": "Juvenil", "entrenador": "Entrenador JB", "num_jugadores": 22}
            ],
            "Senior": [
                {"nombre": "Valencia Mestalla", "categoria": "Senior", "entrenador": "Entrenador VM", "num_jugadores": 24}
            ]
        }
        with open(EQUIPOS_FILE, 'w') as f:
            json.dump(equipos_iniciales, f)
        return equipos_iniciales
    
    try:
        with open(EQUIPOS_FILE, 'r') as f:
            return json.load(f)
    except:
        # En caso de error, devolver estructura vacía
        return {"Infantil": [], "Cadete": [], "Juvenil": [], "Senior": []}

# Función para procesar estadísticas de un equipo desde los archivos Excel
def procesar_estadisticas_equipo(equipo_nombre):
    # Buscar archivos de este equipo
    archivos_equipo = [a for a in st.session_state.archivos_subidos if a.get('equipo') == equipo_nombre]
    
    if not archivos_equipo:
        return None, 0
    
    # Inicializar estadísticas
    estadisticas = {
        "goles_favor": 0,
        "goles_contra": 0,
        "faltas_realizadas": 0,
        "faltas_recibidas": 0,
        "tiros_puerta": 0,
        "tiros_fuera": 0,
        "corners_favor": 0,
        "corners_contra": 0,
        "pases_completados": 0,
        "pases_fallados": 0
    }
    
    # Procesar cada archivo
    for archivo in archivos_equipo:
        try:
            # Cargar Excel
            df = pd.read_excel(archivo['ruta'])
            
            # Mostrar las primeras filas del DataFrame para depuración
            st.write(f"Analizando archivo: {archivo['nombre_original']}")
            
            # Filtrar datos del Valencia y del rival
            df_valencia = df[df["Team"] == "Valencia"]
            df_rival = df[df["Team"] != "Valencia"]
            
            # Contar finalizaciones y goles
            df_fin_valencia = df_valencia[df_valencia["code"] == "Finalizaciones"]
            df_fin_rival = df_rival[df_rival["code"] == "Finalizaciones"]
            
            # Goles
            estadisticas["goles_favor"] += df_fin_valencia[df_fin_valencia["text"] == "Gol"].shape[0]
            estadisticas["goles_contra"] += df_fin_rival[df_fin_rival["text"] == "Gol"].shape[0]
            
            # Tiros
            estadisticas["tiros_puerta"] += df_fin_valencia[df_fin_valencia["group"] == "A puerta"].shape[0]
            estadisticas["tiros_fuera"] += df_fin_valencia[df_fin_valencia["group"] == "Fuera"].shape[0]
            
            # Faltas
            estadisticas["faltas_realizadas"] += df_valencia[df_valencia["code"] == "Faltas"].shape[0]
            estadisticas["faltas_recibidas"] += df_rival[df_rival["code"] == "Faltas"].shape[0]
            
            # Corners - Buscando en code="Est.Generales" y group="Saque de esquina"
            df_corners_valencia = df_valencia[
                (df_valencia["code"] == "Est.Generales") & 
                (df_valencia["group"] == "Saque de esquina")
            ]
            df_corners_rival = df_rival[
                (df_rival["code"] == "Est.Generales") & 
                (df_rival["group"] == "Saque de esquina")
            ]
            
            estadisticas["corners_favor"] += len(df_corners_valencia)
            estadisticas["corners_contra"] += len(df_corners_rival)
            
            # Pases
            df_pases = df_valencia[df_valencia["code"] == "Pases"]
            estadisticas["pases_completados"] += df_pases["Secundary"].notna().sum()
            estadisticas["pases_fallados"] += df_pases["Secundary"].isna().sum()
            
        except Exception as e:
            st.error(f"Error al procesar archivo {archivo['nombre_original']}: {str(e)}")
            import traceback
            st.text(traceback.format_exc())
    
    return estadisticas, len(archivos_equipo)

# Función para mostrar estadísticas de un equipo
def mostrar_estadisticas_equipo(equipo_nombre, estadisticas, num_partidos):
    st.subheader(f"Estadísticas de {equipo_nombre}")
    st.write(f"Datos acumulados de {num_partidos} partidos")
    
    # Crear gráfico de barras con las estadísticas (sin amarillas y con corners separados)
    categorias = [
        "Goles a favor", "Goles en contra", 
        "Faltas realizadas", "Faltas recibidas", 
        "Tiros a puerta", "Tiros fuera", 
        "Corners a favor", "Corners en contra"
    ]
    
    valores = [
        estadisticas["goles_favor"], estadisticas["goles_contra"], 
        estadisticas["faltas_realizadas"], estadisticas["faltas_recibidas"], 
        estadisticas["tiros_puerta"], estadisticas["tiros_fuera"], 
        estadisticas["corners_favor"], estadisticas["corners_contra"]
    ]
    
    # Colores personalizados para cada categoría
    colores = [
        "#4CAF50", "#F44336", 
        "#FF9800", "#2196F3", 
        "#3F51B5", "#9C27B0", 
        "#009688", "#795548"
    ]
    
    # Crear gráfico de barras interactivo
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=categorias,
        y=valores,
        marker_color=colores,
        text=valores,
        textposition='outside'
    ))
    
    fig.update_layout(
        title={
            'text': f"Estadísticas acumuladas de {num_partidos} partidos",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 18, 'color': '#1a5276'}
        },
        xaxis={'title': '', 'tickangle': -45},
        yaxis={'title': 'Cantidad'},
        plot_bgcolor='white',
        hoverlabel=dict(bgcolor="white", font_size=12),
        height=450,
        margin=dict(l=50, r=50, t=80, b=100)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Métricas clave
    st.subheader("Métricas clave")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Partidos analizados", 
            value=num_partidos
        )
    
    with col2:
        promedio_goles = round(estadisticas["goles_favor"] / num_partidos, 1) if num_partidos > 0 else 0
        st.metric(
            label="Promedio goles", 
            value=promedio_goles
        )
    
    with col3:
        # Efectividad de tiros
        total_tiros = estadisticas["tiros_puerta"] + estadisticas["tiros_fuera"]
        efectividad = round((estadisticas["tiros_puerta"] / total_tiros * 100), 1) if total_tiros > 0 else 0
        st.metric(
            label="Efectividad tiros", 
            value=f"{efectividad}%"
        )
    
    with col4:
        # Diferencia de goles
        st.metric(
            label="Diferencia goles", 
            value=estadisticas["goles_favor"] - estadisticas["goles_contra"],
            delta=estadisticas["goles_favor"] - estadisticas["goles_contra"]
        )
    
    # Gráfico de distribución de pases
    if estadisticas["pases_completados"] + estadisticas["pases_fallados"] > 0:
        st.subheader("Distribución de pases")
        porcentaje_completados = round((estadisticas["pases_completados"] / (estadisticas["pases_completados"] + estadisticas["pases_fallados"]) * 100), 1)
        
        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=["Pases Completados", "Pases Fallados"],
            values=[estadisticas["pases_completados"], estadisticas["pases_fallados"]],
            hole=0.6,
            marker=dict(colors=['#4CAF50', '#E57373']),
            textinfo='percent',
            hoverinfo='label+value',
            textfont_size=14
        ))
        
        fig.update_layout(
            annotations=[dict(
                text=f"{porcentaje_completados}%<br>precisión",
                x=0.5, y=0.5,
                font_size=15,
                showarrow=False
            )],
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            height=350,
            margin=dict(l=30, r=30, t=30, b=50)
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Función para mostrar el navegador de equipos
def mostrar_navegador_equipos():
    st.title("📊 Navegador de Equipos")
    
    # Verificar si estamos viendo un equipo específico
    if "ver_equipo" in st.session_state and st.session_state["ver_equipo"]:
        equipo_nombre = st.session_state.get("equipo_seleccionado", "")
        if equipo_nombre:
            # Procesar estadísticas del equipo
            estadisticas, num_partidos = procesar_estadisticas_equipo(equipo_nombre)
            
            # Botón para volver
            if st.button("⬅️ Volver al navegador de equipos", use_container_width=True):
                st.session_state["ver_equipo"] = False
                st.rerun()
            
            if not estadisticas or num_partidos == 0:
                st.warning(f"No hay archivos disponibles para {equipo_nombre}. Sube algunos archivos para ver estadísticas.")
                return
            
            # Mostrar estadísticas
            mostrar_estadisticas_equipo(equipo_nombre, estadisticas, num_partidos)
            return
    
    # Estilos CSS personalizados para las tarjetas de equipo
    st.markdown("""
    <style>
    .equipo-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 20px;
        transition: transform 0.3s;
        cursor: pointer;
    }
    .equipo-card:hover {
        transform: translateY(-5px);
        box-shadow: 0px 6px 12px rgba(0, 0, 0, 0.15);
    }
    .equipo-escudo {
        width: 80px;
        height: 80px;
        margin: 0 auto 15px auto;
    }
    .equipo-nombre {
        font-size: 18px;
        font-weight: bold;
        color: #FF6600;
        margin-bottom: 5px;
    }
    .equipo-info {
        font-size: 14px;
        color: #666;
    }
    .categoria-header {
        background-color: #FF6600;
        color: white;
        padding: 10px;
        border-radius: 10px;
        margin: 20px 0;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Cargar escudo
    escudo_base64 = None
    if os.path.exists(ESCUDO_PATH):
        escudo_base64 = get_image_base64(ESCUDO_PATH)
    
    # Cargar datos de equipos
    equipos = cargar_equipos()
    
    # Mostrar equipos por categoría
    for categoria, lista_equipos in equipos.items():
        if lista_equipos:  # Solo mostrar categorías con equipos
            # Título de la categoría
            st.markdown(f"""
            <div class="categoria-header">
                {categoria}
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar equipos en filas de 3
            num_equipos = len(lista_equipos)
            
            # Dividir en filas de 3 equipos
            for i in range(0, num_equipos, 3):
                cols = st.columns(3)
                
                # Procesar los equipos de esta fila
                for j in range(min(3, num_equipos - i)):
                    equipo = lista_equipos[i + j]
                    with cols[j]:
                        escudo_html = ""
                        if escudo_base64:
                            escudo_html = f'<img src="data:image/png;base64,{escudo_base64}" class="equipo-escudo" alt="Escudo Valencia CF">'
                        
                        # Hacer que el contenedor sea un botón
                        equipo_card = f"""
                        <div class="equipo-card">
                            {escudo_html}
                            <div class="equipo-nombre">{equipo['nombre']}</div>
                            <div class="equipo-info">Categoría: {equipo['categoria']}</div>
                            <div class="equipo-info">Entrenador: {equipo['entrenador']}</div>
                            <div class="equipo-info">Jugadores: {equipo['num_jugadores']}</div>
                        </div>
                        """
                        
                        # Crear un botón con la misma apariencia que la tarjeta
                        if st.button(equipo['nombre'], key=f"btn_{equipo['nombre']}", use_container_width=True):
                            st.session_state["equipo_seleccionado"] = equipo['nombre']
                            st.session_state["ver_equipo"] = True
                            st.rerun()
                        
                        # Mostrar la tarjeta (sin funcionalidad de clic, ya que usamos el botón)
                        st.markdown(equipo_card, unsafe_allow_html=True)

# Función para mostrar el panel de un equipo (para mantener compatibilidad con vcf_app.py)
def mostrar_panel_equipo():
    if "equipo_seleccionado" not in st.session_state:
        st.warning("No hay equipo seleccionado.")
        if st.button("Volver al navegador"):
            if "ver_panel_equipo" in st.session_state:
                del st.session_state["ver_panel_equipo"]
            st.rerun()
        return
    
    equipo_nombre = st.session_state["equipo_seleccionado"]
    
    # Procesar y mostrar estadísticas
    estadisticas, num_partidos = procesar_estadisticas_equipo(equipo_nombre)
    
    if not estadisticas or num_partidos == 0:
        st.warning(f"No hay archivos disponibles para {equipo_nombre}. Sube algunos archivos para ver estadísticas.")
    else:
        mostrar_estadisticas_equipo(equipo_nombre, estadisticas, num_partidos)
    
    # Botón para volver
    if st.button("⬅️ Volver al navegador de equipos", use_container_width=True):
        if "ver_panel_equipo" in st.session_state:
            del st.session_state["ver_panel_equipo"]
        if "equipo_seleccionado" in st.session_state:
            del st.session_state["equipo_seleccionado"]
        st.rerun()