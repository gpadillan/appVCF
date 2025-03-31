import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import json
import base64
from datetime import datetime
import random
import io
import plotly.io as pio
from PIL import Image as PILImage

# Importar funciones comunes de individuales.py
from modules.individuales import encontrar_jugador_plantilla, obtener_foto_jugador

# Constantes
PLAYERS_DATA_DIR = "players_data"
PLAYERS_FILE = os.path.join(PLAYERS_DATA_DIR, "players.json")
PHOTOS_DIR = os.path.join(PLAYERS_DATA_DIR, "photos")

# Colores para gráficos
COLOR_PASES_COMPLETADOS = "#43A047"    # Verde
COLOR_PASES_FALLADOS = "#E53935"       # Rojo
COLOR_TIROS_FUERA = "#FF9800"          # Naranja
COLOR_GOLES = "#FFC107"                # Amarillo
COLOR_TIROS_PUERTA = "#2196F3"         # Azul
COLOR_MINUTOS = "#2196F3"              # Azul
COLOR_RECUPERACIONES = "#673AB7"       # Morado
COLOR_PROFUNDIDAD = "#00BCD4"          # Cyan
COLOR_CARA = "#FF5722"                 # Naranja oscuro
COLOR_FALTAS = "#F44336"               # Rojo
COLOR_AREA = "#FFEB3B"                 # Amarillo claro
COLOR_PERDIDAS = "#795548"             # Marrón

# Función para obtener archivos disponibles según el usuario
def obtener_archivos_disponibles():
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
    
    return archivos_a_mostrar

# Función para obtener jugadores y partidos
def obtener_jugadores_y_partidos(archivos_a_mostrar):
    jugadores_por_archivo = {}
    all_players = set()
    fechas_partidos = {}
    
    with st.spinner("Cargando datos de partidos..."):
        for archivo_info in archivos_a_mostrar:
            ruta_archivo = archivo_info['ruta']
            nombre_archivo = archivo_info['nombre_original']
            
            try:
                # Extraer fecha del nombre del archivo (asumiendo formato: YYYY-MM-DD_Rival)
                fecha_str = nombre_archivo.split('_')[0] if '_' in nombre_archivo else None
                rival_str = nombre_archivo.split('_')[1].replace('.xlsx', '') if '_' in nombre_archivo and len(nombre_archivo.split('_')) > 1 else nombre_archivo
                
                try:
                    fecha_partido = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else None
                except:
                    fecha_partido = None
                
                # Cargar Excel
                df = pd.read_excel(ruta_archivo)
                
                # Filtrar jugadores de Valencia
                df_valencia = df[df["Team"] == "Valencia"]
                
                # Obtener jugadores únicos
                jugadores = []
                for jugador in df_valencia["Player"].unique():
                    if jugador != "Valencia" and isinstance(jugador, str) and pd.notna(jugador):
                        jugadores.append(jugador)
                        all_players.add(jugador)
                
                # Guardar jugadores de este archivo
                jugadores_por_archivo[nombre_archivo] = {
                    'jugadores': jugadores,
                    'ruta': ruta_archivo,
                    'fecha': fecha_partido,
                    'rival': rival_str
                }
                
                # Guardar fecha del partido (para ordenar)
                if fecha_partido:
                    fechas_partidos[nombre_archivo] = fecha_partido
                
            except Exception as e:
                st.error(f"Error al procesar {nombre_archivo}: {str(e)}")
    
    # Convertir set a lista y ordenar
    jugadores_unicos = sorted(list(all_players))
    
    return jugadores_unicos, jugadores_por_archivo, fechas_partidos

