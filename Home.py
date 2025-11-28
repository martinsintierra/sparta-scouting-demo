import streamlit as st
import sys
from pathlib import Path

from utils.database import get_bigquery_client, get_system_stats
from utils.logger import setup_logger
from utils.i18n import language_selector, t, get_language

logger = setup_logger(__name__)

# Configuración de página
st.set_page_config(
    page_title=t("app_title"), 
    layout="wide", 
    page_icon="⚽",
    initial_sidebar_state="expanded"
)

# CSS personalizado
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

# Selector de idioma en sidebar (SIEMPRE VISIBLE)
language_selector()

# Inicializar cliente BigQuery
if 'client' not in st.session_state:
    st.session_state.client = get_bigquery_client()

client = st.session_state.client

if not client:
    st.error(f"⚠️ {t('connection_error')} BigQuery")
    st.stop()

# Header
st.title(t("home_title"))
st.markdown(f"""
{t("home_subtitle")}  
{t("home_description")}  
{t("home_coverage")}
""")

st.divider()

# Información del sistema
st.markdown(f"### 📊 {t('system_stats')}")

if client:
    try:
        stats = get_system_stats(client)
        
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        
        with col_stats1:
            st.metric(f"👥 {t('unique_players')}", f"{stats['total_jugadores']:,}")
        
        with col_stats2:
            st.metric(f"🔗 {t('similarity_relations')}", f"{stats['total_relaciones']:,}")
        
        with col_stats3:
            st.metric(f"📅 {t('seasons')}", stats['temporadas'])
    
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        st.error(f"❌ {t('error')}: {e}")
else:
    st.error(f"❌ {t('connection_error')} BigQuery.")

st.divider()

# Guía de uso
st.markdown(f"### {t('get_started')}")

col_nav1, col_nav2, col_nav3 = st.columns(3)

# Contenido específico por idioma
lang = get_language()

if lang == 'es':
    with col_nav1:
        st.markdown("""
        #### Buscar Jugadores
        Encuentra jugadores similares a un perfil específico.
        - Búsqueda inteligente con tolerancia a errores
        - Filtros por temporada y similitud
        - Resultados detallados con radar charts
        """)

    with col_nav2:
        st.markdown("""
        #### Comparar Jugadores
        Compara lado a lado múltiples jugadores.
        - Comparación visual de estadísticas
        - Análisis de fortalezas/debilidades
        - Identificación de diferencias clave
        """)

    with col_nav3:
        st.markdown("""
        #### Explorador PCA
        Visualiza perfiles en un mapa 2D.
        - Reducción dimensional inteligente
        - Identificación de clusters
        - Descubrimiento de patrones
        """)
else:  # English
    with col_nav1:
        st.markdown("""
        #### Search Players
        Find players similar to a specific profile.
        - Smart search with error tolerance
        - Filters by season and similarity
        - Detailed results with radar charts
        """)

    with col_nav2:
        st.markdown("""
        #### Compare Players
        Compare multiple players side by side.
        - Visual comparison of statistics
        - Strengths/weaknesses analysis
        - Key differences identification
        """)

    with col_nav3:
        st.markdown("""
        #### PCA Explorer
        Visualize profiles on a 2D map.
        - Smart dimensional reduction
        - Cluster identification
        - Pattern discovery
        """)

st.divider()

# Características principales
st.markdown(f"### ✨ {t('main_features')}")

col_feat1, col_feat2 = st.columns(2)

if lang == 'es':
    with col_feat1:
        st.markdown("""
        **Precisión del Modelo:**
        - Algoritmo K-NN con ponderación específica por posición
        - Decay temporal para priorizar datos recientes
        - Normalización por percentiles dentro de cada posición
        
        **Métricas Analizadas:**
        - xG, xA (Expected Goals/Assists)
        - Pases progresivos y key passes
        - Dribbles exitosos
        - Recuperaciones y duelos aéreos
        - Rating promedio ponderado
        """)

    with col_feat2:
        st.markdown("""
        **Herramientas Disponibles:**
        - Búsqueda fuzzy con corrección de errores
        - Visualización de evolución histórica
        - Mapas PCA de similitud
        - Comparaciones multi-jugador
        - Exportación de datos
        
        **Performance:**
        - Caché inteligente en disco (24h)
        - Búsquedas locales instantáneas
        - Queries optimizadas a BigQuery
        - Logging estructurado para debugging
        """)
else:  # English
    with col_feat1:
        st.markdown("""
        **Model Precision:**
        - K-NN algorithm with position-specific weighting
        - Temporal decay to prioritize recent data
        - Normalization by percentiles within each position
        
        **Analyzed Metrics:**
        - xG, xA (Expected Goals/Assists)
        - Progressive passes and key passes
        - Successful dribbles
        - Recoveries and aerial duels
        - Weighted average rating
        """)

    with col_feat2:
        st.markdown("""
        **Available Tools:**
        - Fuzzy search with error correction
        - Historical evolution visualization
        - PCA similarity maps
        - Multi-player comparisons
        - Data export
        
        **Performance:**
        - Smart disk cache (24h)
        - Instant local searches
        - Optimized BigQuery queries
        - Structured logging for debugging
        """)

st.divider()

# Footer
if lang == 'es':
    st.markdown("""
    ---
    **💡 Sugerencia:** Empezá explorando la sección Buscar para encontrar jugadores similares a tu perfil ideal.

    Para más información, consultá el Glosario (por favor) en la barra lateral!
    """)
else:
    st.markdown("""
    ---
    **💡 Tip:** Start by exploring the Search section to find players similar to your ideal profile.

    For more information, check the Glossary (please) in the sidebar!
    """)

logger.info(f"Home page rendered successfully (lang: {lang})")