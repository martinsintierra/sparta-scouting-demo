import streamlit as st
import sys
from pathlib import Path

from utils.database import get_bigquery_client, get_system_stats
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Configuración de página
st.set_page_config(
    page_title="Scouting Pro AI", 
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

# Inicializar cliente BigQuery
if 'client' not in st.session_state:
    st.session_state.client = get_bigquery_client()

client = st.session_state.client

if not client:
    st.error("⚠️ No se pudo conectar a BigQuery")
    st.stop()

# Header
st.title("⚽ Scouting Pro AI - Motor Vectorial de Similitud")
st.markdown("""
Sistema de recomendación basado en **K-Nearest Neighbors** con ponderación por posición y decay temporal.  
Encuentra jugadores similares usando xG, xA, pases progresivos, recuperaciones y más.
""")

st.divider()

# Información del sistema
st.markdown("### 📊 Estadísticas del Sistema")

if client:
    try:
        stats = get_system_stats(client)
        
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        
        with col_stats1:
            st.metric("👥 Jugadores Únicos", f"{stats['total_jugadores']:,}")
        
        with col_stats2:
            st.metric("🔗 Relaciones de Similitud", f"{stats['total_relaciones']:,}")
        
        with col_stats3:
            st.metric("📅 Temporadas", stats['temporadas'])
    
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        st.error(f"❌ Error cargando estadísticas: {e}")
else:
    st.error("❌ No se pudo conectar a BigQuery. Verifica tu configuración.")

st.divider()

# Guía de uso
st.markdown("### 🚀 Comenzar")

col_nav1, col_nav2, col_nav3 = st.columns(3)

with col_nav1:
    st.markdown("""
    #### 🔍 Buscar Jugadores
    Encuentra jugadores similares a un perfil específico.
    - Búsqueda inteligente con tolerancia a errores
    - Filtros por temporada y similitud
    - Resultados detallados con radar charts
    
    [Ir a Buscar →](1_buscar)
    """)

with col_nav2:
    st.markdown("""
    #### ⚖️ Comparar Jugadores
    Compara lado a lado múltiples jugadores.
    - Comparación visual de estadísticas
    - Análisis de fortalezas/debilidades
    - Identificación de diferencias clave
    
    [Ir a Comparar →](Comparar)
    """)

with col_nav3:
    st.markdown("""
    #### 🗺️ Explorador PCA
    Visualiza perfiles en un mapa 2D.
    - Reducción dimensional inteligente
    - Identificación de clusters
    - Descubrimiento de patrones
    
    [Ir a Explorador →](Explorador_PCA)
    """)

st.divider()

# Características principales
st.markdown("### ✨ Características Principales")

col_feat1, col_feat2 = st.columns(2)

with col_feat1:
    st.markdown("""
    **🎯 Precisión del Modelo:**
    - Algoritmo K-NN con ponderación específica por posición
    - Decay temporal para priorizar datos recientes
    - Normalización por percentiles dentro de cada posición
    
    **📊 Métricas Analizadas:**
    - xG, xA (Expected Goals/Assists)
    - Pases progresivos y key passes
    - Dribbles exitosos
    - Recuperaciones y duelos aéreos
    - Rating promedio ponderado
    """)

with col_feat2:
    st.markdown("""
    **🔧 Herramientas Disponibles:**
    - Búsqueda fuzzy con corrección de errores
    - Visualización de evolución histórica
    - Mapas PCA de similitud
    - Comparaciones multi-jugador
    - Exportación de datos
    
    **🚀 Performance:**
    - Caché inteligente en disco (24h)
    - Búsquedas locales instantáneas
    - Queries optimizadas a BigQuery
    - Logging estructurado para debugging
    """)

st.divider()

# Footer
st.markdown("""
---
**💡 Sugerencia:** Comienza explorando la sección **🔍 Buscar** para encontrar jugadores similares a tu perfil ideal.

Para más información, consulta la **📚 Guía de Interpretación** en la barra lateral.
""")

logger.info("Home page rendered successfully")