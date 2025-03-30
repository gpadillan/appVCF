import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.patches as mpatches
from mplsoccer import Pitch
from modules.pdf_export import download_single_chart, download_session_charts

# Diccionario para almacenar todas las figuras generadas
all_figs = {}

# =========================
# Funciones Auxiliares
# =========================

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

# =========================
# 1) Red de Pases
# =========================

def red_de_pases(df):
    """
    Genera el gráfico de Red de Pases:
    - Filtra por 'Periodo' seleccionado o muestra la segunda parte completa.
    - Usa 'startX', 'startY', 'endX', 'endY' y 
      jugadores en 'Player' y 'Secundary'.
    - Muestra el rango de tiempo (minutos) correspondiente a cada periodo.
    - Diferencia visualmente a los jugadores que entraron como sustitutos.
    """

    st.subheader("📌 Red de Pases del Valencia")

    if df is None or df.empty:
        st.warning("⚠️ No hay datos disponibles para generar la Red de Pases.")
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

    # Comprobar columnas necesarias
    cols_req = ["Player", "Secundary", "startX", "startY", "endX", "endY", "Periodo"]
    if not all(col in df.columns for col in cols_req):
        st.error(f"❌ Faltan columnas. Necesario: {cols_req}")
        return

    # Filtrar pases primero (tomando en cuenta que el código es "Pases" no "Pase")
    df_pases = df[(df['Team'] == 'Valencia') & (df['code'] == 'Pases') & 
                 df['Player'].notna() & df['Secundary'].notna() & 
                 df['startX'].notna() & df['startY'].notna() & 
                 df['endX'].notna() & df['endY'].notna()]
    
    if df_pases.empty:
        st.warning("⚠️ No hay datos de pases válidos para analizar.")
        return
    
    # PASO 1: Calcular dinámicamente los rangos de tiempo para cada periodo
    rangos_tiempo = {}
    periodos_ordenados = sorted(df_pases["Periodo"].unique())
    
    # Para el periodo 1
    if 1 in periodos_ordenados:
        # Encontrar eventos significativos (minuto > 0)
        eventos_periodo1 = df[df["Periodo"] == 1]
        eventos_significativos1 = eventos_periodo1[eventos_periodo1["Mins"] > 0]
        
        if not eventos_significativos1.empty:
            min_minuto1 = eventos_significativos1["Mins"].min()
            max_minuto1 = eventos_significativos1["Mins"].max()
            rangos_tiempo[1] = {"inicio": min_minuto1, "fin": max_minuto1}
        else:
            # Si no hay eventos significativos, usar valores predeterminados
            rangos_tiempo[1] = {"inicio": 0, "fin": 45}
    
    # Para los periodos siguientes
    ultimo_fin = rangos_tiempo.get(1, {"fin": 45})["fin"]
    
    for periodo in periodos_ordenados:
        if periodo == 1:
            continue  # Ya procesamos el periodo 1
            
        # Encontrar eventos significativos para este periodo
        eventos_periodo = df[df["Periodo"] == periodo]
        eventos_significativos = eventos_periodo[eventos_periodo["Mins"] > 0]
        
        if not eventos_significativos.empty:
            max_minuto = eventos_significativos["Mins"].max()
            # El inicio es el fin del último periodo + 1
            inicio = ultimo_fin + 1
            rangos_tiempo[periodo] = {"inicio": inicio, "fin": max_minuto}
            ultimo_fin = max_minuto
        else:
            # Si no hay eventos significativos, usar un rango estimado
            inicio = ultimo_fin + 1
            fin = inicio + 10  # Rango arbitrario de 10 minutos
            rangos_tiempo[periodo] = {"inicio": inicio, "fin": fin}
            ultimo_fin = fin
    
    # Calcular rango para la 2ª Parte
    periodos_segunda_parte = [p for p in periodos_ordenados if p > 1]
    if periodos_segunda_parte:
        primer_periodo = min(periodos_ordenados)
        ultimo_periodo = max(periodos_ordenados)
        
        inicio_segunda = rangos_tiempo[primer_periodo]["fin"] + 1
        fin_segunda = rangos_tiempo[ultimo_periodo]["fin"]
        
        rangos_tiempo["2ª Parte"] = {"inicio": inicio_segunda, "fin": fin_segunda}
    
    # PASO 2: Identificar jugadores sustitutos
    sustituciones = df[
        (df['Team'] == 'Valencia') & 
        (df['code'] == 'Sustitucion') & 
        (df['Secundary'].notna()) & 
        (df['Mins'] >= rangos_tiempo.get(1, {"fin": 45})["fin"])  # Después del primer periodo
    ]
    
    sustitutos = set()
    if not sustituciones.empty:
        # El jugador que entra es el 'Secundary'
        sustitutos = set(sustituciones['Secundary'].unique())
    
    # PASO 3: Preparar opciones de periodos y selector
    opciones_periodos = periodos_ordenados.copy()
    if periodos_segunda_parte:
        opciones_periodos.append("2ª Parte")
    
    # Elegir el período
    periodo_seleccionado = st.selectbox("📊 Selecciona el período del partido:", opciones_periodos)

    # PASO 4: Filtrar datos según selección
    if periodo_seleccionado == "2ª Parte":
        # Filtrar todos los pases de la segunda parte (periodos > 1)
        df_periodo = df_pases[df_pases["Periodo"] > 1].copy()
        if df_periodo.empty:
            st.warning("⚠️ No hay datos para la segunda parte.")
            return
    else:
        # Filtrar por el periodo individual seleccionado
        df_periodo = df_pases[df_pases["Periodo"] == periodo_seleccionado].copy()
        if df_periodo.empty:
            st.warning(f"⚠️ No hay datos para el período {periodo_seleccionado}.")
            return
    
    # PASO 5: Mostrar información del rango de tiempo
    if periodo_seleccionado in rangos_tiempo:
        inicio = rangos_tiempo[periodo_seleccionado]["inicio"]
        fin = rangos_tiempo[periodo_seleccionado]["fin"]
        
        if periodo_seleccionado == "2ª Parte":
            st.info(f"📝 2ª Parte: Min. {inicio} - Min. {fin}")
        else:
            st.info(f"📝 Periodo {periodo_seleccionado}: Min. {inicio} - Min. {fin}")
    else:
        if periodo_seleccionado == "2ª Parte":
            st.info(f"📝 2ª Parte")
        else:
            st.info(f"📝 Periodo {periodo_seleccionado}")

    # Crear columnas de coordenadas convertidas usando la función local
    df_periodo["startX_conv"], df_periodo["startY_conv"] = zip(*df_periodo.apply(
        lambda row: convertir_coordenadas_local(row["startX"], row["startY"]), axis=1
    ))
    df_periodo["endX_conv"], df_periodo["endY_conv"] = zip(*df_periodo.apply(
        lambda row: convertir_coordenadas_local(row["endX"], row["endY"]), axis=1
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

    fig.set_facecolor("white")  # Cambiado a blanco para mejor visibilidad

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
        if row["es_sustituto"] and periodo_seleccionado == "2ª Parte":
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
        indicador = " (S)" if es_sustituto and periodo_seleccionado == "2ª Parte" else ""
        ax.text(125, 70 - (idx * 4), f"{jugador}{indicador}", color="black", fontsize=12, va="center")

    # Agregar leyenda solo para la 2ª Parte si hay sustitutos
    if mostrar_leyenda:
        from matplotlib.lines import Line2D
        leyenda_elementos = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='black', markersize=10, label='Titulares'),
            Line2D([0], [0], marker='s', color='w', markerfacecolor='black', markersize=10, label='Sustitutos')
        ]
        ax.legend(handles=leyenda_elementos, loc='upper right', fontsize=10)

    # Usar el rango de tiempo calculado para el título
    if periodo_seleccionado in rangos_tiempo:
        inicio = rangos_tiempo[periodo_seleccionado]["inicio"]
        fin = rangos_tiempo[periodo_seleccionado]["fin"]
        rango_minutos = f" (Min. {inicio}-{fin})"
    else:
        rango_minutos = ""
    
    # Establecer el título según la selección
    if periodo_seleccionado == "2ª Parte":
        plt.suptitle(f"Red de Pases - 2ª Parte{rango_minutos}", color="black", fontsize=20)
    else:
        plt.suptitle(f"Red de Pases - Período {periodo_seleccionado}{rango_minutos}", color="black", fontsize=20)
    
    # Estadísticas adicionales
    st.pyplot(fig)
    
    # Mostrar estadísticas de pases
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Top Conexiones")
        top_pases = pases_entre_jugadores.sort_values("count", ascending=False).head(10)
        for _, row in top_pases.iterrows():
            st.write(f"**{row['Player']} → {row['Secundary']}**: {row['count']} pases")
    
    with col2:
        st.subheader("👟 Participación")
        participacion = intervenciones.sort_values("count", ascending=False).head(10)
        for _, row in participacion.iterrows():
            jugador = row['Player']
            # Añadir indicador de sustituto solo en la segunda parte
            es_sustituto = jugador in sustitutos
            indicador = " (Sustituto)" if es_sustituto and periodo_seleccionado == "2ª Parte" else ""
            st.write(f"**{jugador}{indicador}**: {row['count']} acciones")

