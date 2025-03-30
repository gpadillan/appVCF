import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import json
import base64
from mplsoccer import Pitch
import matplotlib.pyplot as plt
# Nuevas importaciones para PDF
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import plotly.io as pio
from PIL import Image as PILImage
# Importaciones para HTML/PDF
from jinja2 import Template
import weasyprint
import tempfile
from datetime import datetime

# Constantes
PLAYERS_DATA_DIR = "players_data"
PLAYERS_FILE = os.path.join(PLAYERS_DATA_DIR, "players.json")
PHOTOS_DIR = os.path.join(PLAYERS_DATA_DIR, "photos")

# Función para cargar datos de jugadores de la plantilla
def cargar_jugadores_plantilla():
    if not os.path.exists(PLAYERS_FILE):
        return []
    
    try:
        with open(PLAYERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

# Función para encontrar jugador en la plantilla por nombre
def encontrar_jugador_plantilla(nombre_completo):
    jugadores = cargar_jugadores_plantilla()
    
    # Eliminar número del nombre si está en formato "10. Jaume"
    nombre_buscar = nombre_completo
    if ". " in nombre_completo:
        nombre_buscar = nombre_completo.split(". ", 1)[1]
    
    # Debug para ver qué estamos buscando
    print(f"Buscando: {nombre_buscar}")
    
    # 1. Buscar por coincidencia exacta
    for jugador in jugadores:
        nombre_jugador = jugador.get("nombre", "").lower()
        if nombre_jugador == nombre_buscar.lower():
            print(f"Coincidencia exacta: {jugador}")
            return jugador
    
    # 2. Buscar coincidencia parcial pero más estricta
    # Comparar si el nombre del jugador está completo en el nombre de búsqueda o viceversa
    # (esto evita coincidencias de substrings pequeños)
    for jugador in jugadores:
        nombre_jugador = jugador.get("nombre", "").lower()
        apellido_jugador = jugador.get("apellidos", "").lower() if jugador.get("apellidos") else ""
        nombre_completo_jugador = f"{nombre_jugador} {apellido_jugador}".strip().lower()
        
        # Coincidencia si el nombre completo a buscar contiene el nombre completo del jugador
        if nombre_completo_jugador and (nombre_completo_jugador in nombre_buscar.lower() or 
                                        nombre_buscar.lower() in nombre_completo_jugador):
            if len(nombre_completo_jugador) > 3:  # Evitar coincidencias con nombres muy cortos
                print(f"Coincidencia parcial: {jugador}")
                return jugador
    
    print(f"No se encontró ninguna coincidencia para: {nombre_buscar}")
    return None

# Función para obtener la foto de un jugador - VERSION MEJORADA
def obtener_foto_jugador(jugador_id):
    """
    Busca la foto de un jugador, primero por ID y luego por nombre si no la encuentra.
    """
    # Primero intenta buscar por ID (el método original)
    for ext in ['jpg', 'jpeg', 'png']:
        ruta_foto = os.path.join(PHOTOS_DIR, f"{jugador_id}.{ext}")
        if os.path.exists(ruta_foto):
            return ruta_foto
    
    # Si no la encuentra, busca el nombre del jugador en la lista de jugadores
    jugadores = cargar_jugadores_plantilla()
    for jugador in jugadores:
        if jugador['id'] == jugador_id and 'nombre' in jugador:
            # Buscar por nombre
            nombre = jugador['nombre']
            for ext in ['jpg', 'jpeg', 'png']:
                ruta_foto = os.path.join(PHOTOS_DIR, f"{nombre}.{ext}")
                if os.path.exists(ruta_foto):
                    return ruta_foto
    
    return None

# Función para visualizar los pases en el campo
def visualizar_pases_campo(df_jugador):
    """
    Crea una visualización del terreno de juego mostrando los pases del jugador.
    - Pases buenos (completados): con línea del origen al destino en rojo
    - Pases malos (fallidos): con línea del origen al destino en negro
    
    Args:
        df_jugador: DataFrame con las acciones del jugador seleccionado
    """
    # Filtrar solo los pases
    df_pases = df_jugador[df_jugador["code"] == "Pases"].copy()
    
    if df_pases.empty:
        st.warning("No hay datos de pases disponibles para visualizar en el campo.")
        return
    
    # Definir función de conversión localmente para evitar errores
    def convertir_coordenadas_local(x, y):
        """
        Convierte coordenadas originales (ej. 240x150) a (120x80),
        reflejando eje Y.
        """
        x_scale = 120 / 240
        y_scale = 80 / 150
        x_offset = -5
        y_offset = -5.333

        x_new = (x + x_offset) * x_scale
        y_new = (y + y_offset) * y_scale
        y_new = 80 - y_new  # Invertimos Y

        return x_new, y_new
    
    # Crear columnas de coordenadas convertidas usando la función local
    df_pases["startX_conv"], df_pases["startY_conv"] = zip(*df_pases.apply(
        lambda row: convertir_coordenadas_local(row["startX"], row["startY"]), axis=1
    ))
    
    # Para TODOS los pases convertimos coordenadas de destino
    df_pases["endX_conv"], df_pases["endY_conv"] = zip(*df_pases.apply(
        lambda row: convertir_coordenadas_local(row["endX"], row["endY"]), axis=1
    ))
    
    # Separar pases completados y fallidos
    pases_completados = df_pases[df_pases["Secundary"].notna()]
    pases_fallidos = df_pases[df_pases["Secundary"].isna()]
    
    # Dibujar el campo
    pitch = Pitch(
        pitch_type="custom",
        pitch_length=120,
        pitch_width=80,
        line_color="black",
        pitch_color="#d0f0c0",
        linewidth=2
    )
    fig, ax = pitch.draw(figsize=(16, 11))
    
    # Franjas horizontales
    franja_altura = 80 / 5
    for i in range(5):
        if i % 2 == 0:
            ax.fill_between([0, 120], i * franja_altura, (i + 1) * franja_altura, color="#a0c080", alpha=0.7)
    
    fig.set_facecolor("white")
    
    # Dibujar pases completados (con líneas rojas)
    for _, pase in pases_completados.iterrows():
        # Línea del pase
        ax.plot(
            [pase["startX_conv"], pase["endX_conv"]],
            [pase["startY_conv"], pase["endY_conv"]],
            color="red", lw=2, alpha=0.7, zorder=1
        )
        
        # Punto de origen
        ax.scatter(
            pase["startX_conv"], pase["startY_conv"],
            color="black", s=100, edgecolors="red", marker="o", zorder=2
        )
        
        # Punto de destino
        ax.scatter(
            pase["endX_conv"], pase["endY_conv"],
            color="black", s=100, edgecolors="red", marker="o", zorder=2
        )
    
    # Dibujar pases fallidos (también con líneas pero en negro)
    for _, pase in pases_fallidos.iterrows():
        # Línea del pase
        ax.plot(
            [pase["startX_conv"], pase["endX_conv"]],
            [pase["startY_conv"], pase["endY_conv"]],
            color="black", lw=2, alpha=0.7, zorder=1
        )
        
        # Punto de origen
        ax.scatter(
            pase["startX_conv"], pase["startY_conv"],
            color="white", s=100, edgecolors="black", marker="o", zorder=2
        )
        
        # Punto de destino
        ax.scatter(
            pase["endX_conv"], pase["endY_conv"],
            color="white", s=100, edgecolors="black", marker="o", zorder=2
        )
    
    # Agregar leyenda
    from matplotlib.lines import Line2D
    leyenda_elementos = [
        Line2D([0], [0], marker='o', color='red', linestyle='-', 
               markerfacecolor='black', markeredgecolor='red', 
               markersize=10, label='Pase completado'),
        Line2D([0], [0], marker='o', color='black', linestyle='-', 
               markerfacecolor='white', markeredgecolor='black', 
               markersize=10, label='Pase fallido')
    ]
    ax.legend(handles=leyenda_elementos, loc='upper right', fontsize=10)
    
    # Añadir título
    plt.suptitle("Visualización de Pases en el Campo", color="black", fontsize=20)
    
    # Añadir información sobre total de pases
    total_completados = len(pases_completados)
    total_fallidos = len(pases_fallidos)
    precision = (total_completados / (total_completados + total_fallidos) * 100) if (total_completados + total_fallidos) > 0 else 0
    
    # Agregar texto con estadísticas
    stats_text = f"Pases completados: {total_completados} ({precision:.1f}%)\nPases fallidos: {total_fallidos}"
    plt.figtext(0.5, 0.01, stats_text, ha="center", fontsize=12, bbox=dict(facecolor='white', alpha=0.8, edgecolor='black'))
    
    st.pyplot(fig)
    
    # Para capturar este gráfico para el PDF, guardarlo en un buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')  # Retornamos el gráfico en base64

def dibujar_campo_futbol(fig):
    """
    Añade las líneas de un campo de fútbol a una figura de Plotly
    
    Args:
        fig: Objeto figura de Plotly
    """
    # Dimensiones del campo normalizadas (120x80)
    ancho_campo = 120
    alto_campo = 80
    
    # Color del césped y líneas
    color_campo = '#d0f0c0'
    color_lineas = 'black'
    
    # Dibujar el campo de fútbol
    # 1. Fondo del campo (césped)
    fig.add_shape(
        type="rect",
        x0=0, y0=0, 
        x1=ancho_campo, y1=alto_campo,
        fillcolor=color_campo,
        line_color=color_lineas,
        line_width=2
    )
    
    # 2. Franjas horizontales
    franja_altura = alto_campo / 5
    for i in range(5):
        if i % 2 == 0:
            fig.add_shape(
                type="rect",
                x0=0, y0=i * franja_altura, 
                x1=ancho_campo, y1=(i + 1) * franja_altura,
                fillcolor="#a0c080",
                opacity=0.7,
                line_width=0
            )
    
    # 3. Línea central
    fig.add_shape(
        type="line",
        x0=ancho_campo/2, y0=0, 
        x1=ancho_campo/2, y1=alto_campo,
        line_color=color_lineas,
        line_width=2
    )
    
    # 4. Círculo central
    fig.add_shape(
        type="circle",
        x0=ancho_campo/2-10, y0=alto_campo/2-10, 
        x1=ancho_campo/2+10, y1=alto_campo/2+10,
        line_color=color_lineas,
        line_width=2,
        fillcolor='rgba(0,0,0,0)'
    )
    
    # 5. Áreas de portería izquierda
    fig.add_shape(
        type="rect",
        x0=0, y0=alto_campo/2-20, 
        x1=16, y1=alto_campo/2+20,
        line_color=color_lineas,
        line_width=2,
        fillcolor='rgba(0,0,0,0)'
    )
    
    fig.add_shape(
        type="rect",
        x0=0, y0=alto_campo/2-10, 
        x1=5, y1=alto_campo/2+10,
        line_color=color_lineas,
        line_width=2,
        fillcolor='rgba(0,0,0,0)'
    )
    
    # 6. Áreas de portería derecha
    fig.add_shape(
        type="rect",
        x0=ancho_campo-16, y0=alto_campo/2-20, 
        x1=ancho_campo, y1=alto_campo/2+20,
        line_color=color_lineas,
        line_width=2,
        fillcolor='rgba(0,0,0,0)'
    )
    
    fig.add_shape(
        type="rect",
        x0=ancho_campo-5, y0=alto_campo/2-10, 
        x1=ancho_campo, y1=alto_campo/2+10,
        line_color=color_lineas,
        line_width=2,
        fillcolor='rgba(0,0,0,0)'
    )
    
    # Configurar ejes para que el campo se vea correctamente
    fig.update_xaxes(
        range=[0, ancho_campo],
        showgrid=False,
        zeroline=False,
        showticklabels=False,
        fixedrange=True,
        scaleratio=1
    )
    
    fig.update_yaxes(
        range=[0, alto_campo],
        showgrid=False,
        zeroline=False,
        showticklabels=False,
        fixedrange=True,
        scaleratio=1
    )

# Función para convertir las coordenadas (asegurando que esta función esté disponible)
def convertir_coordenadas_reflejado(x, y):
    """
    Convierte coordenadas originales (ej. 240x150) a (120x80),
    reflejando eje Y.
    """
    x_scale = 120 / 240
    y_scale = 80 / 150
    x_offset = -5
    y_offset = -5.333

    x_new = (x + x_offset) * x_scale
    y_new = (y + y_offset) * y_scale
    y_new = 80 - y_new  # Invertimos Y

    return x_new, y_new

# Función para mostrar estadísticas de portero
def mostrar_estadisticas_portero(df, df_jugador, jugador_seleccionado, info_jugador, minutos_jugados):
    """
    Muestra estadísticas específicas para porteros, incluyendo paradas, goles recibidos, etc.
    """
    st.markdown('<div class="section-header">Estadísticas del Portero</div>', unsafe_allow_html=True)
    
    # Encontrar datos del rival
    df_rival = None
    equipo_rival_nombre = None
    
    # Buscar el equipo rival en el DataFrame
    equipos_unicos = df["Team"].unique().tolist()
    for equipo in equipos_unicos:
        if equipo != "Valencia" and isinstance(equipo, str):
            equipo_rival_nombre = equipo
            df_rival = df[df["Team"] == equipo]
            break
    
    if df_rival is None or df_rival.empty:
        st.warning("No se encontraron datos del equipo rival para analizar el rendimiento del portero.")
        return
    
    # Finalizaciones del equipo rival
    df_rival_finalizaciones = df_rival[df_rival["code"] == "Finalizaciones"]
    finalizaciones_totales = len(df_rival_finalizaciones)
    
    # Goles recibidos
    goles_recibidos = df_rival_finalizaciones[df_rival_finalizaciones["text"] == "Gol"].shape[0]
    
    # Tiros a puerta y fuera
    tiros_puerta = df_rival_finalizaciones[df_rival_finalizaciones["group"] == "A puerta"].shape[0]
    tiros_fuera = df_rival_finalizaciones[df_rival_finalizaciones["group"] == "Fuera"].shape[0]
    
    # Paradas (tiros a puerta - goles)
    paradas = max(0, tiros_puerta - goles_recibidos)
    
    # Porcentaje de paradas
    porcentaje_paradas = round((paradas / tiros_puerta * 100), 1) if tiros_puerta > 0 else 0
    
    # Estadísticas del portero en pases
    df_pases = df_jugador[df_jugador["code"] == "Pases"]
    pases_totales = len(df_pases)
    pases_completados = df_pases["Secundary"].notna().sum()
    pases_fallados = pases_totales - pases_completados
    precision_pases = round((pases_completados / pases_totales * 100), 1) if pases_totales > 0 else 0
    
    # Métricas clave
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">Minutos Jugados (M.J.)</div>
            <div class="metric-value">{minutos_jugados}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">Paradas</div>
            <div class="metric-value">{paradas}</div>
            <div style="font-size: 14px;">{porcentaje_paradas:.1f}% de efectividad</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">Goles Recibidos</div>
            <div class="metric-value">{goles_recibidos}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Índice de rendimiento para porteros
        indice_rendimiento = (
            paradas * 0.3 +
            (porcentaje_paradas * 0.05) -
            (goles_recibidos * 0.5) +
            (precision_pases * 0.01)
        )
        
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">Índice Rendimiento</div>
            <div class="metric-value">{indice_rendimiento:.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Segunda fila de métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">Tiros a Puerta Recibidos</div>
            <div class="metric-value">{tiros_puerta}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">Tiros Fuera Recibidos</div>
            <div class="metric-value">{tiros_fuera}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">Pases Completados</div>
            <div class="metric-value">{pases_completados}</div>
            <div style="font-size: 14px;">{precision_pases:.1f}% de precisión</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">Pases Fallados</div>
            <div class="metric-value">{pases_fallados}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Área de visualización
    st.markdown('<div class="section-header">Visualización de Rendimiento</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    charts = {}  # Diccionario para almacenar gráficos para el PDF
    
    with col1:
        # Gráfico de distribución de tiros recibidos
        if finalizaciones_totales > 0:
            fig_tiros = go.Figure()
            
            # Colores para diferentes tipos de tiros
            colores_tiros = ['#4CAF50', '#F44336', '#FF9800']
            
            # Valores para paradas, goles y tiros fuera
            valores_tiros = [paradas, goles_recibidos, tiros_fuera]
            etiquetas_tiros = ['Paradas', 'Goles Recibidos', 'Tiros Fuera']
            
            fig_tiros.add_trace(go.Pie(
                labels=etiquetas_tiros,
                values=valores_tiros,
                hole=0.6,
                marker=dict(colors=colores_tiros),
                textinfo='percent+value',
                insidetextorientation='radial',
                pull=[0.1, 0, 0]
            ))
            
            fig_tiros.update_layout(
                annotations=[dict(
                    text=f"{porcentaje_paradas:.1f}%<br>paradas",
                    x=0.5, y=0.5,
                    font_size=15,
                    showarrow=False
                )],
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                height=350,
                margin=dict(l=20, r=20, t=60, b=20),
                paper_bgcolor='white',
                plot_bgcolor='white'
            )
            
            st.plotly_chart(fig_tiros, use_container_width=True)
            
            # Capturar gráfico para PDF
            try:
                charts['tiros_chart'] = capturar_graficos_plotly(fig_tiros)
            except Exception as e:
                st.warning(f"No se pudo capturar el gráfico de tiros: {str(e)}")
        else:
            st.info("No hay datos de tiros recibidos disponibles para este portero.")
    
    with col2:
        # Gráfico de distribución de pases
        if pases_totales > 0:
            fig_pases = go.Figure()
            fig_pases.add_trace(go.Pie(
                labels=['Completados', 'Fallados'],
                values=[pases_completados, pases_fallados],
                hole=0.6,
                marker=dict(colors=['#4CAF50', '#E57373']),
                textinfo='percent+value',
                insidetextorientation='radial',
                pull=[0.05, 0],
                rotation=90
            ))
            
            fig_pases.update_layout(
                annotations=[dict(
                    text=f"{precision_pases:.1f}%<br>precisión",
                    x=0.5, y=0.5,
                    font_size=15,
                    showarrow=False
                )],
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                ),
                margin=dict(l=20, r=20, t=60, b=20),
                paper_bgcolor='white',
                plot_bgcolor='white'
            )
            
            st.plotly_chart(fig_pases, use_container_width=True)
            
            # Capturar gráfico para PDF
            try:
                charts['distribucion_pases'] = capturar_graficos_plotly(fig_pases)
            except Exception as e:
                st.warning(f"No se pudo capturar el gráfico de distribución de pases: {str(e)}")
        else:
            st.info("No hay datos de pases disponibles para este portero.")
    
    # Gráfico de barras de resumen
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    # Crear un dataframe para el gráfico de barras
    tipos_acciones = {
        'M.J.': minutos_jugados,
        'Paradas': paradas,
        'Goles Recibidos': goles_recibidos,
        'Tiros a Puerta Recibidos': tiros_puerta,
        'Tiros Fuera Recibidos': tiros_fuera,
        'Pases Completados': pases_completados,
        'Pases Fallados': pases_fallados
    }
    
    df_acciones = pd.DataFrame({
        'Tipo': list(tipos_acciones.keys()),
        'Cantidad': list(tipos_acciones.values())
    })
    
    # Ordenar por cantidad (descendente)
    df_acciones = df_acciones.sort_values('Cantidad', ascending=False)
    
    # Asignar colores según tipo de acción
    colores_acciones = {
        'M.J.': '#1E88E5',
        'Paradas': '#4CAF50',
        'Goles Recibidos': '#F44336',
        'Tiros a Puerta Recibidos': '#2196F3',
        'Tiros Fuera Recibidos': '#FF9800',
        'Pases Completados': '#00BCD4',
        'Pases Fallados': '#E57373'
    }
    
    colores_barras = [colores_acciones.get(tipo, '#757575') for tipo in df_acciones['Tipo']]
    
    # Crear gráfico de barras con estilo profesional
    fig_acciones = go.Figure()
    
    fig_acciones.add_trace(go.Bar(
        x=df_acciones['Tipo'],
        y=df_acciones['Cantidad'],
        marker_color=colores_barras,
        text=df_acciones['Cantidad'],
        textposition='auto'
    ))
    
    fig_acciones.update_layout(
        xaxis=dict(
            title='',
            tickangle=-45,
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            title='',
            gridcolor='#eee',
            zerolinecolor='#eee'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=450,
        margin=dict(l=40, r=40, t=60, b=80)
    )
    
    st.plotly_chart(fig_acciones, use_container_width=True)
    
    # Capturar gráfico para PDF
    try:
        charts['resumen_acciones'] = capturar_graficos_plotly(fig_acciones)
    except Exception as e:
        st.warning(f"No se pudo capturar el gráfico de resumen: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Nueva sección: Visualización de pases en el campo
    st.markdown('<div class="section-header">Mapa de Pases en el Campo</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    # Llamar a la función que visualiza los pases en el campo
    mapa_pases_base64 = visualizar_pases_campo(df_jugador)
    
    # Guardar imagen para PDF
    if mapa_pases_base64:
        charts['mapa_pases'] = mapa_pases_base64
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tabla de finalizaciones del rival
    st.markdown('<div class="section-header">Análisis de Tiros Recibidos</div>', unsafe_allow_html=True)
    
    with st.expander("Ver detalles de finalizaciones recibidas"):
        if not df_rival_finalizaciones.empty:
            # Simplificar el dataframe para mostrar solo columnas relevantes
            cols_to_show = ["Periodo", "Mins", "code", "group", "Player", "text"]
            df_to_show = df_rival_finalizaciones[cols_to_show].copy()
            
            # Renombrar columnas para mejor legibilidad
            df_to_show = df_to_show.rename(columns={
                "code": "Tipo",
                "group": "Resultado", 
                "Player": "Rival",
                "text": "Detalle"
            })
            
            # Estilizar la tabla
            st.dataframe(
                df_to_show.style.background_gradient(
                    cmap='Reds',
                    subset=['Periodo', 'Mins']
                ),
                use_container_width=True
            )
        else:
            st.info("No hay datos de finalizaciones recibidas disponibles.")
    
    # Sección para exportar a PDF (porteros)
    st.markdown('<div class="section-header">Exportar Análisis</div>', unsafe_allow_html=True)
    
    # Capturar foto del jugador si hay
    if info_jugador:
        ruta_foto = obtener_foto_jugador(info_jugador.get("id"))
        if ruta_foto and os.path.exists(ruta_foto):
            with open(ruta_foto, "rb") as img_file:
                charts['foto_jugador'] = base64.b64encode(img_file.read()).decode()
    
    # Guardar métricas importantes en el diccionario charts
    charts['paradas'] = paradas
    charts['goles_recibidos'] = goles_recibidos
    charts['porcentaje_paradas'] = porcentaje_paradas
    
    # Generar el PDF con HTML/CSS para porteros
    pdf_data = generar_pdf_html_portero(
        jugador_seleccionado,
        info_jugador,
        minutos_jugados,
        paradas,
        porcentaje_paradas,
        goles_recibidos,
        tiros_puerta,
        tiros_fuera,
        pases_completados,
        precision_pases,
        pases_fallados,
        indice_rendimiento,
        charts
    )
    
    # Botón para descargar
    nombre_archivo = f"{jugador_seleccionado.replace(' ', '_')}_analisis.pdf"
    st.markdown(crear_boton_descargar_pdf(pdf_data, nombre_archivo), unsafe_allow_html=True)

def capturar_graficos_matplotlib():
    """
    Captura el gráfico de matplotlib actual y lo convierte a base64
    """
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def capturar_graficos_plotly(fig):
    """
    Captura un gráfico de plotly y lo convierte a base64 con mejor gestión de errores
    """
    try:
        # Configurar pio explícitamente para usar kaleido
        import plotly.io as pio
        pio.kaleido.scope.default_format = "png"
        pio.kaleido.scope.default_width = 800
        pio.kaleido.scope.default_height = 500
        pio.kaleido.scope.default_scale = 1.0
        
        # Intenta usar la forma básica
        img_bytes = pio.to_image(fig, format="png")
        return base64.b64encode(img_bytes).decode('utf-8')
    except Exception as e:
        print(f"Error principal al capturar gráfico: {e}")
        
        # Alternativa directa con matplotlib
        try:
            buffer = io.BytesIO()
            
            # Crear una versión simplificada del gráfico con matplotlib
            import matplotlib.pyplot as plt
            plt.figure(figsize=(8, 6))
            
            # Crear un gráfico simple basado en el tipo de gráfico Plotly
            if 'pie' in str(fig.data[0]).lower():
                # Es un gráfico circular
                labels = fig.data[0].labels if hasattr(fig.data[0], 'labels') and fig.data[0].labels else []
                values = fig.data[0].values if hasattr(fig.data[0], 'values') and fig.data[0].values else []
                
                plt.pie(values, labels=labels, autopct='%1.1f%%')
                plt.axis('equal')
                
            elif 'bar' in str(fig.data[0]).lower():
                # Es un gráfico de barras
                x_vals = fig.data[0].x if hasattr(fig.data[0], 'x') and fig.data[0].x else []
                y_vals = fig.data[0].y if hasattr(fig.data[0], 'y') and fig.data[0].y else []
                
                plt.bar(x_vals, y_vals)
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
            
            # Título básico
            plt.title("Gráfico generado como respaldo")
            
            # Guardar y codificar
            plt.savefig(buffer, format='png', bbox_inches='tight')
            plt.close()
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
        except Exception as e2:
            print(f"Error con el método alternativo: {e2}")
            return None

def crear_boton_descargar_pdf(pdf_data, filename="analisis_jugador.pdf"):
    """
    Crea un botón para descargar el PDF generado
    
    Args:
        pdf_data: Datos del PDF en bytes
        filename: Nombre del archivo a descargar
    """
    b64 = base64.b64encode(pdf_data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}" style="text-decoration:none;">'\
           f'<div style="background-color:#ff6600; padding:10px 15px; color:white; '\
           f'font-weight:bold; border-radius:5px; text-align:center; margin:20px 0;">' \
           f'📥 Descargar Informe en PDF</div></a>'
    return href

# Nueva función para generar PDFs con HTML para jugadores regulares
def generar_pdf_html(jugador_seleccionado, info_jugador, minutos_jugados, 
                    pases_completados, precision_pases, pases_fallados,
                    finalizaciones_totales, goles, encontrar_profundidad,
                    encontrar_cara, atacar_area, faltas, indice_rendimiento,
                    charts):
    """
    Genera un PDF con diseño HTML personalizado, muy similar a la interfaz web
    
    Returns:
        bytes: PDF generado en bytes
    """
    # HTML Template usando Jinja2
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Análisis de {{ jugador_nombre }}</title>
        <style>
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-family: 'Arial', sans-serif;
                color: #333;
                line-height: 1.6;
                padding: 0;
                margin: 0;
            }
            .page {
                page-break-after: always;
                padding: 20px;
            }
            .last-page {
                page-break-after: avoid;
            }
            .header {
                font-size: 28px;
                font-weight: bold;
                color: #1a5276;
                margin-bottom: 20px;
                border-bottom: 2px solid #ff6600;
                padding-bottom: 8px;
            }
            .player-card {
                background-color: #1a5276;
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
            }
            .player-photo {
                width: 80px;
                height: 80px;
                border-radius: 50%;
                border: 3px solid #ff6600;
                object-fit: cover;
                margin-right: 20px;
            }
            .player-info {
                flex-grow: 1;
            }
            .player-name {
                font-size: 24px;
                font-weight: bold;
            }
            .player-team {
                font-size: 16px;
                opacity: 0.8;
            }
            .player-position {
                background-color: #ff6600;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                display: inline-block;
                margin-top: 5px;
                font-size: 14px;
            }
            .section-header {
                font-size: 20px;
                color: #1a5276;
                margin: 20px 0 10px 0;
                padding-bottom: 5px;
                border-bottom: 1px solid #ddd;
            }
            .metrics-container {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 10px;
                margin-bottom: 20px;
            }
            .metric-box {
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            }
            .metric-title {
                font-size: 16px;
                color: #666;
                margin-bottom: 5px;
            }
            .metric-value {
                font-size: 26px;
                font-weight: bold;
                color: #ff6600;
            }
            .metric-subtitle {
                font-size: 14px;
                color: #666;
            }
            .charts-container {
                margin-bottom: 20px;
            }
            .chart-row {
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
                justify-content: center;
            }
            .chart-box {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                flex: 1;
                max-width: 45%;
            }
            .chart-full {
                width: 90%;
                margin: 0 auto 20px auto;
            }
            .chart-img {
                width: 100%;
                height: auto;
                border-radius: 8px;
            }
            .full-width-chart {
                width: 90%;
                margin: 0 auto;
            }
            .footer {
                font-size: 12px;
                color: #666;
                text-align: center;
                margin-top: 40px;
                border-top: 1px solid #ddd;
                padding-top: 10px;
            }
        </style>
    </head>
    <body>
        <!-- PÁGINA 1: Información básica y métricas -->
        <div class="page">
            <div class="header">📊 Análisis Individual: {{ jugador_nombre }}</div>
            
            <!-- Tarjeta del jugador -->
            <div class="player-card">
                {% if foto_jugador %}
                <img src="data:image/png;base64,{{ foto_jugador }}" class="player-photo" alt="{{ jugador_nombre }}">
                {% else %}
                <div style="width: 80px; height: 80px; border-radius: 50%; background-color: #ff6600; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; color: white; margin-right: 20px;">{{ iniciales }}</div>
                {% endif %}
                <div class="player-info">
                    <div class="player-name">{{ jugador_nombre }}</div>
                    <div class="player-team">Valencia CF</div>
                    {% if posicion %}
                    <div class="player-position">{{ posicion }}</div>
                    {% endif %}
                </div>
            </div>
            
            <!-- Métricas clave -->
            <div class="section-header">Métricas Clave</div>
            
            <div class="metrics-container">
                <!-- Fila 1 -->
                <div class="metric-box">
                    <div class="metric-title">Minutos Jugados (M.J.)</div>
                    <div class="metric-value">{{ minutos_jugados }}</div>
                </div>
                
                <div class="metric-box">
                    <div class="metric-title">Pases Completados</div>
                    <div class="metric-value">{{ pases_completados }}</div>
                    <div class="metric-subtitle">{{ precision_pases }}% de precisión</div>
                </div>
                
                <div class="metric-box">
                    <div class="metric-title">Finalizaciones</div>
                    <div class="metric-value">{{ finalizaciones_totales }}</div>
                    <div class="metric-subtitle">{{ goles }} gol{% if goles != 1 %}es{% endif %}</div>
                </div>
                
                <div class="metric-box">
                    <div class="metric-title">Índice Rendimiento</div>
                    <div class="metric-value">{{ indice_rendimiento }}</div>
                </div>
                
                <!-- Fila 2 -->
                <div class="metric-box">
                    <div class="metric-title">Pases Fallados</div>
                    <div class="metric-value">{{ pases_fallados }}</div>
                </div>
                
                <div class="metric-box">
                    <div class="metric-title">Encontrar Futbolista</div>
                    <div class="metric-value">{{ encontrar_total }}</div>
                    <div class="metric-subtitle">{{ encontrar_profundidad }} en profundidad</div>
                </div>
                
                <div class="metric-box">
                    <div class="metric-title">Atacar el área</div>
                    <div class="metric-value">{{ atacar_area }}</div>
                </div>
                
                <div class="metric-box">
                    <div class="metric-title">Faltas Cometidas</div>
                    <div class="metric-value">{{ faltas }}</div>
                </div>
            </div>
        </div>
        
        <!-- PÁGINA 2: Visualizaciones de Rendimiento -->
        <div class="page">
            <div class="section-header">Visualización de Rendimiento</div>
            
            <!-- Gráficos en una fila -->
            <div class="chart-row">
                {% if chart_pases %}
                <div class="chart-box">
                    <img src="data:image/png;base64,{{ chart_pases }}" class="chart-img" alt="Distribución de Pases">
                </div>
                {% endif %}
                
                {% if chart_finalizaciones %}
                <div class="chart-box">
                    <img src="data:image/png;base64,{{ chart_finalizaciones }}" class="chart-img" alt="Finalizaciones">
                </div>
                {% endif %}
            </div>
            
            <!-- Gráfico de resumen (ancho completo) -->
            {% if chart_resumen %}
            <div class="chart-full">
                <img src="data:image/png;base64,{{ chart_resumen }}" class="chart-img" alt="Resumen de Acciones">
            </div>
            {% endif %}
        </div>
        
        <!-- PÁGINA 3: Mapa de Pases -->
        <div class="last-page">
            <div class="section-header">Mapa de Pases en el Campo</div>
            {% if chart_mapa_pases %}
            <div class="full-width-chart">
                <img src="data:image/png;base64,{{ chart_mapa_pases }}" class="chart-img" alt="Mapa de Pases">
            </div>
            {% endif %}
            
            <div class="footer">
                <p>Informe generado para Valencia CF | Fecha: {{ fecha_generacion }}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Preparar datos para la plantilla
    # Calcular iniciales del jugador
    nombre_display = info_jugador.get("nombre", "") if info_jugador else jugador_seleccionado
    if ". " in nombre_display:
        nombre_display = nombre_display.split(". ", 1)[1]
    iniciales = "".join([n[0] for n in nombre_display[0:2].upper()])
    
    template_data = {
        'jugador_nombre': nombre_display,
        'iniciales': iniciales,
        'posicion': info_jugador.get("posicion", "") if info_jugador else "",
        'foto_jugador': charts.get('foto_jugador', None),
        'minutos_jugados': minutos_jugados,
        'pases_completados': pases_completados,
        'precision_pases': f"{precision_pases:.1f}",
        'pases_fallados': pases_fallados,
        'finalizaciones_totales': finalizaciones_totales,
        'goles': goles,
        'encontrar_profundidad': encontrar_profundidad,
        'encontrar_total': encontrar_profundidad + encontrar_cara,
        'atacar_area': atacar_area,
        'faltas': faltas,
        'indice_rendimiento': f"{indice_rendimiento:.1f}",
        'chart_pases': charts.get('distribucion_pases', None),
        'chart_finalizaciones': charts.get('finalizaciones_chart', None),
        'chart_resumen': charts.get('resumen_acciones', None),
        'chart_mapa_pases': charts.get('mapa_pases', None),
        'fecha_generacion': datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    
    # Renderizar el HTML con Jinja2
    template = Template(html_template)
    html_content = template.render(**template_data)
    
    # Guardar el HTML temporalmente
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
        tmp.write(html_content.encode('utf-8'))
        tmp_path = tmp.name
    
    # Generar PDF a partir del HTML
    pdf = weasyprint.HTML(filename=tmp_path).write_pdf()
    
    # Eliminar archivo temporal
    os.unlink(tmp_path)
    
    return pdf

# Nueva función para generar PDFs con HTML para porteros
def generar_pdf_html_portero(jugador_seleccionado, info_jugador, minutos_jugados,
                           paradas, porcentaje_paradas, goles_recibidos, 
                           tiros_puerta, tiros_fuera, pases_completados,
                           precision_pases, pases_fallados, indice_rendimiento,
                           charts):
    """
    Genera un PDF con diseño HTML personalizado para porteros
    
    Returns:
        bytes: PDF generado en bytes
    """
    # HTML Template usando Jinja2
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Análisis del Portero {{ jugador_nombre }}</title>
        <style>
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-family: 'Arial', sans-serif;
                color: #333;
                line-height: 1.6;
                padding: 0;
                margin: 0;
            }
            .page {
                page-break-after: always;
                padding: 20px;
            }
            .last-page {
                page-break-after: avoid;
            }
            .header {
                font-size: 28px;
                font-weight: bold;
                color: #1a5276;
                margin-bottom: 20px;
                border-bottom: 2px solid #ff6600;
                padding-bottom: 8px;
            }
            .player-card {
                background-color: #1a5276;
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
            }
            .player-photo {
                width: 80px;
                height: 80px;
                border-radius: 50%;
                border: 3px solid #ff6600;
                object-fit: cover;
                margin-right: 20px;
            }
            .player-info {
                flex-grow: 1;
            }
            .player-name {
                font-size: 24px;
                font-weight: bold;
            }
            .player-team {
                font-size: 16px;
                opacity: 0.8;
            }
            .player-position {
                background-color: #ff6600;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                display: inline-block;
                margin-top: 5px;
                font-size: 14px;
            }
            .section-header {
                font-size: 20px;
                color: #1a5276;
                margin: 20px 0 10px 0;
                padding-bottom: 5px;
                border-bottom: 1px solid #ddd;
            }
            .metrics-container {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 10px;
                margin-bottom: 20px;
            }
            .metric-box {
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            }
            .metric-title {
                font-size: 16px;
                color: #666;
                margin-bottom: 5px;
            }
            .metric-value {
                font-size: 26px;
                font-weight: bold;
                color: #ff6600;
            }
            .metric-subtitle {
                font-size: 14px;
                color: #666;
            }
            .charts-container {
                margin-bottom: 20px;
            }
            .chart-row {
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
                justify-content: center;
            }
            .chart-box {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                flex: 1;
                max-width: 45%;
            }
            .chart-full {
                width: 90%;
                margin: 0 auto 20px auto;
            }
            .chart-img {
                width: 100%;
                height: auto;
                border-radius: 8px;
            }
            .full-width-chart {
                width: 90%;
                margin: 0 auto;
            }
            .footer {
                font-size: 12px;
                color: #666;
                text-align: center;
                margin-top: 40px;
                border-top: 1px solid #ddd;
                padding-top: 10px;
            }
        </style>
    </head>
    <body>
        <!-- PÁGINA 1: Información básica y métricas -->
        <div class="page">
            <div class="header">📊 Análisis del Portero: {{ jugador_nombre }}</div>
            
            <!-- Tarjeta del jugador -->
            <div class="player-card">
                {% if foto_jugador %}
                <img src="data:image/png;base64,{{ foto_jugador }}" class="player-photo" alt="{{ jugador_nombre }}">
                {% else %}
                <div style="width: 80px; height: 80px; border-radius: 50%; background-color: #ff6600; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; color: white; margin-right: 20px;">{{ iniciales }}</div>
                {% endif %}
                <div class="player-info">
                    <div class="player-name">{{ jugador_nombre }}</div>
                    <div class="player-team">Valencia CF</div>
                    {% if posicion %}
                    <div class="player-position">{{ posicion }}</div>
                    {% endif %}
                </div>
            </div>
            
            <!-- Métricas clave -->
            <div class="section-header">Estadísticas del Portero</div>
            
            <div class="metrics-container">
                <!-- Fila 1 -->
                <div class="metric-box">
                    <div class="metric-title">Minutos Jugados (M.J.)</div>
                    <div class="metric-value">{{ minutos_jugados }}</div>
                </div>
                
                <div class="metric-box">
                    <div class="metric-title">Paradas</div>
                    <div class="metric-value">{{ paradas }}</div>
                    <div class="metric-subtitle">{{ porcentaje_paradas }}% de efectividad</div>
                </div>
                
                <div class="metric-box">
                    <div class="metric-title">Goles Recibidos</div>
                    <div class="metric-value">{{ goles_recibidos }}</div>
                </div>
                
                <div class="metric-box">
                    <div class="metric-title">Índice Rendimiento</div>
                    <div class="metric-value">{{ indice_rendimiento }}</div>
                </div>
                
                <!-- Fila 2 -->
                <div class="metric-box">
                    <div class="metric-title">Tiros a Puerta Recibidos</div>
                    <div class="metric-value">{{ tiros_puerta }}</div>
                </div>
                
                <div class="metric-box">
                    <div class="metric-title">Tiros Fuera Recibidos</div>
                    <div class="metric-value">{{ tiros_fuera }}</div>
                </div>
                
                <div class="metric-box">
                    <div class="metric-title">Pases Completados</div>
                    <div class="metric-value">{{ pases_completados }}</div>
                    <div class="metric-subtitle">{{ precision_pases }}% de precisión</div>
                </div>
                
                <div class="metric-box">
                    <div class="metric-title">Pases Fallados</div>
                    <div class="metric-value">{{ pases_fallados }}</div>
                </div>
            </div>
        </div>
            
        <!-- PÁGINA 2: Visualizaciones de Rendimiento -->
        <div class="page">
            <div class="section-header">Visualización de Rendimiento</div>
            
            <!-- Gráficos en una fila -->
            <div class="chart-row">
                {% if chart_tiros %}
                <div class="chart-box">
                    <img src="data:image/png;base64,{{ chart_tiros }}" class="chart-img" alt="Distribución de Tiros">
                </div>
                {% endif %}
                
                {% if chart_pases %}
                <div class="chart-box">
                    <img src="data:image/png;base64,{{ chart_pases }}" class="chart-img" alt="Distribución de Pases">
                </div>
                {% endif %}
            </div>
            
            <!-- Gráfico de resumen (ancho completo) -->
            {% if chart_resumen %}
            <div class="chart-full">
                <img src="data:image/png;base64,{{ chart_resumen }}" class="chart-img" alt="Resumen de Acciones">
            </div>
            {% endif %}
        </div>
        
        <!-- PÁGINA 3: Mapa de Pases -->
        <div class="last-page">
            <div class="section-header">Mapa de Pases en el Campo</div>
            {% if chart_mapa_pases %}
            <div class="full-width-chart">
                <img src="data:image/png;base64,{{ chart_mapa_pases }}" class="chart-img" alt="Mapa de Pases">
            </div>
            {% endif %}
            
            <div class="footer">
                <p>Informe generado para Valencia CF | Fecha: {{ fecha_generacion }}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Preparar datos para la plantilla
    # Calcular iniciales del jugador
    nombre_display = info_jugador.get("nombre", "") if info_jugador else jugador_seleccionado
    if ". " in nombre_display:
        nombre_display = nombre_display.split(". ", 1)[1]
    iniciales = "".join([n[0] for n in nombre_display[0:2].upper()])
    
    template_data = {
        'jugador_nombre': nombre_display,
        'iniciales': iniciales,
        'posicion': info_jugador.get("posicion", "") if info_jugador else "",
        'foto_jugador': charts.get('foto_jugador', None),
        'minutos_jugados': minutos_jugados,
        'paradas': paradas,
        'porcentaje_paradas': f"{porcentaje_paradas:.1f}",
        'goles_recibidos': goles_recibidos,
        'tiros_puerta': tiros_puerta,
        'tiros_fuera': tiros_fuera,
        'pases_completados': pases_completados,
        'precision_pases': f"{precision_pases:.1f}",
        'pases_fallados': pases_fallados,
        'indice_rendimiento': f"{indice_rendimiento:.1f}",
        'chart_tiros': charts.get('tiros_chart', None),
        'chart_pases': charts.get('distribucion_pases', None),
        'chart_resumen': charts.get('resumen_acciones', None),
        'chart_mapa_pases': charts.get('mapa_pases', None),
        'fecha_generacion': datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    
    # Renderizar el HTML con Jinja2
    template = Template(html_template)
    html_content = template.render(**template_data)
    
    # Guardar el HTML temporalmente
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
        tmp.write(html_content.encode('utf-8'))
        tmp_path = tmp.name
    
    # Generar PDF a partir del HTML
    pdf = weasyprint.HTML(filename=tmp_path).write_pdf()
    
    # Eliminar archivo temporal
    os.unlink(tmp_path)
    
    return pdf

def pagina_registros_individuales():
    # Aplicar estilo profesional con CSS personalizado
    st.markdown("""
    <style>
    .main-header {
        font-size: 28px;
        font-weight: bold;
        color: #1a5276;
        margin-bottom: 20px;
        border-bottom: 2px solid #ff6600;
        padding-bottom: 8px;
    }
    .metric-container {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .metric-title {
        font-size: 16px;
        color: #666;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 26px;
        font-weight: bold;
        color: #ff6600;
    }
    .section-header {
        font-size: 20px;
        color: #1a5276;
        margin: 20px 0 10px 0;
        padding-bottom: 5px;
        border-bottom: 1px solid #ddd;
    }
    .chart-container {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .player-selector {
        background-color: #1a5276;
        color: white;
        padding: 8px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .player-card {
        background-color: #1a5276; 
        color: white; 
        padding: 20px; 
        border-radius: 8px; 
        margin-bottom: 20px;
        display: flex;
        align-items: center;
    }
    .player-photo {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        border: 3px solid #ff6600;
        object-fit: cover;
        margin-right: 20px;
    }
    .player-info {
        flex-grow: 1;
    }
    .player-name {
        font-size: 24px;
        font-weight: bold;
    }
    .player-team {
        font-size: 16px;
        opacity: 0.8;
    }
    .player-position {
        background-color: #ff6600;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        display: inline-block;
        margin-top: 5px;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-header">📊 Análisis Individual</div>', unsafe_allow_html=True)
    
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
    
    # Selector de archivo con estilo personalizado
    st.markdown('<div class="section-header">Selección de Partido</div>', unsafe_allow_html=True)
    nombres_archivos = [archivo['nombre_original'] for archivo in archivos_a_mostrar]
    archivo_seleccionado = st.selectbox("", nombres_archivos)
    
    # Encontrar la ruta del archivo seleccionado
    archivo_info = next((a for a in archivos_a_mostrar if a['nombre_original'] == archivo_seleccionado), None)
    
    if archivo_info:
        ruta_archivo = archivo_info['ruta']
        
        try:
            # Cargar el archivo Excel
            df = pd.read_excel(ruta_archivo)
            
            # Filtrar solo datos del Valencia
            df_valencia = df[df["Team"] == "Valencia"]
            
            # Filtrar jugadores - solo queremos jugadores reales (excluyendo "Valencia" y valores NaN)
            jugadores = []
            for jugador in df_valencia["Player"].unique():
                if jugador != "Valencia" and isinstance(jugador, str) and pd.notna(jugador):
                    jugadores.append(jugador)
            
            # Ordenar jugadores (todos son string ahora)
            jugadores.sort()
            
            # Panel de control con estilo mejorado
            st.markdown('<div class="player-selector">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            
            with col1:
                # Seleccionar un jugador para analizar
                jugador_seleccionado = st.selectbox("Jugador", jugadores)
            
            with col2:
                periodos = sorted(df_valencia["Periodo"].unique().tolist())
                opciones_periodo = ["Todos"] + [f"Periodo {p}" for p in periodos]
                periodo_seleccionado = st.selectbox("Periodo", opciones_periodo, key="periodo_stats")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Filtrar por periodo si se seleccionó uno específico
            df_filtrado = df_valencia.copy()
            if periodo_seleccionado != "Todos":
                periodo_num = int(periodo_seleccionado.split(" ")[1])
                df_filtrado = df_filtrado[df_filtrado["Periodo"] == periodo_num]
            
            # Filtrar datos del jugador seleccionado
            df_jugador = df_filtrado[df_filtrado["Player"] == jugador_seleccionado]
            
            if len(df_jugador) == 0:
                st.warning(f"No hay datos disponibles para {jugador_seleccionado} en el periodo seleccionado.")
                return
            
            # Buscar jugador en la plantilla
            info_jugador = encontrar_jugador_plantilla(jugador_seleccionado)
            
            # Extraer nombre del jugador si está en formato "#. Nombre"
            jugador_nombre = jugador_seleccionado
            if ". " in jugador_seleccionado:
                partes = jugador_seleccionado.split(". ", 1)
                if len(partes) == 2:
                    jugador_nombre = partes[1]
            
            # Obtener minutos jugados
            minutos_jugados = None
            # Buscar en las filas donde Jugadores y M.J contienen la información
            jugador_mj_info = df[(df["Jugadores"] == jugador_seleccionado) & pd.notna(df["M.J"])]
            if not jugador_mj_info.empty:
                # Usar el valor de M.J cuando el jugador aparece en la columna Jugadores
                minutos_jugados = int(jugador_mj_info["M.J"].iloc[0])
            else:
                # Intentar buscar con otro formato o nombre parcial si no se encuentra exacto
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
            
            # Cabecera de jugador con foto de la plantilla
            if info_jugador:
                # Obtener foto del jugador
                ruta_foto = obtener_foto_jugador(info_jugador.get("id"))
                foto_html = ""
                
                if ruta_foto and os.path.exists(ruta_foto):
                    # Leer la imagen y convertirla a base64
                    with open(ruta_foto, "rb") as img_file:
                        img_bytes = img_file.read()
                        img_base64 = base64.b64encode(img_bytes).decode()
                    
                    foto_html = f'<img src="data:image/png;base64,{img_base64}" class="player-photo" alt="{info_jugador.get("nombre", "")}">'
                else:
                    # Si no hay foto, mostrar un círculo con iniciales
                    iniciales = "".join([n[0] for n in info_jugador.get("nombre", jugador_nombre)[0:2].upper()])
                    foto_html = f'''
                    <div style="width: 80px; height: 80px; border-radius: 50%; background-color: #ff6600; 
                    display: flex; align-items: center; justify-content: center; font-size: 24px; 
                    font-weight: bold; color: white; margin-right: 20px;">{iniciales}</div>
                    '''
                
                # Crear tarjeta del jugador
                st.markdown(f'''
                <div class="player-card">
                    {foto_html}
                    <div class="player-info">
                        <div class="player-name">{info_jugador.get("nombre", "")} {info_jugador.get("apellidos", "")}</div>
                        <div class="player-team">Valencia CF</div>
                        <div class="player-position">{info_jugador.get("posicion", "")}</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                # Si no hay información en la plantilla, mostrar información básica
                # Extraer número y nombre del jugador si está en formato "#. Nombre"
                jugador_nombre = jugador_seleccionado
                jugador_numero = ""
                if ". " in jugador_seleccionado:
                    partes = jugador_seleccionado.split(". ", 1)
                    if len(partes) == 2:
                        jugador_numero = partes[0]
                        jugador_nombre = partes[1]
                
                foto_html = f"""
                <div style="width: 80px; height: 80px; border-radius: 50%; background-color: #ff6600; 
                    display: flex; align-items: center; justify-content: center; font-size: 24px; 
                    font-weight: bold; color: white; margin-right: 20px;">
                    {jugador_numero if jugador_numero else jugador_nombre[0:2].upper()}
                </div>
                """
                
                st.markdown(f"""
                <div class="player-card">
                    {foto_html}
                    <div class="player-info">
                        <div class="player-name">{jugador_nombre}</div>
                        <div class="player-team">Valencia CF</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Determinar si es portero
            es_portero = False
            
            # Verificar en info_jugador (si está en la plantilla)
            if info_jugador:
                # Si tenemos info del jugador en la plantilla, usamos EXCLUSIVAMENTE su posición registrada
                posicion = info_jugador.get("posicion", "").lower()
                es_portero = any(palabra in posicion for palabra in ["portero", "goalkeeper", "arquero", "porter"])
            else:
                # SOLO si no está en la plantilla, intentamos inferir si es portero por su nombre
                porteros_conocidos = ["mamardashvili", "jaume", "domenech", "cillessen", "herrera", "jimenez", "raul"]
                for nombre in porteros_conocidos:
                    if nombre in jugador_nombre.lower():
                        # Comprobación adicional: verificar si hay datos de portero
                        # (esto ayuda a evitar falsos positivos)
                        for equipo in df["Team"].unique().tolist():
                            if equipo != "Valencia" and isinstance(equipo, str):
                                df_rival = df[df["Team"] == equipo]
                                df_rival_finalizaciones = df_rival[df_rival["code"] == "Finalizaciones"]
                                if len(df_rival_finalizaciones) > 0:
                                    es_portero = True
                                    break
                        break
            
            # Mostrar estadísticas según si es portero o jugador de campo
            if es_portero:
                # Mostrar estadísticas específicas de portero
                mostrar_estadisticas_portero(df, df_jugador, jugador_seleccionado, info_jugador, minutos_jugados)
            else:
                # Calcular estadísticas para jugador de campo
                total_acciones = len(df_jugador)
                
                # 1. Estadísticas de pases
                df_pases = df_jugador[df_jugador["code"] == "Pases"]
                pases_totales = len(df_pases)
                pases_completados = df_pases["Secundary"].notna().sum()
                pases_fallados = pases_totales - pases_completados
                precision_pases = (pases_completados/pases_totales*100) if pases_totales > 0 else 0
                
                # 2. Estadísticas de finalizaciones
                df_finalizaciones = df_jugador[df_jugador["code"] == "Finalizaciones"]
                finalizaciones_totales = len(df_finalizaciones)
                
                # Calcular goles, tiros a puerta y fuera
                goles = df_finalizaciones[df_finalizaciones["text"] == "Gol"].shape[0]
                tiros_puerta = df_finalizaciones[df_finalizaciones["group"] == "A puerta"].shape[0]
                tiros_fuera = df_finalizaciones[df_finalizaciones["group"] == "Fuera"].shape[0]
                
                # 3. Estadísticas de faltas
                faltas = df_jugador[df_jugador["code"] == "Faltas"].shape[0]
                
                # 4. Estadísticas de recuperaciones
                recuperaciones = df_jugador[df_jugador["code"] == "Recuperaciones"].shape[0]
                
                # 5. Otras estadísticas
                encontrar_profundidad = df_jugador[df_jugador["code"] == "Encontrar Futbolista en profundidad"].shape[0]
                encontrar_cara = df_jugador[df_jugador["code"] == "Encontrar Futbolista de cara"].shape[0]
                atacar_area = df_jugador[df_jugador["code"] == "Atacar el área"].shape[0]
                
                # Tarjetas de métricas clave (estilo de LaLiga)
                st.markdown('<div class="section-header">Métricas Clave</div>', unsafe_allow_html=True)
                
                # Primera fila de métricas - Añadimos M.J.
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-title">Minutos Jugados (M.J.)</div>
                        <div class="metric-value">{minutos_jugados}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-title">Pases Completados</div>
                        <div class="metric-value">{pases_completados}</div>
                        <div style="font-size: 14px;">{precision_pases:.1f}% de precisión</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-title">Finalizaciones</div>
                        <div class="metric-value">{finalizaciones_totales}</div>
                        <div style="font-size: 14px;">{goles} gol{'es' if goles != 1 else ''}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    # Calcular un índice de rendimiento
                    indice_rendimiento = (
                        pases_completados * 0.1 + 
                        goles * 3 + 
                        tiros_puerta * 0.5 + 
                        recuperaciones * 0.5 - 
                        faltas * 0.2 + 
                        (pases_fallados * -0.05) +
                        encontrar_profundidad * 0.2 +
                        encontrar_cara * 0.1 +
                        atacar_area * 0.3
                    )
                    
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-title">Índice Rendimiento</div>
                        <div class="metric-value">{indice_rendimiento:.1f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Segunda fila de métricas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-title">Pases Fallados</div>
                        <div class="metric-value">{pases_fallados}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-title">Encontrar Futbolista</div>
                        <div class="metric-value">{encontrar_profundidad + encontrar_cara}</div>
                        <div style="font-size: 14px;">{encontrar_profundidad} en profundidad</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-title">Atacar el área</div>
                        <div class="metric-value">{atacar_area}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-title">Faltas Cometidas</div>
                        <div class="metric-value">{faltas}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Área de visualización con gráficos profesionales
                st.markdown('<div class="section-header">Visualización de Rendimiento</div>', unsafe_allow_html=True)
                
                charts = {}  # Diccionario para almacenar gráficos para el PDF
                
                # Diseño de dos columnas para gráficos principales
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico de distribución de pases estilo profesional
                    if pases_totales > 0:
                        fig_pases = go.Figure()
                        fig_pases.add_trace(go.Pie(
                            labels=['Completados', 'Fallados'],
                            values=[pases_completados, pases_fallados],
                            hole=0.6,
                            marker=dict(colors=['#4CAF50', '#E57373']),
                            textinfo='percent+value',
                            insidetextorientation='radial',
                            pull=[0.05, 0],
                            rotation=90
                        ))
                        
                        fig_pases.update_layout(
                            title={
                                'text': "Distribución de Pases",
                                'y':0.95,
                                'x':0.5,
                                'xanchor': 'center',
                                'yanchor': 'top',
                                'font': dict(size=16, color='#1a5276')
                            },
                            annotations=[dict(
                                text=f"{precision_pases:.1f}%<br>precisión",
                                x=0.5, y=0.5,
                                font=dict(size=16, color='#1a5276'),
                                showarrow=False
                            )],
                            showlegend=True,
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=-0.2,
                                xanchor="center",
                                x=0.5
                            ),
                            margin=dict(l=20, r=20, t=60, b=20),
                            paper_bgcolor='white',
                            plot_bgcolor='white'
                        )
                        
                        st.plotly_chart(fig_pases, use_container_width=True)
                        
                        # Capturar gráfico para PDF
                        try:
                            charts['distribucion_pases'] = capturar_graficos_plotly(fig_pases)
                        except Exception as e:
                            st.warning(f"No se pudo capturar el gráfico de pases: {str(e)}")
                    else:
                        st.info("No hay datos de pases disponibles para este jugador.")
                
                with col2:
                    # Gráfico de finalizaciones con diseño profesional
                    if finalizaciones_totales > 0:
                        # Crea un gráfico de anillos personalizado para finalizaciones
                        fig_fin = go.Figure()
                        
                        # Colores para diferentes tipos de tiros
                        colores_tiros = ['#4CAF50', '#2196F3', '#FF9800']
                        
                        # Valores para goles, a puerta (sin gol) y fuera
                        valores_tiros = [goles, tiros_puerta - goles, tiros_fuera]
                        etiquetas_tiros = ['Goles', 'A puerta', 'Fuera']
                        
                        fig_fin.add_trace(go.Pie(
                            labels=etiquetas_tiros,
                            values=valores_tiros,
                            hole=0.6,
                            marker=dict(colors=colores_tiros),
                            textinfo='percent+value',
                            insidetextorientation='radial',
                            pull=[0.1, 0, 0]
                        ))
                        
                        # Calcular porcentaje de acierto (goles/finalizaciones)
                        porcentaje_acierto = (goles / finalizaciones_totales * 100) if finalizaciones_totales > 0 else 0
                        
                        fig_fin.update_layout(
                            title={
                                'text': "Finalizaciones",
                                'y':0.95,
                                'x':0.5,
                                'xanchor': 'center',
                                'yanchor': 'top',
                                'font': dict(size=16, color='#1a5276')
                            },
                            annotations=[dict(
                                text=f"{porcentaje_acierto:.1f}%<br>efectividad",
                                x=0.5, y=0.5,
                                font=dict(size=16, color='#1a5276'),
                                showarrow=False
                            )],
                            showlegend=True,
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=-0.2,
                                xanchor="center",
                                x=0.5
                            ),
                            margin=dict(l=20, r=20, t=60, b=20),
                            paper_bgcolor='white',
                            plot_bgcolor='white'
                        )
                        
                        st.plotly_chart(fig_fin, use_container_width=True)
                        
                        # Capturar gráfico para PDF
                        try:
                            charts['finalizaciones_chart'] = capturar_graficos_plotly(fig_fin)
                        except Exception as e:
                            st.warning(f"No se pudo capturar el gráfico de finalizaciones: {str(e)}")
                    else:
                        st.info("No hay datos de finalizaciones disponibles para este jugador.")
                
                # Gráfico de barras de resumen
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                
                # Crear un dataframe para el gráfico de barras por tipo de acción
                tipos_acciones = {
                    'M.J.': minutos_jugados,  # Añadimos M.J. al resumen
                    'Pases Completados': pases_completados,
                    'Pases Fallados': pases_fallados,
                    'Tiros a Puerta': tiros_puerta,
                    'Tiros Fuera': tiros_fuera,
                    'Recuperaciones': recuperaciones,
                    'Faltas': faltas,
                    'Futbolista en Profundidad': encontrar_profundidad,
                    'Futbolista de Cara': encontrar_cara,
                    'Atacar el área': atacar_area
                }
                
                df_acciones = pd.DataFrame({
                    'Tipo': list(tipos_acciones.keys()),
                    'Cantidad': list(tipos_acciones.values())
                })
                
                # Ordenar por cantidad (descendente)
                df_acciones = df_acciones.sort_values('Cantidad', ascending=False)
                
                # Asignar colores según tipo de acción (estilo LaLiga)
                colores_acciones = {
                    'M.J.': '#1E88E5',  # Color para M.J.
                    'Pases Completados': '#4CAF50',
                    'Pases Fallados': '#E57373',
                    'Tiros a Puerta': '#2196F3',
                    'Tiros Fuera': '#FF9800',
                    'Recuperaciones': '#9C27B0',
                    'Faltas': '#F44336',
                    'Futbolista en Profundidad': '#00BCD4',
                    'Futbolista de Cara': '#3F51B5',
                    'Atacar el área': '#FFC107'
                }
                
                colores_barras = [colores_acciones.get(tipo, '#757575') for tipo in df_acciones['Tipo']]
                
                # Crear gráfico de barras con estilo profesional
                fig_acciones = go.Figure()
                
                fig_acciones.add_trace(go.Bar(
                    x=df_acciones['Tipo'],
                    y=df_acciones['Cantidad'],
                    marker_color=colores_barras,
                    text=df_acciones['Cantidad'],
                    textposition='auto'
                ))
                
                fig_acciones.update_layout(
                    title={
                        'text': "Resumen de Acciones",
                        'y':0.95,
                        'x':0.5,
                        'xanchor': 'center',
                        'yanchor': 'top',
                        'font': dict(size=18, color='#1a5276')
                    },
                    xaxis=dict(
                        title='',
                        tickangle=-45,
                        tickfont=dict(size=12)
                    ),
                    yaxis=dict(
                        title='',
                        gridcolor='#eee',
                        zerolinecolor='#eee'
                    ),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    height=450,
                    margin=dict(l=40, r=40, t=60, b=80)
                )
                
                st.plotly_chart(fig_acciones, use_container_width=True)
                
                # Capturar gráfico para PDF
                try:
                    charts['resumen_acciones'] = capturar_graficos_plotly(fig_acciones)
                except Exception as e:
                    st.warning(f"No se pudo capturar el gráfico de resumen: {str(e)}")
                
                st.markdown('</div>', unsafe_allow_html=True)

                # Nueva sección: Visualización de pases en el campo
                st.markdown('<div class="section-header">Mapa de Pases en el Campo</div>', unsafe_allow_html=True)
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                
                # Llamar a la función que visualiza los pases en el campo
                mapa_pases_base64 = visualizar_pases_campo(df_jugador)
                
                # Guardar imagen para PDF
                if mapa_pases_base64:
                    charts['mapa_pases'] = mapa_pases_base64
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Sección para exportar a PDF
                st.markdown('<div class="section-header">Exportar Análisis</div>', unsafe_allow_html=True)
                
                # Si hay foto del jugador, capturarla
                if info_jugador:
                    ruta_foto = obtener_foto_jugador(info_jugador.get("id"))
                    if ruta_foto and os.path.exists(ruta_foto):
                        with open(ruta_foto, "rb") as img_file:
                            charts['foto_jugador'] = base64.b64encode(img_file.read()).decode()
                
                # Generar el PDF con HTML/CSS
                pdf_data = generar_pdf_html(
                    jugador_seleccionado,
                    info_jugador,
                    minutos_jugados,
                    pases_completados,
                    precision_pases,
                    pases_fallados,
                    finalizaciones_totales,
                    goles,
                    encontrar_profundidad,
                    encontrar_cara,
                    atacar_area,
                    faltas,
                    indice_rendimiento,
                    charts
                )
                
                # Botón para descargar
                nombre_archivo = f"{jugador_seleccionado.replace(' ', '_')}_analisis.pdf"
                st.markdown(crear_boton_descargar_pdf(pdf_data, nombre_archivo), unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error al procesar el archivo: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    # Botón para volver atrás con estilo
    st.markdown("""
    <style>
    .back-button {
        background-color: #1a5276;
        color: white;
        padding: 10px 15px;
        border-radius: 5px;
        text-decoration: none;
        cursor: pointer;
        margin-top: 20px;
        display: inline-block;
        transition: background-color 0.3s;
    }
    .back-button:hover {
        background-color: #154360;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("⬅️ Volver"):
        # Si venimos del panel de equipo, volver a él
        if st.session_state.get("ver_individuales_equipo", False):
            st.session_state["ver_individuales_equipo"] = False
            st.session_state["menu_seleccionado"] = "navegador_equipos"
            st.session_state["ver_panel_equipo"] = True
        else:
            # Si no, volver al menú principal
            st.session_state["menu_seleccionado"] = "inicio"
        st.rerun()