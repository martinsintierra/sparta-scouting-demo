import streamlit as st

from utils.database import get_all_players_index, obtener_datos_pca
from utils.search import buscar_jugadores_fuzzy
from utils.visualization import mostrar_mapa_pca
from utils.logger import setup_logger
from utils.i18n import language_selector, t, get_language
from utils.filters import (
    render_economic_filters_sidebar,
    aplicar_filtros_economicos
)

logger = setup_logger(__name__)

st.set_page_config(page_title=t("pca_title"), layout="wide", page_icon="🗺️")

# Selector de idioma
language_selector()

st.title(t("pca_title"))
st.markdown(f"""
{t("pca_subtitle")}  
{t("pca_description")}
""")

# Verificar cliente
if 'client' not in st.session_state:
    from utils.database import get_bigquery_client
    st.session_state.client = get_bigquery_client()

client = st.session_state.client

if not client:
    st.error(f"❌ {t('connection_error')} BigQuery")
    st.stop()

# Cargar índice
with st.spinner(f"🔄 {t('loading')}..."):
    df_players_index = get_all_players_index(client)

st.sidebar.divider()

config_filtros = render_economic_filters_sidebar(
    default_max_value=50,
    default_age_range=(16, 40),
    default_young_prospects=False,
    expanded=False
)

# Sidebar - Configuración
st.sidebar.header(f"🔍 {t('select_player')}")

nombre_buscar = st.sidebar.text_input(
    t("search_player"), 
    placeholder="Ej: Valentin Gomez, Lucas Castro..." if get_language() == 'es' else "e.g., Valentin Gomez, Lucas Castro...",
    help=t("search_help_pca")
)

temporada_pca = st.sidebar.selectbox(
    t("season_analysis"),
    options=[2025, 2024, 2023, 2022, 2021],
    index=1
)

umbral_fuzzy = st.sidebar.slider(
    t("search_tolerance"),
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
        # Aplicar filtros económicos a la búsqueda
        df_search = aplicar_filtros_economicos(
            df_search,
            config_filtros,
            prefijo_columnas=""
        )

    if not df_search.empty:
        # Formatear labels
        from utils.search import format_player_label
        df_search['label'] = df_search.apply(
            lambda x: format_player_label(x, include_relevancia=True), 
            axis=1
        )
        
        seleccion_label = st.sidebar.selectbox(
            f"📋 {t('select_player_list')}", 
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
            st.metric(f"👤 {t('player_name') if get_language() == 'en' else 'Jugador'}", nombre_jugador)
        with col2:
            st.metric(f"⚽ {t('team')}", row_origen['equipo_principal'])
        with col3:
            st.metric(f"📊 {t('position')}", posicion)
        with col4:
            st.metric(f"📅 {t('season')}", temporada_pca)
        
        st.divider()
        
        # Obtener datos PCA
        with st.spinner(f"🔄 {t('calculating_pca')}..."):
            df_pca = obtener_datos_pca(posicion, temporada_pca, client)

        if not df_pca.empty:
            # ✅ CORRECCIÓN: Solo aplicar filtro UNA vez
            df_pca_original = df_pca.copy()
            
            df_pca = aplicar_filtros_economicos(
                df_pca,
                config_filtros,
                prefijo_columnas=""
            )
            
            # Mostrar resumen si hubo filtrado
            if len(df_pca) < len(df_pca_original):
                st.info(
                    f"🔎 Mostrando {len(df_pca)} jugadores después de filtros "
                    f"(de {len(df_pca_original)} totales en {posicion})"
                )
            else:
                st.success(f"✅ {len(df_pca)} jugadores en {posicion} - Temp {temporada_pca}")
        
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
            st.warning(t("insufficient_data").format(posicion, temporada_pca))
    
    else:
        st.sidebar.warning(f"❌ {t('not_found')}")

else:
    st.info(t("start_searching"))
    
    # Explicación según idioma
    if get_language() == 'es':
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
    else:
        st.markdown("""
        ### 🎯 What is PCA analysis?
        
        **PCA (Principal Component Analysis)** is a dimensional reduction technique that:
        
        - 📊 Takes multiple statistical metrics (xG, xA, progressive passes, etc.)
        - 🔄 Reduces them to 2 visualizable dimensions
        - 🗺️ Maintains as much information as possible
        
        **Map interpretation:**
        - **Close** players have **similar** profiles
        - **Distant** players have **different** playing styles
        - The **axes** represent combinations of original metrics
        
        **Use cases:**
        - Identify clusters of players with similar profiles
        - Discover cheap alternatives to expensive players
        - Validate K-NN model recommendations
        - Visually explore an entire position
        """)

logger.info(f"PCA page rendered (lang: {get_language()})")