# =========================
# 2) Matriz de Pases
# =========================

def matriz_de_pases(df):
    st.subheader("📊 Matriz de Pases del Valencia")

    if df is None or df.empty:
        st.warning("⚠️ No hay datos disponibles para generar la Matriz de Pases.")
        return

    cols_req = ["Player", "Secundary", "Periodo"]
    if not all(col in df.columns for col in cols_req):
        st.error(f"❌ Faltan columnas. Necesario: {cols_req}")
        return
    
    # Filtrar pases primero (ajustando para el código "Pases")
    df_pases = df[(df['Team'] == 'Valencia') & (df['code'] == 'Pases') & 
                 df['Player'].notna() & df['Secundary'].notna()]
    
    if df_pases.empty:
        st.warning("⚠️ No hay datos de pases válidos para analizar.")
        return

    # Opciones: periodos individuales o matrices combinadas
    opciones = ["Primera Parte (Periodo 1)", "Segunda Parte (Periodos >1)", "Matriz Total"]
    opcion_seleccionada = st.selectbox("📊 Selecciona los periodos:", opciones, key="periodo_matriz")

    if opcion_seleccionada == "Primera Parte (Periodo 1)":
        df_periodo = df_pases[df_pases["Periodo"] == 1].copy()
        titulo = "Matriz de Pases - Primera Parte (Periodo 1)"
    elif opcion_seleccionada == "Segunda Parte (Periodos >1)":
        df_periodo = df_pases[df_pases["Periodo"] > 1].copy()
        titulo = "Matriz de Pases - Segunda Parte (Periodos >1)"
    else:  # Matriz Total
        df_periodo = df_pases.copy()
        titulo = "Matriz de Pases - Todos los Períodos"

    if df_periodo.empty:
        st.warning(f"⚠️ No hay datos para {opcion_seleccionada}.")
        return

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
    st.pyplot(fig)
    
    # Estadísticas adicionales
    col1, col2 = st.columns(2)
    
    with col1:
        # Pases por jugador
        pases_por_jugador = matriz_pases.sum(axis=1).sort_values(ascending=False)
        st.subheader("🥇 Jugadores con más pases")
        for jugador, pases in pases_por_jugador.head(5).items():
            nombre = jugador.split(". ")[1] if ". " in jugador else jugador
            st.write(f"**{nombre}**: {pases} pases")
    
    with col2:
        # Receptores de pases
        receptores = matriz_pases.sum(axis=0).sort_values(ascending=False)
        st.subheader("🎯 Principales receptores")
        for jugador, pases in receptores.head(5).items():
            nombre = jugador.split(". ")[1] if ". " in jugador else jugador
            st.write(f"**{nombre}**: {pases} pases recibidos")