# Función para mostrar la tarjeta del jugador
def mostrar_tarjeta_jugador(jugador_seleccionado):
    # Buscar información del jugador en la plantilla
    info_jugador = encontrar_jugador_plantilla(jugador_seleccionado)
    
    # Extraer nombre del jugador si está en formato "#. Nombre"
    jugador_nombre = jugador_seleccionado
    if ". " in jugador_seleccionado:
        partes = jugador_seleccionado.split(". ", 1)
        if len(partes) == 2:
            jugador_nombre = partes[1]
    
    # Cabecera con información del jugador
    st.markdown("""
    <style>
        .jugador-header {
            background: linear-gradient(90deg, #012856 0%, #022142 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
        }
        .jugador-foto {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid #FF6600;
            margin-right: 20px;
        }
        .jugador-info {
            flex-grow: 1;
        }
        .jugador-nombre {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .jugador-equipo {
            font-size: 16px;
            opacity: 0.8;
            margin-bottom: 5px;
        }
        .jugador-posicion {
            background-color: #FF6600;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            display: inline-block;
            font-size: 12px;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)
    
    if info_jugador:
        # Obtener foto del jugador
        ruta_foto = obtener_foto_jugador(info_jugador.get("id"))
        if ruta_foto and os.path.exists(ruta_foto):
            with open(ruta_foto, "rb") as img_file:
                img_bytes = img_file.read()
                img_base64 = base64.b64encode(img_bytes).decode()
                foto_html = f'<img src="data:image/png;base64,{img_base64}" class="jugador-foto" alt="{info_jugador.get("nombre", "")}">'
        else:
            iniciales = "".join([n[0] for n in info_jugador.get("nombre", jugador_nombre)[0:2].upper()]) if info_jugador.get("nombre") else jugador_nombre[0:2].upper()
            foto_html = f"""
            <div class="jugador-foto" style="display: flex; align-items: center; justify-content: center; 
                background: linear-gradient(45deg, #FF6600, #FF8C40); font-size: 24px; font-weight: bold;">
                {iniciales}
            </div>
            """
        
        nombre_completo = f"{info_jugador.get('nombre', '')} {info_jugador.get('apellidos', '')}"
        posicion = info_jugador.get("posicion", "")
        
        st.markdown(f"""
        <div class="jugador-header">
            {foto_html}
            <div class="jugador-info">
                <div class="jugador-nombre">{nombre_completo}</div>
                <div class="jugador-equipo">Valencia CF</div>
                <div class="jugador-posicion">{posicion}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Determinar si es portero
        es_portero = any(palabra in posicion.lower() for palabra in ["portero", "goalkeeper", "arquero", "porter"])
    else:
        # Si no hay información en la plantilla, mostrar información básica
        jugador_numero = ""
        if ". " in jugador_seleccionado:
            partes = jugador_seleccionado.split(". ", 1)
            if len(partes) == 2:
                jugador_numero = partes[0]
                jugador_nombre = partes[1]
        
        foto_html = f"""
        <div class="jugador-foto" style="display: flex; align-items: center; justify-content: center; 
            background: linear-gradient(45deg, #FF6600, #FF8C40); font-size: 24px; font-weight: bold;">
            {jugador_numero if jugador_numero else jugador_nombre[0:2].upper()}
        </div>
        """
        
        st.markdown(f"""
        <div class="jugador-header">
            {foto_html}
            <div class="jugador-info">
                <div class="jugador-nombre">{jugador_nombre}</div>
                <div class="jugador-equipo">Valencia CF</div>
                <div class="jugador-posicion">Jugador</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        es_portero = False
    
    return jugador_nombre, es_portero, info_jugador

# Función para procesar datos de partidos
def procesar_datos_partidos(selected_matches, jugador_seleccionado, jugadores_por_archivo, jugador_nombre):
    datos_partidos = []
    
    # Mostrar progreso
    progress_bar = st.progress(0)
    
    # Acumuladores para estadísticas totales
    total_stats = {
        'minutos': 0,
        'pases_completados': 0,
        'pases_fallados': 0,
        'finalizaciones': 0,
        'goles': 0,
        'tiros_puerta': 0,
        'tiros_fuera': 0,
        'faltas': 0,
        'recuperaciones': 0,
        'profundidad': 0,
        'cara': 0,
        'area': 0,
        'paradas': 0,
        'goles_recibidos': 0,
        'tiros_recibidos_puerta': 0,
        'tiros_recibidos_fuera': 0
    }
    
    # Procesar cada partido
    for i, nombre_archivo in enumerate(selected_matches):
        info_archivo = jugadores_por_archivo[nombre_archivo]
        ruta_archivo = info_archivo['ruta']
        
        try:
            # Cargar Excel
            df = pd.read_excel(ruta_archivo)
            
            # Filtrar datos
            df_valencia = df[df["Team"] == "Valencia"]
            df_jugador = df_valencia[df_valencia["Player"] == jugador_seleccionado]
            
            if len(df_jugador) == 0:
                # Si no hay datos para este jugador en este partido, saltar
                continue
            
            # Obtener minutos jugados
            minutos_jugados = None
            # Buscar en las filas donde Jugadores y M.J contienen la información
            jugador_mj_info = df[(df["Jugadores"] == jugador_seleccionado) & pd.notna(df["M.J"])]
            if not jugador_mj_info.empty:
                # Usar el valor de M.J cuando el jugador aparece en la columna Jugadores
                minutos_jugados = int(jugador_mj_info["M.J"].iloc[0])
            else:
                # Intentar buscar con otro formato o nombre parcial
                for idx, row in df.iterrows():
                    if pd.notna(row.get("Jugadores")) and pd.notna(row.get("M.J")):
                        if jugador_nombre in str(row["Jugadores"]) or str(row["Jugadores"]) in jugador_seleccionado:
                            minutos_jugados = int(row["M.J"])
                            break
                            
            # Si no pudimos obtener M.J, calculamos una estimación
            if minutos_jugados is None:
                # Calcular minutos jugados basados en Mins
                periodos_jugados = df_jugador["Periodo"].unique()
                minutos_jugados = 0
                for periodo in periodos_jugados:
                    mins_periodo = df_jugador[df_jugador["Periodo"] == periodo]["Mins"]
                    if not mins_periodo.empty:
                        minutos_jugados += (max(mins_periodo) - min(mins_periodo) + 1)
            
            datos_partido = {
                'nombre': nombre_archivo,
                'fecha': info_archivo['fecha'],
                'rival': info_archivo['rival'],
                'minutos_jugados': minutos_jugados,
                'ruta': ruta_archivo
            }
            
            # Sumar al total
            total_stats['minutos'] += minutos_jugados
            
            # Estadísticas del portero
            df_rival = df[df["Team"] != "Valencia"]
            
            # Finalizaciones del equipo rival (para porteros)
            df_rival_finalizaciones = df_rival[df_rival["code"] == "Finalizaciones"]
            goles_recibidos = df_rival_finalizaciones[df_rival_finalizaciones["text"] == "Gol"].shape[0]
            tiros_puerta = df_rival_finalizaciones[df_rival_finalizaciones["group"] == "A puerta"].shape[0]
            tiros_fuera = df_rival_finalizaciones[df_rival_finalizaciones["group"] == "Fuera"].shape[0]
            paradas = max(0, tiros_puerta - goles_recibidos)
            
            # Estadísticas de pases
            df_pases = df_jugador[df_jugador["code"] == "Pases"]
            pases_totales = len(df_pases)
            pases_completados = df_pases["Secundary"].notna().sum()
            pases_fallados = pases_totales - pases_completados
            
            # Añadir estadísticas comunes
            datos_partido.update({
                'pases_completados': pases_completados,
                'pases_fallados': pases_fallados
            })
            
            # Actualizar totales
            total_stats['pases_completados'] += pases_completados
            total_stats['pases_fallados'] += pases_fallados
            
            # Para estadísticas de jugadores de campo
            # Finalizaciones
            df_finalizaciones = df_jugador[df_jugador["code"] == "Finalizaciones"]
            finalizaciones_totales = len(df_finalizaciones)
            
            # Goles, tiros a puerta y fuera
            goles = df_finalizaciones[df_finalizaciones["text"] == "Gol"].shape[0]
            tiros_puerta_jugador = df_finalizaciones[df_finalizaciones["group"] == "A puerta"].shape[0]
            tiros_fuera_jugador = df_finalizaciones[df_finalizaciones["group"] == "Fuera"].shape[0]
            
            # Otras estadísticas
            faltas = df_jugador[df_jugador["code"] == "Faltas"].shape[0]
            recuperaciones = df_jugador[df_jugador["code"] == "Recuperaciones"].shape[0]
            encontrar_profundidad = df_jugador[df_jugador["code"] == "Encontrar Futbolista en profundidad"].shape[0]
            encontrar_cara = df_jugador[df_jugador["code"] == "Encontrar Futbolista de cara"].shape[0]
            atacar_area = df_jugador[df_jugador["code"] == "Atacar el área"].shape[0]
            
            # Añadir todas las estadísticas al diccionario del partido
            datos_partido.update({
                'finalizaciones': finalizaciones_totales,
                'goles': goles,
                'tiros_puerta': tiros_puerta_jugador,
                'tiros_fuera': tiros_fuera_jugador,
                'faltas': faltas,
                'recuperaciones': recuperaciones,
                'profundidad': encontrar_profundidad,
                'cara': encontrar_cara,
                'area': atacar_area,
                'paradas': paradas,
                'goles_recibidos': goles_recibidos,
                'tiros_recibidos_puerta': tiros_puerta,
                'tiros_recibidos_fuera': tiros_fuera
            })
            
            # Actualizar los totales
            total_stats['finalizaciones'] += finalizaciones_totales
            total_stats['goles'] += goles
            total_stats['tiros_puerta'] += tiros_puerta_jugador
            total_stats['tiros_fuera'] += tiros_fuera_jugador
            total_stats['faltas'] += faltas
            total_stats['recuperaciones'] += recuperaciones
            total_stats['profundidad'] += encontrar_profundidad
            total_stats['cara'] += encontrar_cara
            total_stats['area'] += atacar_area
            total_stats['paradas'] += paradas
            total_stats['goles_recibidos'] += goles_recibidos
            total_stats['tiros_recibidos_puerta'] += tiros_puerta
            total_stats['tiros_recibidos_fuera'] += tiros_fuera
            
            # Añadir a la lista de datos procesados
            datos_partidos.append(datos_partido)
            
            # Actualizar barra de progreso
            progress_bar.progress((i + 1) / len(selected_matches))
            
        except Exception as e:
            st.error(f"Error al procesar {nombre_archivo}: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    # Limpiar barra de progreso
    progress_bar.empty()
    
    return datos_partidos, total_stats

# Función para mostrar métricas clave como en individuales.py
def mostrar_metricas_clave(total_stats, es_portero, num_partidos):
    st.markdown("""
    <style>
        .metricas-header {
            font-size: 18px;
            font-weight: bold;
            margin-top: 30px;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #ddd;
            padding-bottom: 10px;
        }
        .metrica-card {
            background-color: #f9f9f9;
            border-radius: 5px;
            padding: 15px;
            height: 100%;
        }
        .metrica-valor {
            font-size: 24px;
            font-weight: bold;
            color: #FF6600;
        }
        .metrica-titulo {
            font-size: 14px;
            color: #555;
            margin-bottom: 5px;
        }
        .metrica-subtexto {
            font-size: 12px;
            color: #888;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='metricas-header'>Métricas Clave</div>", unsafe_allow_html=True)
    
    # Primera fila de métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metrica-card">
            <div class="metrica-titulo">Minutos Jugados (M.J.)</div>
            <div class="metrica-valor">{}</div>
        </div>
        """.format(total_stats['minutos']), unsafe_allow_html=True)
    
    with col2:
        precision_pases = round((total_stats['pases_completados'] / (total_stats['pases_completados'] + total_stats['pases_fallados']) * 100), 1) if (total_stats['pases_completados'] + total_stats['pases_fallados']) > 0 else 0
        
        st.markdown("""
        <div class="metrica-card">
            <div class="metrica-titulo">Pases Completados</div>
            <div class="metrica-valor">{}</div>
            <div class="metrica-subtexto">{}% de precisión</div>
        </div>
        """.format(total_stats['pases_completados'], precision_pases), unsafe_allow_html=True)
    
    with col3:
        if es_portero:
            st.markdown("""
            <div class="metrica-card">
                <div class="metrica-titulo">Paradas</div>
                <div class="metrica-valor">{}</div>
                <div class="metrica-subtexto">Efectividad: {}%</div>
            </div>
            """.format(
                total_stats['paradas'], 
                round((total_stats['paradas'] / (total_stats['paradas'] + total_stats['goles_recibidos']) * 100), 1) if (total_stats['paradas'] + total_stats['goles_recibidos']) > 0 else 0
            ), unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metrica-card">
                <div class="metrica-titulo">Finalizaciones</div>
                <div class="metrica-valor">{}</div>
                <div class="metrica-subtexto">{} gol{}</div>
            </div>
            """.format(
                total_stats['finalizaciones'], 
                total_stats['goles'],
                "es" if total_stats['goles'] != 1 else ""
            ), unsafe_allow_html=True)
    
    with col4:
        # Calcular índice de rendimiento (simple)
        if es_portero:
            efectividad_paradas = (total_stats['paradas'] / (total_stats['paradas'] + total_stats['goles_recibidos']) * 100) if (total_stats['paradas'] + total_stats['goles_recibidos']) > 0 else 0
            indice = round((efectividad_paradas + precision_pases) / 20, 1)  # Escala de 0-10
        else:
            # Para jugadores de campo, considerar goles, pases y recuperaciones
            goles_por_partido = total_stats['goles'] / num_partidos if num_partidos > 0 else 0
            indice = round((precision_pases / 10) + (goles_por_partido * 2) + (total_stats['recuperaciones'] / (10 * num_partidos)), 1)
            indice = min(10.0, max(0.0, indice))  # Asegurar que esté entre 0-10
        
        st.markdown("""
        <div class="metrica-card">
            <div class="metrica-titulo">Índice Rendimiento</div>
            <div class="metrica-valor">{}</div>
        </div>
        """.format(indice), unsafe_allow_html=True)
    
    # Segunda fila de métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metrica-card">
            <div class="metrica-titulo">Pases Fallados</div>
            <div class="metrica-valor">{}</div>
        </div>
        """.format(total_stats['pases_fallados']), unsafe_allow_html=True)
    
    with col2:
        # Sumar todas las acciones de "Encontrar Futbolista"
        total_encontrar = total_stats['profundidad'] + total_stats['cara']
        
        st.markdown("""
        <div class="metrica-card">
            <div class="metrica-titulo">Encontrar Futbolista</div>
            <div class="metrica-valor">{}</div>
            <div class="metrica-subtexto">{} en profundidad</div>
        </div>
        """.format(total_encontrar, total_stats['profundidad']), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metrica-card">
            <div class="metrica-titulo">Atacar el área</div>
            <div class="metrica-valor">{}</div>
        </div>
        """.format(total_stats['area']), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metrica-card">
            <div class="metrica-titulo">Faltas Cometidas</div>
            <div class="metrica-valor">{}</div>
        </div>
        """.format(total_stats['faltas']), unsafe_allow_html=True)
    
    return precision_pases, indice

# Función para mostrar visualizaciones como en individuales.py
def mostrar_visualizaciones(total_stats, es_portero):
    st.markdown("""
    <style>
        .vis-header {
            font-size: 18px;
            font-weight: bold;
            margin-top: 30px;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #ddd;
            padding-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='vis-header'>Visualización de Rendimiento</div>", unsafe_allow_html=True)
    
    # Crear gráficos de distribución
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de distribución de pases
        pases_completados = total_stats['pases_completados']
        pases_fallados = total_stats['pases_fallados']
        total_pases = pases_completados + pases_fallados
        
        if total_pases > 0:
            precision = round((pases_completados / total_pases) * 100, 1)
            
            fig = go.Figure()
            fig.add_trace(go.Pie(
                labels=["Completados", "Fallados"],
                values=[pases_completados, pases_fallados],
                hole=0.7,
                marker=dict(colors=[COLOR_PASES_COMPLETADOS, COLOR_PASES_FALLADOS]),
                textinfo='percent',
                hoverinfo='label+value'
            ))
            
            fig.update_layout(
                title="Distribución de Pases",
                annotations=[
                    dict(
                        text=f"{precision}%<br>precisión",
                        x=0.5, y=0.5,
                        font_size=15,
                        showarrow=False
                    )
                ],
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                height=350,
                margin=dict(l=30, r=30, t=50, b=50)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Siempre mostrar finalizaciones
        goles = total_stats['goles']
        tiros_puerta = total_stats['tiros_puerta'] - goles  # Restamos goles para no contar doble
        tiros_fuera = total_stats['tiros_fuera']
        total_finalizaciones = goles + tiros_puerta + tiros_fuera
        
        if total_finalizaciones > 0:
            efectividad = round((goles / (goles + tiros_puerta)) * 100, 1) if (goles + tiros_puerta) > 0 else 0
            
            fig = go.Figure()
            fig.add_trace(go.Pie(
                labels=["Fuera", "Goles", "A puerta"],
                values=[tiros_fuera, goles, tiros_puerta],
                hole=0.7,
                marker=dict(colors=[COLOR_TIROS_FUERA, COLOR_GOLES, COLOR_TIROS_PUERTA]),
                textinfo='percent',
                hoverinfo='label+value'
            ))
            
            fig.update_layout(
                title="Finalizaciones",
                annotations=[
                    dict(
                        text=f"{efectividad}%<br>efectividad",
                        x=0.5, y=0.5,
                        font_size=15,
                        showarrow=False
                    )
                ],
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                height=350,
                margin=dict(l=30, r=30, t=50, b=50)
            )
            
            st.plotly_chart(fig, use_container_width=True)

    # Mostrar resumen de acciones con gráfico de barras
    st.markdown("<div class='vis-header'>Resumen de Acciones</div>", unsafe_allow_html=True)
    
    # Preparar datos para el gráfico de barras
    acciones = []
    valores = []
    colores = []
    
    if total_stats['minutos'] > 0:
        acciones.append('M.J.')
        valores.append(total_stats['minutos'])
        colores.append(COLOR_MINUTOS)
    
    if total_stats['pases_completados'] > 0:
        acciones.append('Pases Completados')
        valores.append(total_stats['pases_completados'])
        colores.append(COLOR_PASES_COMPLETADOS)
    
    if total_stats['profundidad'] > 0:
        acciones.append('Encontrar en profundidad')
        valores.append(total_stats['profundidad'])
        colores.append(COLOR_PROFUNDIDAD)
    
    if total_stats['recuperaciones'] > 0:
        acciones.append('Recuperaciones')
        valores.append(total_stats['recuperaciones'])
        colores.append(COLOR_RECUPERACIONES)
    
    if total_stats['area'] > 0:
        acciones.append('Atacar el área')
        valores.append(total_stats['area'])
        colores.append(COLOR_AREA)
    
    if total_stats['cara'] > 0:
        acciones.append('Encontrar de cara')
        valores.append(total_stats['cara'])
        colores.append(COLOR_CARA)
    
    if total_stats['finalizaciones'] > 0:
        acciones.append('Finalizaciones')
        valores.append(total_stats['finalizaciones'])
        colores.append(COLOR_TIROS_PUERTA)
    
    if total_stats['faltas'] > 0:
        acciones.append('Faltas')
        valores.append(total_stats['faltas'])
        colores.append(COLOR_FALTAS)
    
    if total_stats['pases_fallados'] > 0:
        acciones.append('Pases Fallados')
        valores.append(total_stats['pases_fallados'])
        colores.append(COLOR_PASES_FALLADOS)
    
    if len(acciones) > 0:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=acciones,
            y=valores,
            marker_color=colores,
            text=valores,
            textposition='auto'
        ))
        
        fig.update_layout(
            yaxis=dict(title='Cantidad'),
            xaxis=dict(title='Acción'),
            height=400,
            margin=dict(l=30, r=30, t=30, b=100)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    return {}

# Función principal que combina todo
def pagina_datos_totales():
    # 1. Obtener archivos disponibles
    archivos_a_mostrar = obtener_archivos_disponibles()
    
    # Verificar si hay archivos para mostrar
    if not archivos_a_mostrar:
        st.warning("No hay archivos disponibles para analizar. Por favor, sube algunos archivos primero.")
        if st.button("Ir a Subir Archivos"):
            st.session_state["menu_seleccionado"] = "subir_archivo"
            st.rerun()
        return
    
    # 2. Obtener jugadores y partidos
    jugadores_unicos, jugadores_por_archivo, fechas_partidos = obtener_jugadores_y_partidos(archivos_a_mostrar)
    
    # 3. Interfaz de selección - MODIFICADO para eliminar selector de número de partidos
    # Seleccionar jugador para analizar
    jugador_seleccionado = st.selectbox("Selecciona un jugador", jugadores_unicos)
    
    # Filtro para seleccionar partidos específicos
    partidos_disponibles = [nombre for nombre, info in jugadores_por_archivo.items() 
                           if jugador_seleccionado in info['jugadores']]
    
    # Ordenar partidos por fecha si está disponible
    if fechas_partidos:
        partidos_disponibles = sorted(partidos_disponibles, 
                                     key=lambda x: fechas_partidos.get(x, datetime.min.date()),
                                     reverse=True)  # Más recientes primero
    
    # Opción para seleccionar partidos específicos
    expandir_partidos = st.expander("Seleccionar partidos específicos")
    with expandir_partidos:
        selected_matches = st.multiselect(
            "Partidos",
            options=partidos_disponibles,
            default=partidos_disponibles,
            format_func=lambda x: f"{jugadores_por_archivo[x]['fecha'].strftime('%d/%m/%Y') if jugadores_por_archivo[x]['fecha'] else 'Sin fecha'} - {jugadores_por_archivo[x]['rival']}"
        )
    
    # 4. Verificar si hay partidos seleccionados
    if not selected_matches:
        st.warning(f"No hay partidos seleccionados para {jugador_seleccionado}.")
        return
    
    # 5. Mostrar tarjeta del jugador y determinar si es portero
    jugador_nombre, es_portero, info_jugador = mostrar_tarjeta_jugador(jugador_seleccionado)
    
    # 6. Procesar datos de partidos
    datos_partidos, total_stats = procesar_datos_partidos(selected_matches, jugador_seleccionado, jugadores_por_archivo, jugador_nombre)
    
    # 7. Verificar si hay datos
    if not datos_partidos:
        st.warning(f"No se encontraron datos para {jugador_seleccionado} en los partidos seleccionados.")
        return
    
    # 8. Ordenar partidos por fecha
    datos_partidos = sorted(datos_partidos, key=lambda x: x['fecha'] if x['fecha'] else datetime.min.date())
    
    # 9. Mostrar métricas clave estilo individuales.py
    precision_pases, indice_rendimiento = mostrar_metricas_clave(total_stats, es_portero, len(datos_partidos))
    
    # 10. Mostrar visualizaciones estilo individuales.py
    mostrar_visualizaciones(total_stats, es_portero)
    
    # 11. Mostrar información sobre los partidos analizados
    partidos_info = [f"{p['fecha'].strftime('%d/%m/%Y') if p['fecha'] else 'Sin fecha'} vs {p['rival']}" for p in datos_partidos]
    st.markdown(f"""
    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-top: 20px; font-size: 13px;">
        <b>Datos acumulados de {len(datos_partidos)} partidos:</b> {', '.join(partidos_info)}
    </div>
    """, unsafe_allow_html=True)
    
    # 12. Botón para volver atrás
    if st.button("⬅️ Volver al Menú Principal", key="volver_btn"):
        st.session_state["menu_seleccionado"] = "inicio"
        st.rerun()