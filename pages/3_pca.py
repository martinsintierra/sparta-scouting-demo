import streamlit as st
import sys
from pathlib import Path


from utils.database import get_all_players_index, obtener_datos_pca
from utils.search import buscar_jugadores_fuzzy
from utils.visualization import mostrar_mapa_pca
from utils.logger import setup_logger

logger = setup_logger(__name__)

st.set_page_config(page_title="Explorador PCA", layout="wide", page_icon="🗺️")

st.title("🗺️ Explorador PCA - Mapa de Similitudes")
st.markdown("""
Visualiza jugadores en un espacio bidimensional usando **PCA (Principal Component Analysis)**.  
Jugadores cercanos en el mapa tienen perfiles estadísticos similares.
""")

# Verificar cliente
if 'client' not in st.session_state:
    from utils.database import get_bigquery_client
    st.session_state.client = get_bigquery_client()

client = st.session_state.client

if not client:
    st.error("❌ Error de conexión con BigQuery")
    st.stop()

# Cargar índice
with st.spinner("📄 Cargando índice de jugadores..."):
    df_players_index = get_all_players_index(client)

# Sidebar - Configuración
st.sidebar.header("🔍 Seleccionar Jugador")

nombre_buscar = st.sidebar.text_input(
    "Buscar Jugador", 
    placeholder="Ej: Valentin Gomez, Lucas Castro...",
    help="Busca el jugador que quieres destacar en el mapa"
)

temporada_pca = st.sidebar.selectbox(
    "Temporada para Análisis",
    options=[2025, 2024, 2023, 2022, 2021],
    index=1
)

umbral_fuzzy = st.sidebar.slider(
    "Tolerancia de búsqueda",
    min_value=50,
    max_value=100,
    value=70,
    step=5
)

if nombre_buscar:
    df_search = buscar_jugadores_fuzzy(
        nombre_buscar, 
        temporada_pca, 
        df_players_index,
        umbral_fuzzy
    )
    
    if not df_search.empty:
        # Formatear labels
        from utils.search import format_player_label
        df_search['label'] = df_search.apply(
            lambda x: format_player_label(x, include_relevancia=True), 
            axis=1
        )
        
        seleccion_label = st.sidebar.selectbox(
            "📋 Selecciona jugador:", 
            df_search['label']
        )
        
        row_origen = df_search[df_search['label'] == seleccion_label].iloc[0]
        player_id = int(row_origen['player_id'])
        posicion = row_origen['posicion']
        nombre_jugador = row_origen['player']
        
        st.divider()
        
        # Información del jugador seleccionado
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👤 Jugador", nombre_jugador)
        with col2:
            st.metric("⚽ Equipo", row_origen['equipo_principal'])
        with col3:
            st.metric("📊 Posición", posicion)
        with col4:
            st.metric("📅 Temporada", temporada_pca)
        
        st.divider()
        
        # Obtener datos PCA
        with st.spinner("🔄 Calculando PCA..."):
            df_pca = obtener_datos_pca(posicion, temporada_pca, client)
        
        if not df_pca.empty:
            # Mostrar mapa
            mostrar_mapa_pca(
                player_id_seleccionado=player_id,
                posicion=posicion,
                temporada=temporada_pca,
                nombre_jugador=nombre_jugador,
                df_pca=df_pca
            )
        else:
            st.warning(f"⚠️ No hay suficientes datos para {posicion} en temporada {temporada_pca}")
    
    else:
        st.sidebar.warning("❌ No se encontraron jugadores con esos criterios")

else:
    st.info("👈 Comienza buscando un jugador en la barra lateral")
    
    st.markdown("""
    ### 🎯 ¿Qué es el análisis PCA?
    
    **PCA (Principal Component Analysis)** es una técnica de reducción dimensional que:
    
    - 📊 Toma múltiples métricas estadísticas (xG, xA, pases progresivos, etc.)
    - 🔄 Las reduce a 2 dimensiones visualizables
    - 🗺️ Mantiene la mayor información posible
    
    **Interpretación del mapa:**
    - Jugadores **cercanos** tienen perfiles **similares**
    - Jugadores **lejanos** tienen estilos de juego **diferentes**
    - Los **ejes** representan combinaciones de métricas originales
    
    **Casos de uso:**
    - Identificar clusters de jugadores con perfiles similares
    - Descubrir alternativas baratas a jugadores caros
    - Validar recomendaciones del modelo K-NN
    - Explorar toda una posición de forma visual
    """)