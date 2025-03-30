import os
import io
import base64
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import streamlit as st
import plotly.graph_objects as go

def create_pdf_download_link(pdf_bytes, filename="reporte.pdf"):
    """
    Crea un enlace de descarga para un archivo PDF.
    
    Args:
        pdf_bytes: Bytes del archivo PDF
        filename: Nombre del archivo a descargar
        
    Returns:
        HTML con enlace de descarga
    """
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" class="btn-download">Descargar PDF</a>'
    return href

def convert_plotly_to_image(fig):
    """
    Convierte una figura de Plotly a una imagen para incluir en PDF.
    
    Args:
        fig: Figura de Plotly
        
    Returns:
        bytes de la imagen
    """
    img_bytes = fig.to_image(format="png", scale=2)
    return img_bytes

def convert_matplotlib_to_image(fig):
    """
    Convierte una figura de Matplotlib a una imagen para incluir en PDF.
    
    Args:
        fig: Figura de Matplotlib
        
    Returns:
        bytes de la imagen
    """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    return buf.getvalue()

def generar_pdf_individuales(jugador_info, df_jugador, estadisticas, figuras_plotly, figuras_mpl=None, minutos_jugados=None):
    """
    Genera un PDF con estadísticas individuales de un jugador.
    
    Args:
        jugador_info: Diccionario con información del jugador
        df_jugador: DataFrame con datos del jugador
        estadisticas: Diccionario con estadísticas del jugador
        figuras_plotly: Lista de figuras de Plotly
        figuras_mpl: Lista de figuras de Matplotlib (opcional)
        minutos_jugados: Minutos jugados por el jugador
        
    Returns:
        Bytes del PDF generado
    """
    buffer = io.BytesIO()
    
    # Crear documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    
    # Estilos
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Title', alignment=TA_CENTER, fontSize=16, spaceAfter=12))
    styles.add(ParagraphStyle(name='Subtitle', alignment=TA_CENTER, fontSize=14, spaceAfter=6))
    styles.add(ParagraphStyle(name='Normal', fontSize=12, spaceAfter=6))
    
    # Elementos a agregar al PDF
    elements = []
    
    # Título y nombre del jugador
    nombre_jugador = jugador_info.get('nombre', '') if jugador_info else df_jugador['Player'].iloc[0]
    elements.append(Paragraph(f"Informe de Rendimiento", styles['Title']))
    elements.append(Paragraph(f"{nombre_jugador}", styles['Subtitle']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Información general
    equipo = "Valencia CF"
    posicion = jugador_info.get('posicion', 'Jugador') if jugador_info else 'Jugador'
    
    # Tabla de información
    data = [
        ["Equipo:", equipo],
        ["Posición:", posicion],
        ["Minutos jugados:", str(minutos_jugados)]
    ]
    
    info_table = Table(data, colWidths=[2*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Estadísticas principales
    elements.append(Paragraph("Estadísticas Principales", styles['Subtitle']))
    
    # Definir estadísticas clave a mostrar
    estadisticas_clave = [
        "Pases completados", "Pases fallados", "Precisión de pases",
        "Finalizaciones", "Goles", "Recuperaciones", "Faltas cometidas"
    ]
    
    # Extraer estadísticas del DataFrame o del diccionario de estadísticas
    datos_estadisticas = []
    
    # Añadir estadísticas disponibles
    if estadisticas:
        for i in range(0, len(estadisticas_clave), 2):
            fila = []
            for j in range(2):
                if i + j < len(estadisticas_clave):
                    clave = estadisticas_clave[i + j]
                    valor = estadisticas.get(clave.lower().replace(" ", "_"), "N/A")
                    fila.extend([clave + ":", str(valor)])
            datos_estadisticas.append(fila)
    
    # Si no hay estadísticas, intentar extraerlas del DataFrame
    else:
        pases_completados = df_jugador[df_jugador["code"] == "Pases"]["Secundary"].notna().sum()
        pases_fallados = len(df_jugador[df_jugador["code"] == "Pases"]) - pases_completados
        precision = round((pases_completados / (pases_completados + pases_fallados) * 100), 1) if (pases_completados + pases_fallados) > 0 else 0
        
        finalizaciones = len(df_jugador[df_jugador["code"] == "Finalizaciones"])
        goles = df_jugador[(df_jugador["code"] == "Finalizaciones") & (df_jugador["text"] == "Gol")].shape[0]
        recuperaciones = len(df_jugador[df_jugador["code"] == "Recuperaciones"])
        faltas = len(df_jugador[df_jugador["code"] == "Faltas"])
        
        datos_estadisticas = [
            ["Pases completados:", str(pases_completados), "Pases fallados:", str(pases_fallados)],
            ["Precisión de pases:", f"{precision}%", "Finalizaciones:", str(finalizaciones)],
            ["Goles:", str(goles), "Recuperaciones:", str(recuperaciones)],
            ["Faltas cometidas:", str(faltas)]
        ]
    
    # Crear tabla de estadísticas
    stats_table = Table(datos_estadisticas, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    
    elements.append(stats_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Convertir figuras de Plotly a imágenes y agregar al PDF
    if figuras_plotly:
        elements.append(Paragraph("Visualización de Rendimiento", styles['Subtitle']))
        
        for i, fig in enumerate(figuras_plotly):
            img_bytes = convert_plotly_to_image(fig)
            img = Image(io.BytesIO(img_bytes), width=6*inch, height=4*inch)
            elements.append(img)
            elements.append(Spacer(1, 0.2*inch))
    
    # Agregar figuras de Matplotlib si existen
    if figuras_mpl:
        for i, fig in enumerate(figuras_mpl):
            img_bytes = convert_matplotlib_to_image(fig)
            img = Image(io.BytesIO(img_bytes), width=6*inch, height=4*inch)
            elements.append(img)
            elements.append(Spacer(1, 0.2*inch))
    
    # Generar PDF
    doc.build(elements)
    
    # Obtener bytes del PDF
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

def generar_pdf_totales(jugador_info, datos_partidos, total_stats, figuras_plotly):
    """
    Genera un PDF con estadísticas totales de un jugador en varios partidos.
    
    Args:
        jugador_info: Diccionario con información del jugador
        datos_partidos: Lista de diccionarios con datos de partidos
        total_stats: Diccionario con estadísticas acumuladas
        figuras_plotly: Lista de figuras de Plotly
        
    Returns:
        Bytes del PDF generado
    """
    buffer = io.BytesIO()
    
    # Crear documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    
    # Estilos
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Title', alignment=TA_CENTER, fontSize=16, spaceAfter=12))
    styles.add(ParagraphStyle(name='Subtitle', alignment=TA_CENTER, fontSize=14, spaceAfter=6))
    styles.add(ParagraphStyle(name='Normal', fontSize=12, spaceAfter=6))
    
    # Elementos a agregar al PDF
    elements = []
    
    # Título y nombre del jugador
    nombre_jugador = jugador_info.get('nombre', '') if jugador_info else datos_partidos[0]['nombre'].split('_')[1].split('.')[0] if datos_partidos else "Jugador"
    elements.append(Paragraph(f"Informe de Rendimiento Acumulado", styles['Title']))
    elements.append(Paragraph(f"{nombre_jugador}", styles['Subtitle']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Información general
    equipo = "Valencia CF"
    posicion = jugador_info.get('posicion', 'Jugador') if jugador_info else 'Jugador'
    num_partidos = len(datos_partidos)
    
    # Tabla de información
    data = [
        ["Equipo:", equipo],
        ["Posición:", posicion],
        ["Partidos analizados:", str(num_partidos)],
        ["Minutos totales:", str(total_stats['minutos'])]
    ]
    
    info_table = Table(data, colWidths=[2*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Estadísticas acumuladas
    elements.append(Paragraph("Estadísticas Acumuladas", styles['Subtitle']))
    
    # Definir estadísticas a mostrar según si es portero o no
    es_portero = 'portero' in posicion.lower() if posicion else False
    
    if es_portero:
        # Estadísticas para porteros
        precision_pases = round((total_stats['pases_completados'] / (total_stats['pases_completados'] + total_stats['pases_fallados']) * 100), 1) if (total_stats['pases_completados'] + total_stats['pases_fallados']) > 0 else 0
        efectividad_paradas = round((total_stats['paradas'] / (total_stats['paradas'] + total_stats['goles_recibidos']) * 100), 1) if (total_stats['paradas'] + total_stats['goles_recibidos']) > 0 else 0
        
        datos_estadisticas = [
            ["Paradas:", str(total_stats['paradas']), "Goles recibidos:", str(total_stats['goles_recibidos'])],
            ["Tiros a puerta recibidos:", str(total_stats['tiros_recibidos_puerta']), "Efectividad:", f"{efectividad_paradas}%"],
            ["Pases completados:", str(total_stats['pases_completados']), "Pases fallados:", str(total_stats['pases_fallados'])],
            ["Precisión de pases:", f"{precision_pases}%"]
        ]
    else:
        # Estadísticas para jugadores de campo
        precision_pases = round((total_stats['pases_completados'] / (total_stats['pases_completados'] + total_stats['pases_fallados']) * 100), 1) if (total_stats['pases_completados'] + total_stats['pases_fallados']) > 0 else 0
        
        datos_estadisticas = [
            ["Pases completados:", str(total_stats['pases_completados']), "Pases fallados:", str(total_stats['pases_fallados'])],
            ["Precisión de pases:", f"{precision_pases}%", "Finalizaciones:", str(total_stats['finalizaciones'])],
            ["Goles:", str(total_stats['goles']), "Recuperaciones:", str(total_stats['recuperaciones'])],
            ["Encontrar en profundidad:", str(total_stats['profundidad']), "Encontrar de cara:", str(total_stats['cara'])],
            ["Atacar el área:", str(total_stats['area']), "Faltas:", str(total_stats['faltas'])]
        ]
    
    # Crear tabla de estadísticas
    stats_table = Table(datos_estadisticas, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    
    elements.append(stats_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Lista de partidos analizados
    elements.append(Paragraph("Partidos Analizados", styles['Subtitle']))
    
    partidos_data = [["Fecha", "Rival", "Minutos"]]
    for partido in datos_partidos:
        fecha = partido['fecha'].strftime('%d/%m/%Y') if partido['fecha'] else "Sin fecha"
        rival = partido['rival']
        minutos = str(partido['minutos_jugados'])
        partidos_data.append([fecha, rival, minutos])
    
    partidos_table = Table(partidos_data, colWidths=[1.5*inch, 3*inch, 1*inch])
    partidos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    
    elements.append(partidos_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Convertir figuras de Plotly a imágenes y agregar al PDF
    if figuras_plotly:
        elements.append(Paragraph("Visualización de Rendimiento", styles['Subtitle']))
        
        for i, fig in enumerate(figuras_plotly):
            img_bytes = convert_plotly_to_image(fig)
            img = Image(io.BytesIO(img_bytes), width=6*inch, height=4*inch)
            elements.append(img)
            elements.append(Spacer(1, 0.2*inch))
    
    # Generar PDF
    doc.build(elements)
    
    # Obtener bytes del PDF
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

def agregar_boton_pdf_individuales(jugador_info, df_jugador, figuras_plotly, figuras_mpl=None, minutos_jugados=None):
    """
    Agrega un botón para generar y descargar un PDF con estadísticas individuales.
    """
    if st.button("📄 Generar Informe PDF"):
        with st.spinner("Generando PDF..."):
            try:
                # Extraer estadísticas del DataFrame
                estadisticas = {}
                
                # Generar PDF
                pdf_bytes = generar_pdf_individuales(
                    jugador_info, 
                    df_jugador, 
                    estadisticas, 
                    figuras_plotly, 
                    figuras_mpl,
                    minutos_jugados
                )
                
                # Nombre del archivo
                nombre_jugador = jugador_info.get('nombre', '') if jugador_info else df_jugador['Player'].iloc[0]
                filename = f"informe_{nombre_jugador.replace(' ', '_').lower()}.pdf"
                
                # Mostrar enlace de descarga
                st.markdown(
                    create_pdf_download_link(pdf_bytes, filename),
                    unsafe_allow_html=True
                )
                
                st.success("¡PDF generado correctamente!")
                
            except Exception as e:
                st.error(f"Error al generar el PDF: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

def agregar_boton_pdf_totales(jugador_info, datos_partidos, total_stats, figuras_plotly):
    """
    Agrega un botón para generar y descargar un PDF con estadísticas totales.
    """
    if st.button("📄 Generar Informe PDF"):
        with st.spinner("Generando PDF..."):
            try:
                # Generar PDF
                pdf_bytes = generar_pdf_totales(
                    jugador_info, 
                    datos_partidos, 
                    total_stats, 
                    figuras_plotly
                )
                
                # Nombre del archivo
                nombre_jugador = jugador_info.get('nombre', '') if jugador_info else "jugador"
                filename = f"informe_total_{nombre_jugador.replace(' ', '_').lower()}.pdf"
                
                # Mostrar enlace de descarga
                st.markdown(
                    create_pdf_download_link(pdf_bytes, filename),
                    unsafe_allow_html=True
                )
                
                st.success("¡PDF generado correctamente!")
                
            except Exception as e:
                st.error(f"Error al generar el PDF: {str(e)}")
                import traceback
                st.code(traceback.format_exc())