import streamlit as st
import io
import base64
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
import seaborn as sns
from mplsoccer import Pitch
import matplotlib.patches as mpatches
import os

matplotlib.use('Agg')  # Establecer el backend no interactivo

# Funciones auxiliares de convertir_coordenadas para usar en la generación de gráficos
def convertir_coordenadas(x, y):
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

def convertir_coordenadas_reflejado(x, y):
    """Alias de convertir_coordenadas, por consistencia."""
    return convertir_coordenadas(x, y)

def figure_to_image(fig, dpi=120):
    """Convierte una figura de matplotlib en una imagen para reportlab"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
    buf.seek(0)
    return Image(buf, width=7*inch, height=5*inch)

def create_download_button(pdf_bytes, filename="report.pdf", button_text="Descargar PDF"):
    """Crea un botón de descarga para el PDF generado"""
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}"><button style="background-color: #FF6600; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">{button_text}</button></a>'
    return href

def download_single_chart(fig, title="Gráfico", prefix=""):
    """Genera un PDF con un solo gráfico y proporciona un botón de descarga"""
    # Crear un buffer para el PDF
    buffer = io.BytesIO()
    
    # Crear el documento PDF
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(A4),
        rightMargin=72, leftMargin=72,
        topMargin=72, bottomMargin=72
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    # Verificar si el estilo ya existe
    if 'CustomTitle' not in styles:
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#FF6600'),
            spaceAfter=24
        ))
    
    # Elementos para el PDF
    elements = []
    
    # Título
    elements.append(Paragraph(f"Academia Valencia CF - {title}", styles["CustomTitle"]))
    elements.append(Spacer(1, 0.2*inch))
    
    # Fecha y hora
    fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"Generado: {fecha_hora}", styles["Normal"]))
    elements.append(Spacer(1, 0.3*inch))
    
    # Convertir la figura a imagen
    img = figure_to_image(fig)
    elements.append(img)
    
    # Construir PDF
    doc.build(elements)
    
    # Volver al inicio del buffer y obtener el valor
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    # Generar nombre de archivo
    filename = f"{prefix}_{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # Crear botón de descarga
    return create_download_button(pdf_bytes, filename=filename)

def download_multiple_charts(figs, titles, main_title="Informe completo", prefix=""):
    """Genera un PDF con múltiples gráficos y proporciona un botón de descarga"""
    # Verificar que las listas tienen la misma longitud
    if len(figs) != len(titles):
        raise ValueError("Las listas de figuras y títulos deben tener la misma longitud")
    
    # Crear un buffer para el PDF
    buffer = io.BytesIO()
    
    # Crear el documento PDF
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(A4),
        rightMargin=72, leftMargin=72,
        topMargin=72, bottomMargin=72
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    # Verificar si los estilos ya existen
    if 'CustomTitle' not in styles:
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#FF6600'),
            spaceAfter=24
        ))
    if 'CustomSubTitle' not in styles:
        styles.add(ParagraphStyle(
            name='CustomSubTitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1a5276'),
            spaceAfter=12
        ))
    
    # Elementos para el PDF
    elements = []
    
    # Título principal
    elements.append(Paragraph(f"Academia Valencia CF - {main_title}", styles["CustomTitle"]))
    elements.append(Spacer(1, 0.2*inch))
    
    # Fecha y hora
    fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"Generado: {fecha_hora}", styles["Normal"]))
    elements.append(Spacer(1, 0.3*inch))
    
    # Agregar cada gráfico con su título
    for i, (fig, title) in enumerate(zip(figs, titles)):
        # Si no es el primer gráfico, agregar salto de página
        if i > 0:
            elements.append(PageBreak())
        
        # Título del gráfico
        elements.append(Paragraph(title, styles["CustomSubTitle"]))
        elements.append(Spacer(1, 0.2*inch))
        
        # Convertir la figura a imagen
        img = figure_to_image(fig)
        elements.append(img)
    
    # Construir PDF
    doc.build(elements)
    
    # Volver al inicio del buffer y obtener el valor
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    # Generar nombre de archivo
    filename = f"{prefix}_{main_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # Crear botón de descarga
    return create_download_button(pdf_bytes, filename=filename)

def generar_red_pases_para_pdf(df, periodo):
    """Genera una figura de red de pases para un periodo específico"""
    # Filtrar pases primero
    df_pases = df[(df['Team'] == 'Valencia') & (df['code'] == 'Pases') & 
                df['Player'].notna() & df['Secundary'].notna() & 
                df['startX'].notna() & df['startY'].notna() & 
                df['endX'].notna() & df['endY'].notna()]
    
    # Calcular rangos de tiempo para cada periodo
    rangos_tiempo = {}
    
    # Para el periodo 1
    if periodo == 1 or periodo == "2ª Parte":
        eventos_periodo1 = df[df["Periodo"] == 1]
        eventos_significativos1 = eventos_periodo1[eventos_periodo1["Mins"] > 0]
        
        if not eventos_significativos1.empty:
            min_minuto1 = eventos_significativos1["Mins"].min()
            max_minuto1 = eventos_significativos1["Mins"].max()
            rangos_tiempo[1] = {"inicio": min_minuto1, "fin": max_minuto1}
        else:
            # Si no hay eventos significativos, usar valores predeterminados
            rangos_tiempo[1] = {"inicio": 1, "fin": 45}
    
    # Para los periodos siguientes
    ultimo_fin = rangos_tiempo.get(1, {"fin": 45})["fin"]
    
    periodos_ordenados = sorted(df["Periodo"].unique())
    for p in periodos_ordenados:
        if p == 1:
            continue  # Ya procesamos el periodo 1
            
        # Encontrar eventos significativos para este periodo
        eventos_periodo = df[df["Periodo"] == p]
        eventos_significativos = eventos_periodo[eventos_periodo["Mins"] > 0]
        
        if not eventos_significativos.empty:
            min_minuto = eventos_significativos["Mins"].min()
            max_minuto = eventos_significativos["Mins"].max()
            rangos_tiempo[p] = {"inicio": min_minuto, "fin": max_minuto}
        else:
            # Si no hay eventos significativos, usar un rango estimado
            inicio = ultimo_fin + 1
            fin = inicio + 15  # Rango arbitrario de 15 minutos
            rangos_tiempo[p] = {"inicio": inicio, "fin": fin}
        
        ultimo_fin = rangos_tiempo[p]["fin"]
    
    # Si es 2ª Parte, filtrar periodos > 1, si no filtrar por el periodo específico
    if periodo == "2ª Parte":
        df_periodo = df_pases[df_pases["Periodo"] > 1].copy()
        
        # Calcular el rango para 2ª Parte
        periodos_segunda_parte = [p for p in periodos_ordenados if p > 1]
        if periodos_segunda_parte:
            primer_periodo_segunda = min(periodos_segunda_parte)
            ultimo_periodo_segunda = max(periodos_segunda_parte)
            
            inicio_segunda = rangos_tiempo.get(primer_periodo_segunda, {"inicio": 46})["inicio"]
            fin_segunda = rangos_tiempo.get(ultimo_periodo_segunda, {"fin": 90})["fin"]
            
            rango_minutos = f"(Min. {inicio_segunda}-{fin_segunda})"
        else:
            rango_minutos = ""
    else:
        df_periodo = df_pases[df_pases["Periodo"] == periodo].copy()
        
        # Extraer rango de minutos para el periodo específico
        if periodo in rangos_tiempo:
            inicio = rangos_tiempo[periodo]["inicio"]
            fin = rangos_tiempo[periodo]["fin"]
            rango_minutos = f"(Min. {inicio}-{fin})"
        else:
            rango_minutos = ""
    
    if df_periodo.empty:
        return None
    
    # Identificar jugadores sustitutos
    sustituciones = df[
        (df['Team'] == 'Valencia') & 
        (df['code'] == 'Sustitucion') & 
        (df['Secundary'].notna())
    ]
    
    sustitutos = set()
    if not sustituciones.empty:
        # El jugador que entra es el 'Secundary'
        sustitutos = set(sustituciones['Secundary'].unique())
    
    # Crear columnas de coordenadas convertidas
    df_periodo["startX_conv"], df_periodo["startY_conv"] = zip(*df_periodo.apply(
        lambda row: convertir_coordenadas(row["startX"], row["startY"]), axis=1
    ))
    df_periodo["endX_conv"], df_periodo["endY_conv"] = zip(*df_periodo.apply(
        lambda row: convertir_coordenadas(row["endX"], row["endY"]), axis=1
    ))

    # Combinar datos de pases para posiciones medias
    df_pases_combined = pd.concat([
        df_periodo[["Player", "startX_conv", "startY_conv"]].rename(columns={
            "startX_conv": "X", "startY_conv": "Y"
        }),
        df_periodo[["Secundary", "endX_conv", "endY_conv"]].rename(columns={
            "Secundary": "Player", "endX_conv": "X", "endY_conv": "Y"
        })
    ])

    # Posiciones medias
    posiciones_medias = df_pases_combined.groupby("Player")[["X", "Y"]].mean().reset_index()

    # Contar pases entre jugadores
    pases_entre_jugadores = df_periodo.groupby(["Player", "Secundary"]).size().reset_index(name="count")

    # Normalizaciones
    MAX_LINE_WIDTH = 18
    MAX_MARKER_SIZE = 3000

    if pases_entre_jugadores["count"].max() > 0:
        pases_entre_jugadores["width"] = (pases_entre_jugadores["count"] / pases_entre_jugadores["count"].max()) * MAX_LINE_WIDTH
    else:
        pases_entre_jugadores["width"] = 1

    # Intervenciones (pases dados + recibidos)
    intervenciones = pd.concat([df_periodo["Player"], df_periodo["Secundary"]]).value_counts().reset_index()
    intervenciones.columns = ["Player", "count"]

    posiciones_medias = posiciones_medias.merge(intervenciones, on="Player", how="left")
    if posiciones_medias["count"].max() > 0:
        posiciones_medias["marker_size"] = (posiciones_medias["count"] / posiciones_medias["count"].max()) * MAX_MARKER_SIZE
    else:
        posiciones_medias["marker_size"] = 100

    # Agregar información de si es sustituto
    posiciones_medias["es_sustituto"] = posiciones_medias["Player"].isin(sustitutos)

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

    # Dibujar conexiones (líneas de pases)
    for _, row in pases_entre_jugadores.iterrows():
        origen = posiciones_medias[posiciones_medias["Player"] == row["Player"]]
        destino = posiciones_medias[posiciones_medias["Player"] == row["Secundary"]]
        if not origen.empty and not destino.empty:
            ax.plot(
                [origen["X"].values[0], destino["X"].values[0]],
                [origen["Y"].values[0], destino["Y"].values[0]],
                color="Orange", lw=row["width"], alpha=0.6, zorder=1
            )

    # Variable para controlar si mostrar la leyenda
    mostrar_leyenda = False

    # Dibujar jugadores - usando marcadores diferentes para sustitutos solo en 2ª Parte
    for _, row in posiciones_medias.iterrows():
        numero_jugador = row["Player"].split(". ")[0] if ". " in row["Player"] else row["Player"]  # Ajuste para formato "3. Rubi"
        
        # Si es sustituto y estamos en la segunda parte, usar marcador cuadrado
        if row["es_sustituto"] and periodo == "2ª Parte":
            # Marcador cuadrado para sustitutos
            ax.scatter(row["X"], row["Y"], color="black", s=row["marker_size"], 
                       edgecolors="Orange", marker="s", zorder=5)
            mostrar_leyenda = True
        else:
            # Marcador circular para todos los demás casos
            ax.scatter(row["X"], row["Y"], color="black", s=row["marker_size"], 
                       edgecolors="Orange", marker="o", zorder=5)
        
        ax.text(row["X"], row["Y"], numero_jugador, color="white", fontsize=14,
                ha="center", va="center", zorder=6, fontweight="bold")

    # Lista de jugadores a la derecha
    nombres_jugadores = sorted(posiciones_medias["Player"])
    for idx, jugador in enumerate(nombres_jugadores):
        # Añadir indicador de sustituto solo en la segunda parte
        es_sustituto = jugador in sustitutos
        indicador = " (S)" if es_sustituto and periodo == "2ª Parte" else ""
        ax.text(125, 70 - (idx * 4), f"{jugador}{indicador}", color="black", fontsize=12, va="center")

    # Agregar leyenda solo para la 2ª Parte si hay sustitutos
    if mostrar_leyenda:
        from matplotlib.lines import Line2D
        leyenda_elementos = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='black', markersize=10, label='Titulares'),
            Line2D([0], [0], marker='s', color='w', markerfacecolor='black', markersize=10, label='Sustitutos')
        ]
        ax.legend(handles=leyenda_elementos, loc='upper right', fontsize=10)

    # Título según el periodo con rango de minutos
    if periodo == "2ª Parte":
        plt.suptitle(f"Red de Pases - 2ª Parte {rango_minutos}", color="black", fontsize=20)
    else:
        plt.suptitle(f"Red de Pases - Período {periodo} {rango_minutos}", color="black", fontsize=20)
    
    return fig

def generar_matriz_pases_para_pdf(df, opcion):
    """Genera una figura de matriz de pases para una opción específica"""
    # Filtrar pases
    df_pases = df[(df['Team'] == 'Valencia') & (df['code'] == 'Pases') & 
                df['Player'].notna() & df['Secundary'].notna()]
    
    if opcion == "Primera Parte (Periodo 1)":
        df_periodo = df_pases[df_pases["Periodo"] == 1].copy()
        titulo = "Matriz de Pases - Primera Parte (Periodo 1)"
    elif opcion == "Segunda Parte (Periodos >1)":
        df_periodo = df_pases[df_pases["Periodo"] > 1].copy()
        titulo = "Matriz de Pases - Segunda Parte (Periodos >1)"
    else:  # Matriz Total
        df_periodo = df_pases.copy()
        titulo = "Matriz de Pases - Todos los Períodos"

    if df_periodo.empty:
        return None

    # Contar pases entre jugadores
    matriz_pases = df_periodo.groupby(["Player", "Secundary"]).size().unstack(fill_value=0)
    
    # Simplificar nombres para la visualización
    matriz_pases_display = matriz_pases.copy()
    matriz_pases_display.index = [idx.split(". ")[1] if ". " in idx else idx for idx in matriz_pases.index]
    matriz_pases_display.columns = [col.split(". ")[1] if ". " in col else col for col in matriz_pases.columns]

    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(matriz_pases_display, annot=True, fmt="d", cmap="Oranges", 
                linewidths=0.5, linecolor="white", ax=ax)

    ax.set_title(titulo, fontsize=14, color="black")
    ax.set_xlabel("Receptor del Pase", fontsize=12)
    ax.set_ylabel("Jugador que pasa", fontsize=12)
    
    plt.tight_layout()
    return fig

def generar_faltas_para_pdf(df, opcion):
    """Genera una figura de faltas para una opción específica"""
    # Filtrar faltas
    faltas = df[
        df["Team"].str.contains("Valencia", case=False, na=False) &
        df["code"].str.contains("Faltas", case=False, na=False)
    ].copy()

    if faltas.empty:
        return None

    # Convertir coordenadas
    faltas["startX_conv"], faltas["startY_conv"] = zip(*faltas.apply(
        lambda row: convertir_coordenadas_reflejado(row["startX"], row["startY"]), axis=1
    ))

    if opcion == "Primera Parte (Periodo 1)":
        faltas_filtradas = faltas[faltas["Periodo"] == 1]
        titulo = "Faltas cometidas por Valencia - Primera Parte"
    elif opcion == "Segunda Parte (Periodos >1)":
        faltas_filtradas = faltas[faltas["Periodo"] > 1]
        titulo = "Faltas cometidas por Valencia - Segunda Parte"
    else:
        faltas_filtradas = faltas
        titulo = "Faltas cometidas por Valencia - Todo el partido"
    
    if faltas_filtradas.empty:
        return None

    pitch = Pitch(
        pitch_type="custom",
        pitch_length=120,
        pitch_width=80,
        line_color="black",
        pitch_color="#d0f0c0",
        linewidth=2
    )
    fig, ax = pitch.draw(figsize=(16, 11))

    franja_altura = 80 / 5
    for i in range(5):
        if i % 2 == 0:
            ax.fill_between([0, 120], i * franja_altura, (i + 1) * franja_altura, color="#a0c080", alpha=0.7)

    # Dibujar las faltas
    for _, row in faltas_filtradas.iterrows():
        x, y = row["startX_conv"], row["startY_conv"]
        periodo = row["Periodo"]
        color_falta = "orange" if periodo == 1 else "blue"
        ax.scatter(x, y, c=color_falta, s=100, edgecolors="black", marker="o", zorder=3)
        
        # Extraer nombre sin número
        nombre_jugador = row["Player"].split(". ")[1] if ". " in row["Player"] else row["Player"]
        ax.text(x, y+1.5, nombre_jugador, fontsize=12, color="black", ha="center", va="center")

    # Leyenda
    naranja_patch = mpatches.Patch(color="orange", label="Primera parte")
    azul_patch = mpatches.Patch(color="blue", label="Segunda parte")
    plt.legend(handles=[naranja_patch, azul_patch], loc="upper left", fontsize=12, title="Faltas", title_fontsize=13)

    plt.suptitle(titulo, color="black", fontsize=20)
    return fig

def generar_tiros_para_pdf(df, parte):
    """Genera una figura de tiros para una parte específica"""
    # Filtrar Tiros (ajustado para incluir "Finalizaciones")
    tiros = df[
        df["Team"].str.contains("Valencia", case=False, na=False) &
        (df["code"].str.contains("Tiros", case=False, na=False) | 
         df["code"].str.contains("Finalizaciones", case=False, na=False))
    ].copy()

    if tiros.empty:
        return None

    # Convertir coords
    tiros["startX_conv"], tiros["startY_conv"] = zip(*tiros.apply(
        lambda row: convertir_coordenadas_reflejado(row["startX"], row["startY"]), axis=1
    ))

    # Determinar parte basado en el periodo en lugar de minutos
    tiros["Parte"] = np.where(tiros["Periodo"] == 1, 1, 2)

    if parte == "Tiros Totales":
        tiros_filtrados = tiros
        titulo = "Tiros Totales del Valencia CF"
    else:
        tiros_filtrados = tiros[tiros["Parte"] == parte]
        titulo = f"Tiros del Valencia CF - Parte {parte}"

    if tiros_filtrados.empty:
        return None

    pitch = Pitch(
        pitch_type="custom",
        pitch_length=120,
        pitch_width=80,
        line_color="black",
        pitch_color="#d0f0c0",
        linewidth=2
    )
    fig, ax = pitch.draw(figsize=(16, 11))

    franja_altura = 80 / 5
    for i in range(5):
        if i % 2 == 0:
            ax.fill_between([0, 120], i * franja_altura, (i + 1) * franja_altura, color="#a0c080", alpha=0.7)

    # Contador para tipos de tiros
    conteo_tiros = {"gol": 0, "a_puerta": 0, "fuera": 0, "otro": 0}
    
    for _, row in tiros_filtrados.iterrows():
        x, y = row["startX_conv"], row["startY_conv"]
        
        # Color según tipo - ajustado para manejar diferentes formatos
        if isinstance(row.get("text"), str) and "Gol" in row["text"]:
            color_tiro = "green"
            conteo_tiros["gol"] += 1
            marker = "*"
            size = 200
        elif row.get("group") == "A puerta" or row.get("group") == "Dentro":
            color_tiro = "blue"
            conteo_tiros["a_puerta"] += 1
            marker = "o"
            size = 120
        elif row.get("group") == "Fuera":
            color_tiro = "red"
            conteo_tiros["fuera"] += 1
            marker = "o"
            size = 120
        else:
            color_tiro = "black"
            conteo_tiros["otro"] += 1
            marker = "o"
            size = 100

        ax.scatter(x, y, c=color_tiro, s=size, edgecolors="black", marker=marker, zorder=3)
        
        # Extraer nombre sin número
        nombre_jugador = row["Player"].split(". ")[1] if ". " in row["Player"] else row["Player"]
        ax.text(x, y+1.5, nombre_jugador, fontsize=12, color="black", ha="center", va="center",
               bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

    # Leyenda
    legend_patches = [
        mpatches.Patch(color="green", label="Gol"),
        mpatches.Patch(color="blue", label="Tiro a puerta"),
        mpatches.Patch(color="red", label="Tiro fuera"),
        mpatches.Patch(color="black", label="No clasificado")
    ]
    plt.legend(handles=legend_patches, loc="upper left", fontsize=12, title="Tipo de Tiro", title_fontsize=13)

    plt.suptitle(titulo, color="black", fontsize=20)
    
    # Añadir estadísticas como texto en la parte inferior
    total_tiros = sum(conteo_tiros.values())
    stats_text = f"Total: {total_tiros} tiros | Goles: {conteo_tiros['gol']} | A puerta: {conteo_tiros['a_puerta']} | Fuera: {conteo_tiros['fuera']}"
    plt.figtext(0.5, 0.01, stats_text, ha="center", fontsize=14, 
               bbox=dict(facecolor='white', alpha=0.8, edgecolor='black'))
    
    return fig

def generar_recuperaciones_para_pdf(df, opcion):
    """Genera una figura de recuperaciones para una opción específica"""
    # Filtrar recuperaciones
    recuperaciones = df[
        df["Team"].str.contains("Valencia", case=False, na=False) &
        df["code"].str.contains("Recuperaciones", case=False, na=False)
    ].copy()

    if recuperaciones.empty:
        return None

    # Convertir coordenadas
    recuperaciones["startX_conv"], recuperaciones["startY_conv"] = zip(*recuperaciones.apply(
        lambda row: convertir_coordenadas_reflejado(row["startX"], row["startY"]), axis=1
    ))
    
    if opcion == "Primera Parte (Periodo 1)":
        recuperaciones_filtradas = recuperaciones[recuperaciones["Periodo"] == 1]
        titulo = "Recuperaciones del Valencia - Primera Parte"
    elif opcion == "Segunda Parte (Periodos >1)":
        recuperaciones_filtradas = recuperaciones[recuperaciones["Periodo"] > 1]
        titulo = "Recuperaciones del Valencia - Segunda Parte"
    else:
        recuperaciones_filtradas = recuperaciones
        titulo = "Recuperaciones del Valencia - Todo el partido"
    
    if recuperaciones_filtradas.empty:
        return None

    # Determinar zona
    def determinar_zona(x):
        # Ajusta el criterio según tus coordenadas:
        return "Campo Propio" if x > 60 else "Campo Contrario"

    recuperaciones_filtradas["Zona"] = recuperaciones_filtradas["startX_conv"].apply(determinar_zona)

    pitch = Pitch(
        pitch_type="custom",
        pitch_length=120,
        pitch_width=80,
        line_color="black",
        pitch_color="#d0f0c0",
        linewidth=2
    )
    fig, ax = pitch.draw(figsize=(16, 11))

    franja_altura = 80 / 5
    for i in range(5):
        if i % 2 == 0:
            ax.fill_between([0, 120], i * franja_altura, (i + 1) * franja_altura, color="#a0c080", alpha=0.7)

    # Dibujar recuperaciones
    for _, row in recuperaciones_filtradas.iterrows():
        x, y = row["startX_conv"], row["startY_conv"]
        color_recuperacion = "blue" if row["Zona"] == "Campo Propio" else "red"
        ax.scatter(x, y, c=color_recuperacion, s=120, edgecolors="black", marker="o", zorder=3)
        
        # Extraer nombre sin número
        nombre_jugador = row["Player"].split(". ")[1] if ". " in row["Player"] else row["Player"]
        ax.text(x, y+1.5, nombre_jugador, fontsize=12, color="black", ha="center", va="center",
               bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

    azul_patch = mpatches.Patch(color="blue", label="Campo Propio")
    rojo_patch = mpatches.Patch(color="red", label="Campo Contrario")
    plt.legend(handles=[azul_patch, rojo_patch], loc="upper left", fontsize=12,
               title="Zona de Recuperación", title_fontsize=13)

    plt.suptitle(titulo, color="black", fontsize=20)
    return fig

def generar_pases_especificos_para_pdf(df, tipo_pase, parte):
    """Genera una figura de pases específicos para un tipo y parte específicos"""
    # Configurar filtros según el tipo de pase
    if tipo_pase == "Futbolista de Cara":
        code_filtro = "Encontrar Futbolista de cara"
        color_linea = "pink"
        titulo = f"Encontrar Futbolista de Cara - Parte {parte}"
    elif tipo_pase == "En Profundidad":
        code_filtro = "Encontrar Futbolista en profundidad"
        color_linea = "green"
        titulo = f"Encontrar Futbolista en Profundidad - Parte {parte}"
    elif tipo_pase == "Atacar el Área":
        code_filtro = "Atacar el área"
        group_filtro = None  # Todos los tipos
        color_linea = "purple"
        titulo = f"Atacar el Área - Parte {parte}"
    elif tipo_pase == "Atacar el Área con +3":
        code_filtro = "Atacar el área"
        group_filtro = "Atacar el área con +3"
        color_linea = "blue"
        titulo = f"Atacar el Área con +3 - Parte {parte}"
    else:
        return None
    
    # Filtrar datos
    if tipo_pase == "Atacar el Área con +3":
        acciones = df[
            (df['Team'] == 'Valencia') &
            (df['code'] == code_filtro) &
            (df['group'] == group_filtro)
        ].copy()
    else:
        acciones = df[
            (df['Team'] == 'Valencia') &
            (df['code'] == code_filtro)
        ].copy()
    
    if acciones.empty:
        return None
    
    # Filtrar por parte
    acciones["Parte"] = np.where(acciones["Periodo"] == 1, 1, 2)
    
    if parte != "Pases Totales":
        acciones = acciones[acciones["Parte"] == parte]
    
    if acciones.empty:
        return None
    
    # Aplicar la conversión de coordenadas
    acciones[['startX_conv', 'startY_conv']] = acciones.apply(
        lambda row: pd.Series(convertir_coordenadas_reflejado(row['startX'], row['startY'])), 
        axis=1
    )
    acciones[['endX_conv', 'endY_conv']] = acciones.apply(
        lambda row: pd.Series(convertir_coordenadas_reflejado(row['endX'], row['endY'])), 
        axis=1
    )
    
    # Identificar jugadores suplentes basados en su primera aparición
    primera_aparicion = df[df['Player'].notna()].groupby('Player')['Mins'].min().reset_index()
    suplentes = primera_aparicion[primera_aparicion['Mins'] > 1]['Player'].tolist()
    
    # Crear figura para el campo
    pitch = Pitch(
        pitch_type='custom', 
        pitch_length=120, 
        pitch_width=80, 
        line_color='black', 
        pitch_color='#d0f0c0', 
        linewidth=2
    )
    
    fig, ax = plt.subplots(figsize=(16, 11))
    pitch.draw(ax=ax)
    
    # Añadir franjas horizontales
    franja_altura = 80 / 5
    for i in range(5):
        if i % 2 == 0:
            ax.fill_between([0, 120], i * franja_altura, (i + 1) * franja_altura, color="#a0c080", alpha=0.7)
    
    fig.set_facecolor("white")
    
    # Dibujar las acciones con líneas y puntos
    for _, row in acciones.iterrows():
        start_x, start_y = row['startX_conv'], row['startY_conv']
        end_x, end_y = row['endX_conv'], row['endY_conv']
        receptor = row['Secundary']
        pasador = row['Player']
        
        # Dibujar la línea de pase
        ax.plot([start_x, end_x], [start_y, end_y], color=color_linea, lw=2, alpha=0.7, zorder=2)
        
        # Determinar si el jugador que pasa es suplente
        es_suplente_pasador = pasador in suplentes
        marker_pasador = 's' if es_suplente_pasador else 'o'  # cuadrado para suplentes, círculo para titulares
        
        # Dibujar el marcador del jugador que da el pase
        ax.scatter(start_x, start_y, c='black', s=100, edgecolors=color_linea, marker=marker_pasador, zorder=3)
        
        # Extraer nombre sin número
        nombre_jugador = pasador.split(". ")[1] if ". " in pasador else pasador
        ax.text(start_x, start_y+1.5, nombre_jugador, fontsize=12, color='black', ha='center', va='center',
               bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
        
        # Si hay receptor, dibujar su círculo y su nombre
        if pd.notna(receptor):
            # Determinar si el receptor es suplente
            es_suplente_receptor = receptor in suplentes
            marker_receptor = 's' if es_suplente_receptor else 'o'  # cuadrado para suplentes, círculo para titulares
            
            ax.scatter(end_x, end_y, c='black', s=100, edgecolors=color_linea, marker=marker_receptor, zorder=3)
            # Extraer nombre del receptor
            nombre_receptor = receptor.split(". ")[1] if ". " in receptor else receptor
            ax.text(end_x, end_y+1.5, nombre_receptor, fontsize=12, color='black', ha='center', va='center',
                   bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
        else:
            ax.scatter(end_x, end_y, c='black', s=100, edgecolors=color_linea, marker='x', zorder=3)
    
    # Añadir leyenda para titulares y suplentes
    from matplotlib.lines import Line2D
    custom_legend = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='black', 
            markeredgecolor=color_linea, markersize=10, label='Titular'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor='black', 
            markeredgecolor=color_linea, markersize=10, label='Suplente'),
        mpatches.Patch(color=color_linea, label=tipo_pase)
    ]
    ax.legend(handles=custom_legend, loc='upper right', fontsize=10)
    
    # Añadir título
    plt.suptitle(titulo, color='black', fontsize=20)
    
    # Añadir estadísticas como texto en la parte inferior
    total_pases = len(acciones)
    stats_text = f"Total: {total_pases} pases de este tipo"
    plt.figtext(0.5, 0.01, stats_text, ha="center", fontsize=14, 
               bbox=dict(facecolor='white', alpha=0.8, edgecolor='black'))
    
    return fig

def download_session_charts(equipo_nombre, archivo_nombre, df):
    """
    Genera un PDF con todos los gráficos para todos los periodos disponibles
    """
    # Crear un buffer para el PDF
    buffer = io.BytesIO()
    
    # Crear el documento PDF
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(A4),
        rightMargin=72, leftMargin=72,
        topMargin=72, bottomMargin=72
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    if 'CustomTitle' not in styles:
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#FF6600'),
            spaceAfter=24
        ))
    if 'CustomSubTitle' not in styles:
        styles.add(ParagraphStyle(
            name='CustomSubTitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1a5276'),
            spaceAfter=12
        ))
    
    # Elementos para el PDF
    elements = []
    
    # ---- PORTADA ----
    # Título principal centrado
    elements.append(Paragraph(f"Academia Valencia CF - Informe completo", styles["CustomTitle"]))
    elements.append(Spacer(1, 0.2*inch))
    
    # Añadir escudo del Valencia CF desde la ruta local
    escudo_path = "assets/valencia.png"
    if os.path.exists(escudo_path):
        valencia_logo = Image(escudo_path, width=3*inch, height=3*inch)
        elements.append(valencia_logo)
    elements.append(Spacer(1, 0.5*inch))
    
    elements.append(Paragraph(f"Equipo: {equipo_nombre}", styles["CustomSubTitle"]))
    elements.append(Paragraph(f"Partido: {archivo_nombre}", styles["CustomSubTitle"]))
    
    # Fecha y hora
    fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"Generado: {fecha_hora}", styles["Normal"]))
    
    # Agregar un salto de página después de la portada
    elements.append(PageBreak())
    
    # Guardar el estado actual de plt
    original_fignums = plt.get_fignums()
    
    # Cerramos las figuras existentes para no confundir
    plt.close('all')
    
    # Lista para almacenar todas las figuras generadas
    all_figures = []
    all_titles = []
    
    # 1. Generar todas las redes de pases
    # Determinar periodos disponibles para red de pases
    df_pases = df[(df['Team'] == 'Valencia') & (df['code'] == 'Pases')]
    periodos_disponibles = sorted(df_pases["Periodo"].unique())
    
    # Generar red de pases para cada periodo
    for periodo in periodos_disponibles:
        fig = generar_red_pases_para_pdf(df, periodo)
        if fig:
            all_figures.append(fig)
            all_titles.append(f"Red de Pases - Periodo {periodo}")
    
    # Generar red de pases para la 2ª Parte si hay periodos > 1
    if any(p > 1 for p in periodos_disponibles):
        fig = generar_red_pases_para_pdf(df, "2ª Parte")
        if fig:
            all_figures.append(fig)
            all_titles.append("Red de Pases - 2ª Parte")
    
    # 2. Matriz de pases (total y por partes)
    for opcion in ["Primera Parte (Periodo 1)", "Segunda Parte (Periodos >1)", "Matriz Total"]:
        fig = generar_matriz_pases_para_pdf(df, opcion)
        if fig:
            all_figures.append(fig)
            all_titles.append(f"Matriz de Pases - {opcion}")
    
    # 3. Faltas (todas y por partes)
    for opcion in ["Todas las faltas", "Primera Parte (Periodo 1)", "Segunda Parte (Periodos >1)"]:
        fig = generar_faltas_para_pdf(df, opcion)
        if fig:
            all_figures.append(fig)
            all_titles.append(f"Faltas - {opcion}")
    
    # 4. Tiros (totales y por partes)
    for parte in [1, 2, "Tiros Totales"]:
        fig = generar_tiros_para_pdf(df, parte)
        if fig:
            all_figures.append(fig)
            all_titles.append(f"Tiros - {parte if parte != 'Tiros Totales' else 'Totales'}")
    
    # 5. Recuperaciones (todas y por partes)
    for opcion in ["Todas las recuperaciones", "Primera Parte (Periodo 1)", "Segunda Parte (Periodos >1)"]:
        fig = generar_recuperaciones_para_pdf(df, opcion)
        if fig:
            all_figures.append(fig)
            all_titles.append(f"Recuperaciones - {opcion}")
    
    # 6. Pases específicos (todos los tipos, para las partes 1 y 2)
    tipos_pases = ["Futbolista de Cara", "En Profundidad", "Atacar el Área", "Atacar el Área con +3"]
    partes = [1, 2]
    
    for tipo in tipos_pases:
        for parte in partes:
            fig = generar_pases_especificos_para_pdf(df, tipo, parte)
            if fig:
                all_figures.append(fig)
                all_titles.append(f"Pases Específicos: {tipo} - Parte {parte}")
    
    # Agregar cada gráfico con su título al PDF
    for i, (fig, titulo) in enumerate(zip(all_figures, all_titles)):
        # Título del gráfico
        elements.append(Paragraph(titulo, styles["CustomSubTitle"]))
        elements.append(Spacer(1, 0.2*inch))
        
        # Convertir la figura a imagen
        img = figure_to_image(fig)
        elements.append(img)
        
        # Agregar salto de página después de cada gráfico excepto el último
        if i < len(all_figures) - 1:
            elements.append(PageBreak())
    
    # Si no hay figuras, agregar mensaje
    if len(all_figures) == 0:
        elements.append(Paragraph("No se encontraron gráficos para incluir en el informe.", styles["Normal"]))
    
    # Construir PDF
    doc.build(elements)
    
    # Cerrar todas las figuras generadas
    for fig in all_figures:
        plt.close(fig)
    
    # Restaurar figuras originales
    for num in original_fignums:
        plt.figure(num)
    
    # Volver al inicio del buffer y obtener el valor
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    # Generar nombre de archivo
    filename = f"informe_completo_{equipo_nombre}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # Crear botón de descarga
    return create_download_button(pdf_bytes, filename=filename)