# =========================
# 3) Faltas
# =========================

def faltas_valencia(df):
    st.subheader("🟥 Faltas Cometidas")

    if df is None or df.empty:
        st.warning("⚠️ No hay datos de faltas.")
        return

    columnas_necesarias = ["Team", "code", "startX", "startY", "Periodo", "Player"]
    if not all(col in df.columns for col in columnas_necesarias):
        st.error(f"❌ Faltan columnas: {columnas_necesarias}")
        return

    # Filtrar faltas
    faltas = df[
        df["Team"].str.contains("Valencia", case=False, na=False) &
        df["code"].str.contains("Faltas", case=False, na=False)
    ].copy()

    if faltas.empty:
        st.warning("⚠️ No hay faltas registradas para Valencia en este partido.")
        return

    # Convertir coordenadas
    faltas["startX_conv"], faltas["startY_conv"] = zip(*faltas.apply(
        lambda row: convertir_coordenadas_reflejado(row["startX"], row["startY"]), axis=1
    ))

    # Opción para filtrar por parte
    opciones = ["Todas las faltas", "Primera Parte (Periodo 1)", "Segunda Parte (Periodos >1)"]
    opcion_seleccionada = st.selectbox("🔍 Filtrar faltas:", opciones, key="filtro_faltas")
    
    if opcion_seleccionada == "Primera Parte (Periodo 1)":
        faltas_filtradas = faltas[faltas["Periodo"] == 1]
        titulo = "Faltas cometidas por Valencia - Primera Parte"
    elif opcion_seleccionada == "Segunda Parte (Periodos >1)":
        faltas_filtradas = faltas[faltas["Periodo"] > 1]
        titulo = "Faltas cometidas por Valencia - Segunda Parte"
    else:
        faltas_filtradas = faltas
        titulo = "Faltas cometidas por Valencia - Todo el partido"
    
    if faltas_filtradas.empty:
        st.warning(f"⚠️ No hay faltas para {opcion_seleccionada}.")
        return

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
    st.pyplot(fig)
    
    # Estadísticas de faltas
    st.subheader("📊 Estadísticas de faltas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Faltas por jugador
        faltas_por_jugador = faltas_filtradas["Player"].value_counts()
        st.write("**Faltas por jugador:**")
        for jugador, num_faltas in faltas_por_jugador.items():
            nombre = jugador.split(". ")[1] if ". " in jugador else jugador
            st.write(f"- {nombre}: {num_faltas} faltas")
    
    with col2:
        # Faltas por periodo
        faltas_por_periodo = faltas_filtradas["Periodo"].value_counts().sort_index()
        st.write("**Faltas por periodo:**")
        for periodo, num_faltas in faltas_por_periodo.items():
            st.write(f"- Periodo {periodo}: {num_faltas} faltas")

# =========================
# 4) Tiros
# =========================

def tiros_valencia(df):
    st.subheader("🎯 Tiros del Valencia CF")

    if df is None or df.empty:
        st.warning("⚠️ No hay datos de tiros.")
        return

    columnas_necesarias = ["Team", "code", "Mins", "startX", "startY", "group", "Player", "text"]
    if not all(col in df.columns for col in columnas_necesarias):
        st.error(f"❌ Faltan columnas: {columnas_necesarias}")
        return

    # Filtrar Tiros (ajustado para incluir "Finalizaciones")
    tiros = df[
        df["Team"].str.contains("Valencia", case=False, na=False) &
        (df["code"].str.contains("Tiros", case=False, na=False) | 
         df["code"].str.contains("Finalizaciones", case=False, na=False))
    ].copy()

    if tiros.empty:
        st.warning("⚠️ No hay tiros registrados.")
        return

    # Convertir coords
    tiros["startX_conv"], tiros["startY_conv"] = zip(*tiros.apply(
        lambda row: convertir_coordenadas_reflejado(row["startX"], row["startY"]), axis=1
    ))

    # Determinar parte basado en el periodo en lugar de minutos
    tiros["Parte"] = np.where(tiros["Periodo"] == 1, 1, 2)

    opciones_parte = [1, 2, "Tiros Totales"]
    parte_seleccionada = st.selectbox("📊 Selecciona la parte:", opciones_parte)

    if parte_seleccionada == "Tiros Totales":
        tiros_filtrados = tiros
        titulo = "Tiros Totales del Valencia CF"
    else:
        tiros_filtrados = tiros[tiros["Parte"] == parte_seleccionada]
        titulo = f"Tiros del Valencia CF - Parte {parte_seleccionada}"

    if tiros_filtrados.empty:
        st.warning(f"⚠️ No hay datos de tiros para la parte {parte_seleccionada}.")
        return

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

    st.pyplot(fig)
    
    # Mostrar estadísticas adicionales
    st.subheader("📊 Estadísticas de tiros")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Tiros por jugador
        tiros_por_jugador = tiros_filtrados["Player"].value_counts()
        st.write("**Tiros por jugador:**")
        for jugador, num_tiros in tiros_por_jugador.items():
            nombre = jugador.split(". ")[1] if ". " in jugador else jugador
            st.write(f"- {nombre}: {num_tiros} tiros")
    
    with col2:
        # Eficacia
        st.write("**Eficacia:**")
        if total_tiros > 0:
            st.write(f"- Precisión: {round((conteo_tiros['gol'] + conteo_tiros['a_puerta'])/total_tiros*100, 1)}%")
            st.write(f"- Conversión: {round(conteo_tiros['gol']/total_tiros*100, 1)}% de los tiros son gol")
        else:
            st.write("No hay suficientes datos para calcular la eficacia.")

# =========================
# 5) Recuperaciones
# =========================

def recuperaciones_valencia(df):
    st.subheader("🟢 Recuperaciones del Valencia CF")

    if df is None or df.empty:
        st.warning("⚠️ No hay datos de recuperaciones.")
        return

    columnas_necesarias = ["Team", "code", "startX", "startY", "Periodo", "Player"]
    if not all(col in df.columns for col in columnas_necesarias):
        st.error(f"❌ Faltan columnas: {columnas_necesarias}")
        return

    # Filtrar recuperaciones
    recuperaciones = df[
        df["Team"].str.contains("Valencia", case=False, na=False) &
        df["code"].str.contains("Recuperaciones", case=False, na=False)
    ].copy()

    if recuperaciones.empty:
        st.warning("⚠️ No hay recuperaciones registradas para Valencia en este partido.")
        return

    # Convertir coordenadas
    recuperaciones["startX_conv"], recuperaciones["startY_conv"] = zip(*recuperaciones.apply(
        lambda row: convertir_coordenadas_reflejado(row["startX"], row["startY"]), axis=1
    ))

    # Opción para filtrar por parte
    opciones = ["Todas las recuperaciones", "Primera Parte (Periodo 1)", "Segunda Parte (Periodos >1)"]
    opcion_seleccionada = st.selectbox("🔍 Filtrar recuperaciones:", opciones, key="filtro_recuperaciones")
    
    if opcion_seleccionada == "Primera Parte (Periodo 1)":
        recuperaciones_filtradas = recuperaciones[recuperaciones["Periodo"] == 1]
        titulo = "Recuperaciones del Valencia - Primera Parte"
    elif opcion_seleccionada == "Segunda Parte (Periodos >1)":
        recuperaciones_filtradas = recuperaciones[recuperaciones["Periodo"] > 1]
        titulo = "Recuperaciones del Valencia - Segunda Parte"
    else:
        recuperaciones_filtradas = recuperaciones
        titulo = "Recuperaciones del Valencia - Todo el partido"
    
    if recuperaciones_filtradas.empty:
        st.warning(f"⚠️ No hay recuperaciones para {opcion_seleccionada}.")
        return

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
    st.pyplot(fig)
    
    # Estadísticas de recuperaciones
    st.subheader("📊 Estadísticas de recuperaciones")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Recuperaciones por jugador
        recuperaciones_por_jugador = recuperaciones_filtradas["Player"].value_counts()
        st.write("**Recuperaciones por jugador:**")
        for jugador, num_recuperaciones in recuperaciones_por_jugador.items():
            nombre = jugador.split(". ")[1] if ". " in jugador else jugador
            st.write(f"- {nombre}: {num_recuperaciones} recuperaciones")
    
    with col2:
        # Recuperaciones por zona
        recuperaciones_por_zona = recuperaciones_filtradas["Zona"].value_counts()
        st.write("**Recuperaciones por zona:**")
        for zona, num_recuperaciones in recuperaciones_por_zona.items():
            st.write(f"- {zona}: {num_recuperaciones} recuperaciones")
    
# =========================
# 6) Pases Específicos
# =========================
def pases_especificos(df):
    st.subheader("🔄 Visualización de Pases Específicos")

    if df is None or df.empty:
        st.warning("⚠️ No hay datos disponibles para visualizar pases específicos.")
        return

    # Comprobar columnas necesarias
    cols_req = ["Team", "code", "group", "Periodo", "Mins", "startX", "startY", "endX", "endY", "Player", "Secundary"]
    if not all(col in df.columns for col in cols_req):
        st.error(f"❌ Faltan columnas. Necesario: {cols_req}")
        return
        
    # Determinar parte basado en el periodo (similar a tiros_valencia)
    df["Parte"] = np.where(df["Periodo"] == 1, 1, 2)
    
    # Opción para filtrar por parte (como estaba en el código original)
    opciones_parte = [1, 2, "Pases Totales"]
    parte_seleccionada = st.selectbox("📊 Selecciona la parte:", opciones_parte, key="filtro_pases_parte")
    
    # Filtrar pases específicos para el Valencia
    if parte_seleccionada == "Pases Totales":
        filtro_parte = df.copy()
        titulo_parte = "Pases Totales"
    else:
        filtro_parte = df[df["Parte"] == parte_seleccionada]
        titulo_parte = f"Parte {parte_seleccionada}"
    
    # Identificar jugadores suplentes basados en su primera aparición
    primera_aparicion = df[df['Player'].notna()].groupby('Player')['Mins'].min().reset_index()
    suplentes = primera_aparicion[primera_aparicion['Mins'] > 1]['Player'].tolist()
    
    # Filtrar los diferentes tipos de pases
    acciones_cara = filtro_parte[
        (filtro_parte['Team'] == 'Valencia') &
        (filtro_parte['code'] == 'Encontrar Futbolista de cara')
    ].copy()
    
    acciones_profundidad = filtro_parte[
        (filtro_parte['Team'] == 'Valencia') &
        (filtro_parte['code'] == 'Encontrar Futbolista en profundidad')
    ].copy()
    
    # Corregido para "Atacar el área" en 'code'
    acciones_area = filtro_parte[
        (filtro_parte['Team'] == 'Valencia') &
        (filtro_parte['code'] == 'Atacar el área')
    ].copy()
    
    # Corrección para "Atacar el área" en 'code' y "Atacar el área con +3" en 'group'
    acciones_area_plus = filtro_parte[
        (filtro_parte['Team'] == 'Valencia') &
        (filtro_parte['code'] == 'Atacar el área') &
        (filtro_parte['group'] == 'Atacar el área con +3')
    ].copy()
    
    # Verificar si hay datos para mostrar
    if acciones_cara.empty and acciones_profundidad.empty and acciones_area.empty and acciones_area_plus.empty:
        st.warning(f"⚠️ No hay datos de pases específicos para {titulo_parte}.")
        return
        
    # Aplicar la conversión de coordenadas a todos los conjuntos de datos
    for acciones in [acciones_cara, acciones_profundidad, acciones_area, acciones_area_plus]:
        if not acciones.empty:
            acciones[['startX_conv', 'startY_conv']] = acciones.apply(
                lambda row: pd.Series(convertir_coordenadas_reflejado(row['startX'], row['startY'])), 
                axis=1
            )
            acciones[['endX_conv', 'endY_conv']] = acciones.apply(
                lambda row: pd.Series(convertir_coordenadas_reflejado(row['endX'], row['endY'])), 
                axis=1
            )
    
    # Función para graficar pases (similar al estilo de tiros_valencia)
    def graficar_pases(df_pases, color, titulo):
        fig, ax = plt.subplots(figsize=(16, 11))
        # Configurar campo similar a tiros_valencia
        pitch = Pitch(
            pitch_type='custom', 
            pitch_length=120, 
            pitch_width=80, 
            line_color='black', 
            pitch_color='#d0f0c0', 
            linewidth=2
        )
        pitch.draw(ax=ax)
        
        # Añadir franjas horizontales como en tiros_valencia
        franja_altura = 80 / 5
        for i in range(5):
            if i % 2 == 0:
                ax.fill_between([0, 120], i * franja_altura, (i + 1) * franja_altura, color="#a0c080", alpha=0.7)
        
        fig.set_facecolor("white")
        
        # Dibujar las acciones con líneas y puntos
        for _, row in df_pases.iterrows():
            start_x, start_y = row['startX_conv'], row['startY_conv']
            end_x, end_y = row['endX_conv'], row['endY_conv']
            receptor = row['Secundary']
            pasador = row['Player']
            
            # Dibujar la línea de pase
            ax.plot([start_x, end_x], [start_y, end_y], color=color, lw=2, alpha=0.7, zorder=2)
            
            # Determinar si el jugador que pasa es suplente
            es_suplente_pasador = pasador in suplentes
            marker_pasador = 's' if es_suplente_pasador else 'o'  # cuadrado para suplentes, círculo para titulares
            
            # Dibujar el marcador del jugador que da el pase
            ax.scatter(start_x, start_y, c='black', s=100, edgecolors=color, marker=marker_pasador, zorder=3)
            
            # Extraer nombre sin número (similar a otras funciones)
            nombre_jugador = pasador.split(". ")[1] if ". " in pasador else pasador
            ax.text(start_x, start_y+1.5, nombre_jugador, fontsize=12, color='black', ha='center', va='center',
                   bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
            
            # Si hay receptor, dibujar su círculo y su nombre
            if pd.notna(receptor):
                # Determinar si el receptor es suplente
                es_suplente_receptor = receptor in suplentes
                marker_receptor = 's' if es_suplente_receptor else 'o'  # cuadrado para suplentes, círculo para titulares
                
                ax.scatter(end_x, end_y, c='black', s=100, edgecolors=color, marker=marker_receptor, zorder=3)
                # Extraer nombre del receptor
                nombre_receptor = receptor.split(". ")[1] if ". " in receptor else receptor
                ax.text(end_x, end_y+1.5, nombre_receptor, fontsize=12, color='black', ha='center', va='center',
                       bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
            else:
                ax.scatter(end_x, end_y, c='black', s=100, edgecolors=color, marker='x', zorder=3)
        
        # Añadir leyenda para titulares y suplentes
        from matplotlib.lines import Line2D
        custom_legend = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='black', 
                markeredgecolor=color, markersize=10, label='Titular'),
            Line2D([0], [0], marker='s', color='w', markerfacecolor='black', 
                markeredgecolor=color, markersize=10, label='Suplente'),
            mpatches.Patch(color=color, label=titulo)
        ]
        ax.legend(handles=custom_legend, loc='upper right', fontsize=10)
        
        # Añadir título
        plt.suptitle(f"{titulo} - {titulo_parte}", color='black', fontsize=20)
        
        # Añadir estadísticas como texto en la parte inferior
        total_pases = len(df_pases)
        stats_text = f"Total: {total_pases} pases de este tipo"
        plt.figtext(0.5, 0.01, stats_text, ha="center", fontsize=14, 
                   bbox=dict(facecolor='white', alpha=0.8, edgecolor='black'))
        
        return fig
    
    # Crear pestañas para cada tipo de pase
    tab1, tab2, tab3, tab4 = st.tabs(["Futbolista de Cara", "Futbolista en Profundidad", "Atacar el Área", "Atacar el Área con +3"])
    
    with tab1:
        if not acciones_cara.empty:
            fig_cara = graficar_pases(acciones_cara, 'pink', "Encontrar Futbolista de Cara")
            st.pyplot(fig_cara)
            
            # Añadir estadísticas por jugador
            st.subheader("📊 Estadísticas por jugador")
            col1, col2 = st.columns(2)
            
            with col1:
                # Pases por jugador
                pases_por_jugador = acciones_cara["Player"].value_counts()
                st.write("**Pases por jugador:**")
                for jugador, num_pases in pases_por_jugador.items():
                    nombre = jugador.split(". ")[1] if ". " in jugador else jugador
                    es_suplente = jugador in suplentes
                    st.write(f"- {nombre} {'(SUP)' if es_suplente else ''}: {num_pases} pases")
            
            with col2:
                # Receptores principales
                receptores = acciones_cara["Secundary"].value_counts()
                st.write("**Principales receptores:**")
                for jugador, num_pases in receptores.items():
                    nombre = jugador.split(". ")[1] if ". " in jugador else jugador
                    es_suplente = jugador in suplentes
                    st.write(f"- {nombre} {'(SUP)' if es_suplente else ''}: {num_pases} pases recibidos")
        else:
            st.warning(f"No hay datos de pases 'Encontrar Futbolista de cara' para {titulo_parte}.")
    
    with tab2:
        if not acciones_profundidad.empty:
            fig_profundidad = graficar_pases(acciones_profundidad, 'green', "Encontrar Futbolista en Profundidad")
            st.pyplot(fig_profundidad)
            
            # Añadir estadísticas por jugador
            st.subheader("📊 Estadísticas por jugador")
            col1, col2 = st.columns(2)
            
            with col1:
                # Pases por jugador
                pases_por_jugador = acciones_profundidad["Player"].value_counts()
                st.write("**Pases por jugador:**")
                for jugador, num_pases in pases_por_jugador.items():
                    nombre = jugador.split(". ")[1] if ". " in jugador else jugador
                    es_suplente = jugador in suplentes
                    st.write(f"- {nombre} {'(SUP)' if es_suplente else ''}: {num_pases} pases")
            
            with col2:
                # Receptores principales
                receptores = acciones_profundidad["Secundary"].value_counts()
                st.write("**Principales receptores:**")
                for jugador, num_pases in receptores.items():
                    nombre = jugador.split(". ")[1] if ". " in jugador else jugador
                    es_suplente = jugador in suplentes
                    st.write(f"- {nombre} {'(SUP)' if es_suplente else ''}: {num_pases} pases recibidos")
        else:
            st.warning(f"No hay datos de pases 'Encontrar Futbolista en profundidad' para {titulo_parte}.")
    
    with tab3:
        if not acciones_area.empty:
            fig_area = graficar_pases(acciones_area, 'purple', "Atacar el Área")
            st.pyplot(fig_area)
            
            # Añadir estadísticas por jugador
            st.subheader("📊 Estadísticas por jugador")
            col1, col2 = st.columns(2)
            
            with col1:
                # Pases por jugador
                pases_por_jugador = acciones_area["Player"].value_counts()
                st.write("**Pases por jugador:**")
                for jugador, num_pases in pases_por_jugador.items():
                    nombre = jugador.split(". ")[1] if ". " in jugador else jugador
                    es_suplente = jugador in suplentes
                    st.write(f"- {nombre} {'(SUP)' if es_suplente else ''}: {num_pases} pases")
            
            with col2:
                # Receptores principales
                receptores = acciones_area["Secundary"].value_counts()
                st.write("**Principales receptores:**")
                for jugador, num_pases in receptores.items():
                    nombre = jugador.split(". ")[1] if ". " in jugador else jugador
                    es_suplente = jugador in suplentes
                    st.write(f"- {nombre} {'(SUP)' if es_suplente else ''}: {num_pases} pases recibidos")
        else:
            st.warning(f"No hay datos de pases 'Atacar el Área' para {titulo_parte}.")
    
    with tab4:
        if not acciones_area_plus.empty:
            fig_area_plus = graficar_pases(acciones_area_plus, 'blue', "Atacar el Área con +3")
            st.pyplot(fig_area_plus)
            
            # Añadir estadísticas por jugador
            st.subheader("📊 Estadísticas por jugador")
            col1, col2 = st.columns(2)
            
            with col1:
                # Pases por jugador
                pases_por_jugador = acciones_area_plus["Player"].value_counts()
                st.write("**Pases por jugador:**")
                for jugador, num_pases in pases_por_jugador.items():
                    nombre = jugador.split(". ")[1] if ". " in jugador else jugador
                    es_suplente = jugador in suplentes
                    st.write(f"- {nombre} {'(SUP)' if es_suplente else ''}: {num_pases} pases")
            
            with col2:
                # Receptores principales
                receptores = acciones_area_plus["Secundary"].value_counts()
                st.write("**Principales receptores:**")
                for jugador, num_pases in receptores.items():
                    nombre = jugador.split(". ")[1] if ". " in jugador else jugador
                    es_suplente = jugador in suplentes
                    st.write(f"- {nombre} {'(SUP)' if es_suplente else ''}: {num_pases} pases recibidos")
        else:
            st.warning(f"No hay datos de pases 'Atacar el Área con +3' para {titulo_parte}.")