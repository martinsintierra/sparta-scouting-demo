import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from google.cloud import bigquery
from google.oauth2 import service_account
import unicodedata
from thefuzz import process, fuzz
import os
from pathlib import Path
import plotly.express as px
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler



# ============================================================
# 1. CONFIGURACIÓN VISUAL
# ============================================================
st.set_page_config(
    page_title="Scouting Pro AI", 
    layout="wide", 
    page_icon="⚽",
    initial_sidebar_state="expanded"
)

# Estilos CSS mejorados
st.markdown("""
<style>
    .metric-card { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px; 
        border-radius: 10px; 
        border: 2px solid #444;
        color: white;
    }
    .big-font { 
        font-size: 20px !important; 
        font-weight: bold; 
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    .similarity-badge {
        display: inline-block;
        background: #10b981;
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# CONFIGURACIÓN DEL PROYECTO
PROJECT_ID = "proyecto-scouting-futbol"
DATASET = "dm_scouting"
client = client = get_bigquery_client()

# ============================================================
# 2. FUNCIONES AUXILIARES
# ============================================================

# Configuración de caché persistente
CACHE_DIR = Path(".streamlit_cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_FILE = CACHE_DIR / "players_index.parquet"
CACHE_EXPIRY_HOURS = 24

def get_bigquery_client():
    """Obtiene cliente de BigQuery desde secrets de Streamlit"""
    try:
        # En Streamlit Cloud
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        return bigquery.Client(credentials=credentials, project=PROJECT_ID)
    except:
        # Localmente (fallback)
        return bigquery.Client(project=PROJECT_ID)

def normalizar_texto(texto):
    """Elimina tildes y caracteres especiales para búsqueda"""
    if not texto:
        return ""
    # NFD descompone caracteres acentuados (á -> a + ́)
    nfkd = unicodedata.normalize('NFD', texto)
    # Filtra solo caracteres ASCII (elimina acentos)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)])

def cache_is_valid():
    """Verifica si el caché en disco es válido (menos de 24 horas)"""
    if not CACHE_FILE.exists():
        return False
    
    import time
    file_age_hours = (time.time() - os.path.getmtime(CACHE_FILE)) / 3600
    return file_age_hours < CACHE_EXPIRY_HOURS

@st.cache_data(ttl=86400)  # 24 horas - se refresca 1 vez al día
def get_all_players_index(_client):
    """Descarga índice completo de jugadores con caché en disco"""
    
    # Intentar cargar desde disco primero
    if cache_is_valid():
        try:
            df = pd.read_parquet(CACHE_FILE)
            st.sidebar.info("📂 Datos cargados desde caché local")
            return df
        except Exception as e:
            st.sidebar.warning(f"⚠️ Error leyendo caché: {e}")
    
    # Si no hay caché válido, consultar BigQuery
    st.sidebar.info("☁️ Descargando datos desde BigQuery...")
    
    # --- CORRECCION SQL 1: Apuntar a la VISTA NUEVA y mapear nombres ---
    sql_index = f"""
        SELECT 
            player_id,
            nombre_jugador as player,   -- Alias para que tu código no se rompa
            equipo_principal, 
            temporada_anio,
            posicion,
            rating_promedio, 
            goals_p90,
            xG_p90,
            partidos_jugados,
            total_minutos
        FROM `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo`
        WHERE total_minutos >= 300
        ORDER BY temporada_anio DESC, rating_promedio DESC
    """
    df = _client.query(sql_index).to_dataframe()
    
    # Pre-procesar columna normalizada una sola vez
    df['player_normalizado'] = df['player'].apply(normalizar_texto)
    
    # Guardar en disco para próximas sesiones
    try:
        df.to_parquet(CACHE_FILE)
        st.sidebar.success("💾 Caché guardado en disco")
    except Exception as e:
        st.sidebar.warning(f"⚠️ No se pudo guardar caché: {e}")
    
    return df

@st.cache_data(ttl=3600)
def get_players_by_season(temporada, _df_index):
    """Caché selectivo por temporada para búsquedas más rápidas"""
    return _df_index[_df_index['temporada_anio'] == temporada].copy()

def buscar_jugadores_fuzzy(nombre, temporada, df_index, umbral_fuzzy=70):
    """
    Búsqueda LOCAL ultra-rápida con tolerancia a errores (fuzzy matching)
    """
    if df_index.empty or not nombre:
        return pd.DataFrame()
    
    # Filtrar por temporada primero (reduce espacio de búsqueda)
    df_temp = get_players_by_season(temporada, df_index)
    
    if df_temp.empty:
        return pd.DataFrame()
    
    # Normalizar término de búsqueda
    nombre_normalizado = normalizar_texto(nombre).upper()
    
    # PASO 1: Búsqueda exacta (substring)
    df_exacto = df_temp[
        df_temp['player_normalizado'].str.upper().str.contains(nombre_normalizado, na=False) |
        df_temp['player'].str.upper().str.contains(nombre.upper(), na=False)
    ].copy()
    
    if not df_exacto.empty:
        df_exacto['relevancia'] = 100  # Máxima relevancia para matches exactos
        return df_exacto.sort_values('rating_promedio', ascending=False).head(20)
    
    # PASO 2: Búsqueda fuzzy (tolerante a errores)
    st.sidebar.info("🔍 Aplicando búsqueda inteligente...")
    
    # Crear lista de nombres normalizados
    nombres_normalizados = df_temp['player_normalizado'].tolist()
    
    # Usar thefuzz para encontrar matches similares
    matches = process.extract(
        nombre_normalizado, 
        nombres_normalizados,
        scorer=fuzz.partial_ratio,  # Permite matches parciales
        limit=20
    )
    
    # Filtrar por umbral de similitud
    matches_validos = [(match, score, idx) for match, score, idx in matches if score >= umbral_fuzzy]
    
    if not matches_validos:
        return pd.DataFrame()
    
    # Obtener índices de los matches
    indices = [idx for _, _, idx in matches_validos]
    scores = [score for _, score, _ in matches_validos]
    
    # Crear DataFrame con resultados
    df_resultado = df_temp.iloc[indices].copy()
    df_resultado['relevancia'] = scores
    
    # Ordenar por relevancia y rating
    df_resultado = df_resultado.sort_values(
        ['relevancia', 'rating_promedio'], 
        ascending=[False, False]
    )
    
    return df_resultado.head(20)

@st.cache_data(ttl=3600)
def obtener_similares(id_origen, temp_origen, temp_destino, min_score, _client):
    """Obtiene jugadores similares para una temporada específica"""
    # Filtro dinámico de temporada (s = tabla similitud)
    condicion_temp = f"AND s.temporada_similar = {temp_destino}" if temp_destino else ""
    
    # --- CORRECCION SQL 2: JOIN entre tabla ML y VISTA MASTER ---
    # Aquí es donde arreglamos el problema de tipos INT64 vs STRING y mapeamos los nombres
    sql_similitud = f"""
        SELECT 
            s.jugador_similar_id,
            v.nombre_jugador as destino_nombre, 
            v.equipo_principal as destino_equipo, 
            v.posicion,
            s.temporada_similar,
            s.score_similitud,
            s.rank_similitud,
            v.edad_promedio as destino_edad, 
            v.valor_mercado as destino_valor,
            v.rating_promedio as destino_rating,
            v.goals_p90 as destino_goles,
            v.assists_p90 as destino_asistencias,
            v.xG_p90 as destino_xg,
            v.xA_p90 as destino_xa,
            v.prog_passes_p90 as destino_prog_passes,
            v.dribbles_p90 as destino_dribbles,
            v.recoveries_p90 as destino_recoveries,
            v.aerial_won_p90 as destino_aereos,
            v.partidos_jugados as destino_partidos,
            v.total_minutos as destino_minutos,
            v.nacionalidad as destino_nacionalidad,
            v.altura as destino_altura,
            v.pie as destino_pie,
            v.contrato_vence as destino_contrato,
            -- Percentiles para el radar (vienen de la vista)
            v.pct_xG as destino_pct_xg,
            v.pct_xA as destino_pct_xa,
            v.pct_prog_passes as destino_pct_prog,
            v.pct_dribbles as destino_pct_dribbles,
            v.pct_recoveries as destino_pct_recov

        FROM `{PROJECT_ID}.{DATASET}.scouting_similitud_pro_v2` s
        JOIN `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo` v
          -- CAST FUNDAMENTAL: v.player_id es INT, s.jugador_similar_id es STRING
          ON CAST(v.player_id AS STRING) = s.jugador_similar_id
          AND v.temporada_anio = s.temporada_similar
        
        WHERE s.jugador_origen_id = '{id_origen}'  -- Aquí sí van comillas (tabla ML usa string)
          AND s.temporada_origen = {temp_origen}
          {condicion_temp}
          AND s.score_similitud >= {min_score}
        ORDER BY s.score_similitud DESC 
        LIMIT 50
    """
    return _client.query(sql_similitud).to_dataframe()

def mostrar_tarjeta_jugador(jugador_detalle, unique_key):
    """Renderiza la tarjeta de detalle de un jugador"""
    with st.container():
        st.markdown("---")
        
        # Header de la tarjeta
        col_header1, col_header2, col_header3 = st.columns([3, 1, 1])
        with col_header1:
            st.markdown(f"### {jugador_detalle['destino_nombre']}")
            st.caption(f"{jugador_detalle['destino_equipo']} | {jugador_detalle['posicion']}")
        with col_header2:
            st.markdown(f"""
            <div class="similarity-badge">
                {jugador_detalle['score_similitud']:.1f}% Match
            </div>
            """, unsafe_allow_html=True)
        with col_header3:
            st.caption(f"📅 Temp. {int(jugador_detalle['temporada_similar'])}")
        
        # Métricas principales
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric("🎂 Edad", f"{int(jugador_detalle['destino_edad'])}")
        with col2:
            altura = jugador_detalle['destino_altura']
            st.metric("📏 Altura", f"{altura:.0f} cm" if pd.notnull(altura) else "N/A")
        with col3:
            pie = jugador_detalle['destino_pie']
            st.metric("🦶 Pie", pie if pd.notnull(pie) else "N/A")
        with col4:
            st.metric("🌍 País", jugador_detalle['destino_nacionalidad'])
        with col5:
            valor = jugador_detalle['destino_valor']
            if pd.notnull(valor) and valor > 0:
                st.metric("💰 Valor", f"€{valor/1000:.0f}K")
            else:
                st.metric("💰 Valor", "N/A")
        with col6:
            contrato = jugador_detalle['destino_contrato']
            st.metric("📄 Contrato", str(contrato)[:4] if pd.notnull(contrato) else "N/A")
        
        # Stats de rendimiento
        st.markdown("#### 📊 Estadísticas por 90 minutos")
        col_stat1, col_stat2, col_stat3, col_stat4, col_stat5, col_stat6 = st.columns(6)
        
        with col_stat1:
            st.metric("⭐ Rating", f"{jugador_detalle['destino_rating']:.2f}")
        with col_stat2:
            st.metric("⚽ Goles", f"{jugador_detalle['destino_goles']:.2f}")
        with col_stat3:
            st.metric("🎯 xG", f"{jugador_detalle['destino_xg']:.2f}")
        with col_stat4:
            st.metric("🅰️ Asist.", f"{jugador_detalle['destino_asistencias']:.2f}")
        with col_stat5:
            st.metric("📤 xA", f"{jugador_detalle['destino_xa']:.2f}")
        with col_stat6:
            st.metric("⬆️ Prog. Pass", f"{jugador_detalle['destino_prog_passes']:.2f}")
        
        # Gráfico de Radar (Percentiles)
        st.markdown("#### 🎯 Perfil Comparativo (Percentiles)")
        
        categories = ['xG', 'xA', 'Pases Prog.', 'Dribbles', 'Recuperaciones']
        
        # Usar .get por seguridad en caso de nulos
        values_jugador = [
            jugador_detalle.get('destino_pct_xg', 0) * 100,
            jugador_detalle.get('destino_pct_xa', 0) * 100,
            jugador_detalle.get('destino_pct_prog', 0) * 100,
            jugador_detalle.get('destino_pct_dribbles', 0) * 100,
            jugador_detalle.get('destino_pct_recov', 0) * 100,
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values_jugador,
            theta=categories,
            fill='toself',
            name=jugador_detalle['destino_nombre'],
            line_color='#667eea'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True, key=f"radar_{unique_key}")
        
        # Contexto adicional
        col_ctx1, col_ctx2 = st.columns(2)
        with col_ctx1:
            st.info(f"📈 Partidos jugados: {int(jugador_detalle['destino_partidos'])}")
        with col_ctx2:
            st.info(f"⏱️ Minutos totales: {int(jugador_detalle['destino_minutos'])}")

def mostrar_tab_temporada(temp_destino, id_origen, temp_origen, min_score, key_suffix):
    """Renderiza una tab con resultados de una temporada específica"""
    df_results = obtener_similares(id_origen, temp_origen, temp_destino, min_score, client)
    
    if not df_results.empty:
        st.success(f"✅ Encontrados {len(df_results)} jugadores similares en {temp_destino if temp_destino else 'todas las temporadas'}")
        
        # Selector para ver detalle
        jugadores_lista = [
            f"{row['destino_nombre']} ({row['destino_equipo']}) - {row['score_similitud']:.1f}% | Temp {int(row['temporada_similar'])}" 
            for _, row in df_results.iterrows()
        ]
        
        jugador_seleccionado = st.selectbox(
            "Ver detalles de:",
            jugadores_lista,
            key=f"select_{key_suffix}"
        )
        
        # Obtener índice del jugador seleccionado
        idx = jugadores_lista.index(jugador_seleccionado)
        jugador_detalle = df_results.iloc[idx]
        
        # Mostrar tarjeta
        mostrar_tarjeta_jugador(jugador_detalle, f"{key_suffix}_{idx}")
        
        # Tabla resumen (opcional, colapsable)
        with st.expander("📋 Ver tabla completa de resultados"):
            df_display = df_results[[
                'destino_nombre', 'destino_equipo', 'posicion', 
                'temporada_similar', 'score_similitud', 'destino_edad',
                'destino_rating', 'destino_xg', 'destino_xa', 
                'destino_partidos', 'destino_minutos'
            ]].copy()
            
            df_display.columns = [
                'Jugador', 'Equipo', 'Pos', 'Temp', 'Match%', 'Edad',
                'Rating', 'xG/90', 'xA/90', 'PJ', 'Minutos'
            ]
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )
    else:
        st.warning(f"⚠️ No se encontraron jugadores similares con score >= {min_score}%")
        st.markdown("""
        **Sugerencias:**
        - Reduce el porcentaje mínimo de similitud
        - Prueba con otra temporada
        - Verifica que existan datos para esta posición
        """)

@st.cache_data(ttl=3600)
def obtener_evolucion_jugador(player_id, _client):
    """Obtiene la evolución histórica de un jugador a través de temporadas"""
    sql_evolucion = f"""
        SELECT 
            temporada_anio,
            rating_promedio,
            xG_p90,
            xA_p90,
            goals_p90,
            assists_p90,
            prog_passes_p90,
            partidos_jugados,
            total_minutos
        FROM `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo`
        WHERE player_id = {player_id}
        ORDER BY temporada_anio
    """
    return _client.query(sql_evolucion).to_dataframe()


def mostrar_timeline_evolucion(player_id, nombre_jugador, client):
    """Renderiza timeline de evolución del jugador"""
    df_evo = obtener_evolucion_jugador(player_id, client)
    
    if df_evo.empty or len(df_evo) < 2:
        st.info(f"📊 No hay suficientes datos históricos para {nombre_jugador}")
        return
    
    st.markdown(f"#### 📈 Evolución Histórica: {nombre_jugador}")
    
    # Selector de métricas
    col_select1, col_select2 = st.columns(2)
    with col_select1:
        metrica_principal = st.selectbox(
            "Métrica Principal",
            options=['rating_promedio', 'xG_p90', 'xA_p90', 'goals_p90', 'assists_p90', 'prog_passes_p90'],
            format_func=lambda x: {
                'rating_promedio': '⭐ Rating',
                'xG_p90': '🎯 xG por 90min',
                'xA_p90': '📤 xA por 90min',
                'goals_p90': '⚽ Goles por 90min',
                'assists_p90': '🅰️ Asistencias por 90min',
                'prog_passes_p90': '⬆️ Pases Progresivos por 90min'
            }[x],
            key=f"timeline_main_{player_id}"
        )
    
    with col_select2:
        metrica_secundaria = st.selectbox(
            "Métrica Secundaria (opcional)",
            options=[None, 'rating_promedio', 'xG_p90', 'xA_p90', 'goals_p90', 'assists_p90', 'prog_passes_p90'],
            format_func=lambda x: "Ninguna" if x is None else {
                'rating_promedio': '⭐ Rating',
                'xG_p90': '🎯 xG por 90min',
                'xA_p90': '📤 xA por 90min',
                'goals_p90': '⚽ Goles por 90min',
                'assists_p90': '🅰️ Asistencias por 90min',
                'prog_passes_p90': '⬆️ Pases Progresivos por 90min'
            }[x],
            key=f"timeline_sec_{player_id}"
        )
    
    # Crear figura con eje Y dual si hay métrica secundaria
    fig = go.Figure()
    
    # Línea principal
    fig.add_trace(go.Scatter(
        x=df_evo['temporada_anio'],
        y=df_evo[metrica_principal],
        mode='lines+markers',
        name=metrica_principal.replace('_', ' ').title(),
        line=dict(color='#667eea', width=3),
        marker=dict(size=10),
        hovertemplate='<b>Temp %{x}</b><br>%{y:.2f}<extra></extra>'
    ))
    
    # Línea secundaria (si existe)
    if metrica_secundaria and metrica_secundaria != metrica_principal:
        fig.add_trace(go.Scatter(
            x=df_evo['temporada_anio'],
            y=df_evo[metrica_secundaria],
            mode='lines+markers',
            name=metrica_secundaria.replace('_', ' ').title(),
            line=dict(color='#f59e0b', width=3, dash='dash'),
            marker=dict(size=8),
            yaxis='y2',
            hovertemplate='<b>Temp %{x}</b><br>%{y:.2f}<extra></extra>'
        ))
        
        # Configurar eje Y secundario
        fig.update_layout(
            yaxis2=dict(
                title=metrica_secundaria.replace('_', ' ').title(),
                overlaying='y',
                side='right',
                showgrid=False
            )
        )
    
    fig.update_layout(
        title=f"Evolución de {nombre_jugador} ({df_evo['temporada_anio'].min()}-{df_evo['temporada_anio'].max()})",
        xaxis_title="Temporada",
        yaxis_title=metrica_principal.replace('_', ' ').title(),
        hovermode='x unified',
        height=450,
        showlegend=True,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla resumen
    with st.expander("📋 Ver datos completos"):
        df_display = df_evo.copy()
        df_display.columns = [
            'Temporada', 'Rating', 'xG/90', 'xA/90', 
            'Goles/90', 'Asist/90', 'ProgPass/90', 'PJ', 'Minutos'
        ]
        st.dataframe(df_display, use_container_width=True, hide_index=True)


# ============================================================
# FUNCIÓN 2: MAPA PCA DE DISPERSIÓN POR POSICIÓN
# ============================================================

@st.cache_data(ttl=3600)
def obtener_datos_pca(posicion, temporada, _client):
    """Obtiene datos de percentiles para análisis PCA"""
    sql_pca = f"""
        SELECT 
            player_id,
            nombre_jugador,
            equipo_principal,
            valor_millones,
            rating_promedio,
            pct_xG,
            pct_xA,
            pct_prog_passes,
            pct_dribbles,
            pct_recoveries,
            pct_aerial,
            pct_rating
        FROM `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo`
        WHERE posicion = '{posicion}'
          AND temporada_anio = {temporada}
          AND total_minutos >= 300
          AND pct_xG IS NOT NULL
          AND pct_xA IS NOT NULL
    """
    return _client.query(sql_pca).to_dataframe()


def mostrar_mapa_pca(player_id_seleccionado, posicion, temporada, nombre_jugador, client):
    """Renderiza mapa PCA con el jugador destacado"""
    df_pca = obtener_datos_pca(posicion, temporada, client)
    
    if df_pca.empty or len(df_pca) < 10:
        st.warning(f"⚠️ Insuficientes datos para PCA en {posicion} (temporada {temporada})")
        return
    
    st.markdown(f"#### 🗺️ Mapa de Similitud (PCA): {posicion} - Temp {temporada}")
    st.caption("Reducción dimensional de percentiles estadísticos. Jugadores cercanos tienen perfiles similares.")
    
    # Preparar datos para PCA
    columnas_pca = ['pct_xG', 'pct_xA', 'pct_prog_passes', 'pct_dribbles', 'pct_recoveries', 'pct_aerial', 'pct_rating']
    X = df_pca[columnas_pca].fillna(0).values
    
    # Normalizar y aplicar PCA
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    # Agregar componentes al DataFrame
    df_pca['PC1'] = X_pca[:, 0]
    df_pca['PC2'] = X_pca[:, 1]
    
    # Identificar si el jugador seleccionado está en el dataset
    df_pca['es_seleccionado'] = df_pca['player_id'] == player_id_seleccionado
    df_pca['color'] = df_pca['es_seleccionado'].map({True: 'Jugador Seleccionado', False: 'Otros'})
    df_pca['size'] = df_pca['es_seleccionado'].map({True: 15, False: 8})
    
    # Crear scatter plot
    fig = px.scatter(
        df_pca,
        x='PC1',
        y='PC2',
        color='color',
        size='size',
        hover_name='nombre_jugador',
        hover_data={
            'equipo_principal': True,
            'rating_promedio': ':.2f',
            'valor_millones': ':.1f',
            'PC1': False,
            'PC2': False,
            'color': False,
            'size': False
        },
        color_discrete_map={
            'Jugador Seleccionado': '#ef4444',
            'Otros': '#667eea'
        },
        title=f"Mapa de Perfiles - {posicion} ({len(df_pca)} jugadores)"
    )
    
    # Personalizar diseño
    fig.update_traces(
        marker=dict(
            line=dict(width=1, color='white'),
            opacity=0.7
        )
    )
    
    fig.update_layout(
        height=500,
        xaxis_title=f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% varianza)",
        yaxis_title=f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% varianza)",
        showlegend=True,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar varianza explicada
    col_var1, col_var2, col_var3 = st.columns(3)
    with col_var1:
        st.metric("🎯 Varianza Explicada (PC1+PC2)", 
                  f"{(pca.explained_variance_ratio_[0] + pca.explained_variance_ratio_[1])*100:.1f}%")
    with col_var2:
        st.metric("👥 Jugadores Analizados", len(df_pca))
    with col_var3:
        # Calcular jugadores cercanos (distancia euclidiana < percentil 10)
        if df_pca['es_seleccionado'].any():
            idx_seleccionado = df_pca[df_pca['es_seleccionado']].index[0]
            pc1_sel = df_pca.loc[idx_seleccionado, 'PC1']
            pc2_sel = df_pca.loc[idx_seleccionado, 'PC2']
            
            df_pca['distancia'] = np.sqrt(
                (df_pca['PC1'] - pc1_sel)**2 + (df_pca['PC2'] - pc2_sel)**2
            )
            
            umbral_cercania = df_pca['distancia'].quantile(0.10)
            cercanos = len(df_pca[df_pca['distancia'] <= umbral_cercania]) - 1
            st.metric("🎪 Jugadores Muy Similares", f"{cercanos}")
    
    # Top 10 más cercanos
    with st.expander("🔍 Ver los 10 jugadores más similares (por distancia PCA)"):
        if df_pca['es_seleccionado'].any():
            df_cercanos = df_pca[~df_pca['es_seleccionado']].nsmallest(10, 'distancia')
            df_cercanos_display = df_cercanos[[
                'nombre_jugador', 'equipo_principal', 'rating_promedio', 
                'valor_millones', 'distancia'
            ]].copy()
            df_cercanos_display.columns = ['Jugador', 'Equipo', 'Rating', 'Valor (€M)', 'Distancia PCA']
            df_cercanos_display['Distancia PCA'] = df_cercanos_display['Distancia PCA'].round(3)
            st.dataframe(df_cercanos_display, use_container_width=True, hide_index=True)

# ============================================================
# FUNCIÓN 3: GLOSARIO Y GUÍA DE INTERPRETACIÓN
# ============================================================

def mostrar_glosario():
    """Muestra guía de conceptos y limitaciones del análisis"""
    st.markdown("""
    ### 📚 Guía de Interpretación
    
    #### 🎯 ¿Qué muestran estas estadísticas?
    
    Este sistema analiza el **rendimiento estadístico** de jugadores basándose en datos objetivos de partidos. 
    Sin embargo, es importante entender sus alcances y limitaciones.
    
    ---
    
    #### 📊 Glosario de Métricas
    
    **Métricas Ofensivas:**
    - **xG (Expected Goals)**: Goles esperados según la calidad de las oportunidades generadas
    - **xA (Expected Assists)**: Asistencias esperadas según la calidad de los pases finales
    - **Goles/90 y Asist/90**: Promedios cada 90 minutos (un partido completo)
    - **Pases Progresivos**: Pases que avanzan significativamente hacia el arco rival
    - **Key Passes**: Pases que generan una oportunidad de gol
    - **Dribbles**: Regates exitosos superando a un rival
    
    **Métricas Defensivas:**
    - **Recoveries**: Recuperaciones de balón
    - **Tackles**: Entradas/barridas exitosas
    - **Interceptions**: Anticipaciones e interceptaciones
    - **Aerial Won**: Duelos aéreos ganados
    
    **Rating**: Nota promedio del rendimiento general (escala 0-10)
    
    **Percentiles**: Indican en qué posición está el jugador respecto a otros de su posición 
    (ej: percentil 90 = mejor que el 90% de jugadores en esa estadística)
    
    ---
    
    #### ⚠️ Limitaciones Importantes
    
    **Las estadísticas NO capturan:**
    - ✋ **Inteligencia táctica** y lectura del juego
    - 🧠 **Mentalidad** y capacidad de liderazgo
    - 💪 **Estado físico** y predisposición al esfuerzo
    - 🎭 **Contexto emocional** y situación personal
    - 👔 **Influencia del entrenador** y sistema de juego
    - 🏟️ **Nivel de la competición** donde juega
    - 👥 **Calidad de compañeros** que lo rodean
    - 🔄 **Adaptabilidad** a nuevos entornos o ligas
    - 🤕 **Historial de lesiones**
    - 🎯 **Posicionamiento** y movimientos sin balón
    
    ---
    
    #### 💡 ¿Cómo usar esta herramienta?
    
    **Este sistema es una PRIMERA APROXIMACIÓN**, no un veredicto final:
    
    1. **Filtro inicial**: Identifica jugadores con perfiles estadísticos similares
    2. **Generación de hipótesis**: Descubre opciones que quizás no habías considerado
    3. **Punto de partida**: Las estadísticas te dicen "dónde mirar", no "a quién fichar"
    
    **Después del análisis estadístico, es fundamental:**
    - 👀 Ver partidos completos del jugador
    - 🗣️ Consultar con scouts que lo hayan visto en vivo
    - 📞 Investigar su entorno personal y profesional
    - 🏥 Revisar historial médico
    - 💬 Hablar con personas que lo conocen (entrenadores, compañeros)
    
    ---
    
    #### 🎲 Ejemplo Práctico
    
    **Escenario**: El sistema encuentra un delantero de 24 años con xG alto y valor bajo
    
    **❌ Interpretación incorrecta:**  
    *"Este jugador es una ganga, hay que ficharlo ya"*
    
    **✅ Interpretación correcta:**  
    *"Este perfil estadístico es interesante. Valdría la pena:*
    - *Ver 3-4 partidos completos*
    - *Investigar por qué su valor es bajo (¿lesiones? ¿problemas de conducta? ¿liga menor?)*
    - *Evaluar si su estilo encaja con nuestro sistema de juego*
    - *Confirmar con scouts locales si el dato es real o hay contexto que explique los números"*
    
    ---
    
    #### 🧭 Filosofía de Uso
    
    > **"Los números abren puertas, pero no las cruzan por ti"**
    
    Las estadísticas son como un **mapa**: te muestran el terreno, pero no caminan en tu lugar.  
    Un buen proceso de scouting combina:
    
    - 📊 **30% Datos** (lo que se ve acá)
    - 👁️ **40% Observación directa** (ver jugar)
    - 🧠 **30% Contexto e intuición** (experiencia humana)
    
    ---
    
    Esta herramienta te ayuda a:
    - ✅ Reducir el universo de opciones
    - ✅ Encontrar patrones y similitudes objetivas
    - ✅ Validar o cuestionar intuiciones con datos
    - ✅ Descubrir jugadores en mercados menos visibles
    
    Pero **nunca reemplaza** el ojo experto, la conversación humana y el análisis de contexto.  
    
    """)

# ============================================================
# 3. HEADER
# ============================================================
st.title("⚽ Scouting Pro AI - Motor Vectorial de Similitud")
st.markdown("""
Sistema de recomendación basado en **K-Nearest Neighbors** con ponderación por posición y decay temporal.  
Encuentra jugadores similares usando xG, xA, pases progresivos, recuperaciones y más.
""")

# ============================================================
# 4. INICIALIZACIÓN DE CACHÉ (EJECUTA 1 SOLA VEZ)
# ============================================================
with st.spinner("🔄 Cargando índice de jugadores (solo la primera vez del día)..."):
    df_players_index = get_all_players_index(client)

st.sidebar.success(f"✅ Índice cargado: {len(df_players_index):,} jugadores")

# ============================================================
# 5. SIDEBAR - BÚSQUEDA Y FILTROS
# ============================================================
st.sidebar.header("🔍 Configuración de Búsqueda")

# Input de búsqueda con ayuda mejorada
nombre_buscar = st.sidebar.text_input(
    "Buscar Jugador", 
    placeholder="Ej: Mesii, Alvares, Echeveri",
    help="💡 **Búsqueda inteligente:** Escribe con errores de tipeo, sin tildes o mayúsculas. ¡Funciona igual!"
)

# Filtros adicionales
col_filtro1, col_filtro2 = st.sidebar.columns(2)
with col_filtro1:
    temp_origen_filter = st.selectbox(
        "Temporada Origen",
        options=[2025, 2024, 2023, 2022, 2021],
        index=1  # Default 2024
    )
with col_filtro2:
    min_score = st.slider(
        "Similitud Mínima %",
        min_value=0,
        max_value=100,
        value=30,
        step=5
    )


st.sidebar.divider()
if st.sidebar.button("📚 Guía de Interpretación", use_container_width=True):
    st.session_state['mostrar_glosario'] = not st.session_state.get('mostrar_glosario', False)

# 2. Mostrar glosario en el área principal (al inicio, después del título):

# Mostrar glosario si está activado
if st.session_state.get('mostrar_glosario', False):
    with st.container():
        mostrar_glosario()
        st.divider()

# Opciones avanzadas
with st.sidebar.expander("⚙️ Opciones Avanzadas"):
    umbral_fuzzy = st.slider(
        "Tolerancia de búsqueda (fuzzy)",
        min_value=50,
        max_value=100,
        value=70,
        step=5,
        help="Mayor = más estricto. Menor = encuentra más resultados con errores de tipeo"
    )
    
    if st.button("🗑️ Limpiar Caché Local"):
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
            st.cache_data.clear()
            st.success("✅ Caché eliminado. Recarga la página.")
        else:
            st.info("ℹ️ No hay caché para eliminar")

# ============================================================
# 6. BÚSQUEDA DE JUGADORES (AHORA LOCAL CON FUZZY)
# ============================================================
if nombre_buscar:
    try:
        # BÚSQUEDA LOCAL CON FUZZY MATCHING ⚡🔍
        df_search = buscar_jugadores_fuzzy(
            nombre_buscar, 
            temp_origen_filter, 
            df_players_index,
            umbral_fuzzy
        )
        
        if not df_search.empty:
            # Indicador de tipo de match
            if 'relevancia' in df_search.columns and df_search['relevancia'].iloc[0] < 100:
                st.sidebar.success(f"🎯 Encontrados {len(df_search)} resultados similares (fuzzy match)")
            else:
                st.sidebar.success(f"✅ Encontrados {len(df_search)} resultados exactos")
            
            # Formateo mejorado para sidebar
            df_search['label'] = (
                df_search['player'] + " | " + 
                df_search['equipo_principal'].str[:12] + " | " +
                df_search['posicion'] + " | ⭐" + 
                df_search['rating_promedio'].round(1).astype(str) + 
                " | " + df_search['partidos_jugados'].astype(str) + "P"
            )
            
            # Añadir indicador de relevancia si es fuzzy
            if 'relevancia' in df_search.columns:
                df_search['label'] = df_search.apply(
                    lambda x: f"[{x['relevancia']:.0f}%] {x['label']}" if x['relevancia'] < 100 else x['label'],
                    axis=1
                )
            
            seleccion_label = st.sidebar.selectbox(
                "📋 Selecciona versión del jugador:", 
                df_search['label']
            )
            
            # Recuperar datos de la selección
            row_origen = df_search[df_search['label'] == seleccion_label].iloc[0]
            id_origen = str(row_origen['player_id'])
            temp_origen = int(row_origen['temporada_anio'])

            # ============================================================
            # 7. PERFIL DEL JUGADOR SELECCIONADO (MOLDE)
            # ============================================================
            st.divider()
            st.subheader(f"🎯 Perfil del Molde: {row_origen['player']}")
            
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                st.metric("⚽ Equipo", f"{row_origen['equipo_principal']}")
            with col2:
                st.metric("📅 Temporada", f"{temp_origen}")
            with col3:
                st.metric("📊 Posición", f"{row_origen['posicion']}")
            with col4:
                st.metric("⭐ Rating", f"{row_origen['rating_promedio']:.2f}")
            with col5:
                st.metric("🎯 xG/90", f"{row_origen['xG_p90']:.2f}")
            with col6:
                st.metric("🏃 Partidos", f"{row_origen['partidos_jugados']}")
            
            st.info(f"💡 Buscando jugadores que jueguen estadísticamente como **{row_origen['player']} ({temp_origen})**")

            # ============================================================
            # NUEVAS SECCIONES: TIMELINE Y PCA
            # ============================================================

            st.divider()

            # Timeline de evolución
            with st.expander("📈 Ver Evolución Histórica", expanded=False):
                mostrar_timeline_evolucion(
                    player_id=int(id_origen),
                    nombre_jugador=row_origen['player'],
                    client=client
                )

            # Mapa PCA
            with st.expander("🗺️ Ver Mapa de Similitud (PCA)", expanded=False):
                mostrar_mapa_pca(
                    player_id_seleccionado=int(id_origen),
                    posicion=row_origen['posicion'],
                    temporada=temp_origen,
                    nombre_jugador=row_origen['player'],
                    client=client
                )

            # ============================================================
            # 8. TABS DE RESULTADOS
            # ============================================================
            st.divider()
            st.subheader("🔎 Jugadores Similares")
            
            tab_2025, tab_2024, tab_todas = st.tabs([
                "🆕 Temporada 2025", 
                "📅 Temporada 2024", 
                "📊 Todas las Temporadas"
            ])
            
            with tab_2025:
                mostrar_tab_temporada(2025, id_origen, temp_origen, min_score, "2025")
            
            with tab_2024:
                mostrar_tab_temporada(2024, id_origen, temp_origen, min_score, "2024")
            
            with tab_todas:
                mostrar_tab_temporada(None, id_origen, temp_origen, min_score, "todas")

        else:
            st.sidebar.warning("❌ No se encontraron jugadores con esos criterios")
            st.sidebar.info(f"""
            **💡 Tips de búsqueda:**
            - Intenta con menos letras (ej: "Mes" en vez de "Messi")
            - Reduce la tolerancia fuzzy (⚙️ Opciones Avanzadas)
            - Cambia la temporada de origen
            - Verifica que haya jugadores con 400+ minutos
            
            **Ejemplos que funcionan:**
            - "Mesii" → encuentra "Messi"
            - "Alvares" → encuentra "Álvarez"  
            - "Neyma" → encuentra "Neymar"
            """)
            
    except Exception as e:
        st.error(f"⚠️ Error en la consulta: {e}")

else:
    # Pantalla de inicio
    st.info("👈 Comienza escribiendo el nombre de un jugador en la barra lateral")
    
    # Estadísticas del sistema
    st.markdown("### 📊 Estadísticas del Sistema")
    
    col_stats1, col_stats2, col_stats3 = st.columns(3)
    
    # --- CORRECCION SQL 3: Stats apuntando a las tablas nuevas ---
    with col_stats1:
        query_stats = f"""
        SELECT COUNT(DISTINCT player_id) as total_jugadores
        FROM `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo`
        """
        total = client.query(query_stats).to_dataframe().iloc[0]['total_jugadores']
        st.metric("👥 Jugadores Únicos", f"{total:,}")
    
    with col_stats2:
        query_rel = f"""
        SELECT COUNT(*) as total_relaciones
        FROM `{PROJECT_ID}.{DATASET}.scouting_similitud_pro_v2`
        """
        total_rel = client.query(query_rel).to_dataframe().iloc[0]['total_relaciones']
        st.metric("🔗 Relaciones de Similitud", f"{total_rel:,}")
    
    with col_stats3:
        st.metric("📅 Temporadas", "2021-2025")