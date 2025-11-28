import streamlit as st
from pathlib import Path

from utils.logger import setup_logger
from utils.database import CACHE_FILE, CACHE_DIR
from utils.i18n import language_selector, t, get_language

logger = setup_logger(__name__)

st.set_page_config(page_title=t("config_title"), layout="wide", page_icon="⚙️")

# Selector de idioma
language_selector()

st.title(t("config_title"))
st.markdown(t("config_subtitle"))

# Tabs de configuración
tab_cache, tab_logs, tab_about = st.tabs([
    f"💾 {t('cache_tab')}", 
    f"📋 {t('logs_tab')}", 
    f"ℹ️ {t('about_tab')}"
])

# TAB 1: Gestión de Caché
with tab_cache:
    st.header(f"💾 {t('cache_management')}")
    
    if get_language() == 'es':
        st.markdown("""
        El sistema utiliza caché en disco y en memoria para optimizar el rendimiento.
        
        **Tipos de caché:**
        - **Caché en disco** (24h): Índice completo de jugadores
        - **Caché en memoria** (1h): Queries específicas y resultados de similitud
        """)
    else:
        st.markdown("""
        The system uses disk and memory cache to optimize performance.
        
        **Cache types:**
        - **Disk cache** (24h): Complete player index
        - **Memory cache** (1h): Specific queries and similarity results
        """)
    
    col_cache1, col_cache2 = st.columns(2)
    
    with col_cache1:
        st.markdown(f"### 📂 {t('disk_cache')}")
        
        if CACHE_FILE.exists():
            import os
            import time
            
            size_mb = os.path.getsize(CACHE_FILE) / (1024 * 1024)
            age_hours = (time.time() - os.path.getmtime(CACHE_FILE)) / 3600
            
            st.success(f"✅ {t('cache_active')}")
            st.metric(t("size"), f"{size_mb:.2f} MB")
            st.metric(t("age"), f"{age_hours:.1f} {t('hours')}")
            
            if st.button(f"🗑️ {t('clear_disk_cache')}", use_container_width=True):
                try:
                    CACHE_FILE.unlink()
                    logger.info("Caché en disco eliminado manualmente")
                    st.success(f"✅ {t('cache_cleared')}")
                except Exception as e:
                    logger.error(f"Error eliminando caché: {e}")
                    st.error(f"❌ {t('error')}: {e}")
        else:
            if get_language() == 'es':
                st.info("ℹ️ No hay caché en disco actualmente")
            else:
                st.info("ℹ️ No disk cache currently")
    
    with col_cache2:
        st.markdown(f"### 🧠 {t('memory_cache')}")
        
        if st.button(f"🔄 {t('clear_memory_cache')}", use_container_width=True):
            st.cache_data.clear()
            logger.info("Caché de Streamlit limpiado manualmente")
            st.success(f"✅ {t('cache_cleared')}")
        
        st.markdown(f"""
        **{t('when_to_clear')}:**
        """)
        
        if get_language() == 'es':
            st.markdown("""
            - Si ves datos desactualizados
            - Después de cambios en BigQuery
            - Si hay errores persistentes
            """)
        else:
            st.markdown("""
            - If you see outdated data
            - After BigQuery changes
            - If there are persistent errors
            """)

# TAB 2: Visualización de Logs
with tab_logs:
    st.header(f"📋 {t('system_logs')}")
    
    log_dir = Path("logs")
    
    if log_dir.exists():
        log_files = sorted(log_dir.glob("scouting_*.log"), reverse=True)
        
        if log_files:
            st.success(t("log_files_found").format(len(log_files)))
            
            # Selector de archivo
            log_file_selected = st.selectbox(
                t("select_log_file"),
                options=log_files,
                format_func=lambda x: x.name
            )
            
            # Opciones de visualización
            col_log1, col_log2 = st.columns(2)
            with col_log1:
                num_lines = st.slider(t("num_lines"), 10, 500, 100)
            with col_log2:
                if get_language() == 'es':
                    nivel_filtro = st.selectbox(
                        t("filter_level"),
                        options=["TODOS", "INFO", "WARNING", "ERROR", "DEBUG"]
                    )
                else:
                    nivel_filtro = st.selectbox(
                        t("filter_level"),
                        options=["ALL", "INFO", "WARNING", "ERROR", "DEBUG"]
                    )
            
            # Mostrar logs
            if st.button(f"📖 {t('load_logs')}", use_container_width=True):
                try:
                    with open(log_file_selected, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # Filtrar por nivel si es necesario
                    if nivel_filtro not in ["TODOS", "ALL"]:
                        lines = [l for l in lines if nivel_filtro in l]
                    
                    # Mostrar últimas N líneas
                    lines_to_show = lines[-num_lines:]
                    
                    st.code("".join(lines_to_show), language="log")
                    
                    if get_language() == 'es':
                        st.info(f"Mostrando {len(lines_to_show)} de {len(lines)} líneas totales")
                    else:
                        st.info(f"Showing {len(lines_to_show)} of {len(lines)} total lines")
                
                except Exception as e:
                    st.error(f"❌ {t('error')}: {e}")
        else:
            if get_language() == 'es':
                st.info("ℹ️ No hay archivos de log disponibles")
            else:
                st.info("ℹ️ No log files available")
    else:
        if get_language() == 'es':
            st.info("ℹ️ Directorio de logs no existe aún")
        else:
            st.info("ℹ️ Logs directory doesn't exist yet")
    
    st.divider()
    
    # Exportar logs
    st.markdown(f"### 📤 {t('export_logs')}")
    if st.button(f"💾 {t('download_today_logs')}", use_container_width=True):
        from datetime import datetime
        log_today = log_dir / f"scouting_{datetime.now().strftime('%Y%m%d')}.log"
        
        if log_today.exists():
            with open(log_today, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            st.download_button(
                label=f"⬇️ {t('download')}",
                data=log_content,
                file_name=log_today.name,
                mime="text/plain"
            )
        else:
            if get_language() == 'es':
                st.warning("⚠️ No hay logs para hoy")
            else:
                st.warning("⚠️ No logs for today")

# TAB 3: Información del Sistema
with tab_about:
    st.header(f"ℹ️ {t('about_tab')} Scouting Pro AI")
    
    if get_language() == 'es':
        st.markdown("""
        ### 🎯 Arquitectura del Sistema
        
        **Stack Tecnológico:**
        - **Frontend**: Streamlit
        - **Backend**: Google BigQuery
        - **ML**: K-Nearest Neighbors (KNN), PCA
        - **Búsqueda**: FuzzyWuzzy (Levenshtein Distance)
        - **Visualización**: Plotly, Pandas
        
        **Estructura Modular:**
        ```
        proyecto/
        ├── Home.py                    # Landing page
        ├── pages/
        │   ├── 1_Buscar.py        # Búsqueda principal
        │   ├── 2_Comparar.py      # Comparaciones
        │   ├── 3_Explorador_PCA.py # Mapas de similitud
        │   ├── 4_Evolucion.py     # Análisis temporal
        │   ├── 5_Configuracion.py # Este panel
        │   └── 6_Glosario.py      # Documentación
        └── utils/
            ├── database.py            # Queries a BigQuery
            ├── search.py              # Búsqueda fuzzy
            ├── visualization.py       # Componentes visuales
            ├── logger.py              # Sistema de logging
            └── i18n.py                # Internacionalización
        ```
        
        ---
        
        ### 📊 Modelo de Similitud
        
        **Algoritmo K-NN con Ponderación Específica:**
        
        El sistema utiliza K-Nearest Neighbors con pesos ajustados por posición:
        
        - **Delanteros**: Mayor peso en xG, xA, dribbles
        - **Mediocampistas**: Mayor peso en pases progresivos, key passes
        - **Defensores**: Mayor peso en recuperaciones, duelos aéreos, tackles
        
        **Decay Temporal:** Prioriza datos recientes sobre históricos
        
        **Normalización:** Por percentiles dentro de cada posición
        
        ---
        
        ### 🔍 Búsqueda Fuzzy
        
        Utiliza **Levenshtein Distance** para encontrar coincidencias aproximadas:
        
        - Tolerante a errores de tipeo
        - Insensible a tildes y mayúsculas
        - Búsqueda parcial (substring matching)
        
        **Ejemplo:** "Mesii" encuentra "Messi" con 90% de similitud
        
        ---
        
        ### 📈 Análisis PCA
        
        **Principal Component Analysis** reduce 7+ métricas a 2 dimensiones:
        
        - PC1 y PC2 explican ~70-80% de la varianza
        - Jugadores cercanos = perfiles similares
        - Permite visualizar clusters de estilos de juego
        
        ---
        
        ### ⚡ Optimizaciones de Performance
        
        1. **Caché en Disco (24h)**: Índice completo de jugadores
        2. **Caché en Memoria (1h)**: Queries específicas
        3. **Búsqueda Local**: Sin hits a BigQuery por búsqueda
        4. **Queries Optimizadas**: Uso de vistas materializadas
        5. **Logging Estructurado**: Monitoreo de performance
        
        ---
        
        ### 🔢 Versión y Mantenimiento
        
        **Versión:** 2.1.0 (Arquitectura Modular + i18n)
        **Última Actualización:** Noviembre 2025
        
        **Mejoras Recientes:**
        - ✅ Sistema multiidioma (ES/EN)
        - ✅ Estructura modular de 6 páginas
        - ✅ Sistema de logging avanzado
        - ✅ Separación de lógica en `/utils`
        - ✅ Caché persistente optimizado
        - ✅ Búsqueda fuzzy mejorada
        """)
    else:
        st.markdown("""
        ### 🎯 System Architecture
        
        **Technology Stack:**
        - **Frontend**: Streamlit
        - **Backend**: Google BigQuery
        - **ML**: K-Nearest Neighbors (KNN), PCA
        - **Search**: FuzzyWuzzy (Levenshtein Distance)
        - **Visualization**: Plotly, Pandas
        
        **Modular Structure:**
        ```
        project/
        ├── Home.py                    # Landing page
        ├── pages/
        │   ├── 1_Buscar.py        # Main search
        │   ├── 2_Comparar.py      # Comparisons
        │   ├── 3_Explorador_PCA.py # Similarity maps
        │   ├── 4_Evolucion.py     # Temporal analysis
        │   ├── 5_Configuracion.py # This panel
        │   └── 6_Glosario.py      # Documentation
        └── utils/
            ├── database.py            # BigQuery queries
            ├── search.py              # Fuzzy search
            ├── visualization.py       # Visual components
            ├── logger.py              # Logging system
            └── i18n.py                # Internationalization
        ```
        
        ---
        
        ### 📊 Similarity Model
        
        **K-NN Algorithm with Specific Weighting:**
        
        The system uses K-Nearest Neighbors with position-adjusted weights:
        
        - **Forwards**: Higher weight on xG, xA, dribbles
        - **Midfielders**: Higher weight on progressive passes, key passes
        - **Defenders**: Higher weight on recoveries, aerial duels, tackles
        
        **Temporal Decay:** Prioritizes recent data over historical
        
        **Normalization:** By percentiles within each position
        
        ---
        
        ### 🔍 Fuzzy Search
        
        Uses **Levenshtein Distance** to find approximate matches:
        
        - Typo tolerant
        - Accent and case insensitive
        - Partial search (substring matching)
        
        **Example:** "Mesii" finds "Messi" with 90% similarity
        
        ---
        
        ### 📈 PCA Analysis
        
        **Principal Component Analysis** reduces 7+ metrics to 2 dimensions:
        
        - PC1 and PC2 explain ~70-80% of variance
        - Close players = similar profiles
        - Allows visualization of playing style clusters
        
        ---
        
        ### ⚡ Performance Optimizations
        
        1. **Disk Cache (24h)**: Complete player index
        2. **Memory Cache (1h)**: Specific queries
        3. **Local Search**: No BigQuery hits per search
        4. **Optimized Queries**: Use of materialized views
        5. **Structured Logging**: Performance monitoring
        
        ---
        
        ### 🔢 Version and Maintenance
        
        **Version:** 2.1.0 (Modular Architecture + i18n)
        **Last Update:** November 2025
        
        **Recent Improvements:**
        - ✅ Multi-language system (ES/EN)
        - ✅ Modular structure with 6 pages
        - ✅ Advanced logging system
        - ✅ Logic separation in `/utils`
        - ✅ Optimized persistent cache
        - ✅ Improved fuzzy search
        """)
    
    st.divider()
    
    # Información técnica
    col_tech1, col_tech2, col_tech3 = st.columns(3)
    
    with col_tech1:
        st.metric("🐍 Python", "3.10+")
    with col_tech2:
        st.metric("📊 Streamlit", "1.28+")
    with col_tech3:
        st.metric("☁️ BigQuery", "v2")

logger.info(f"Configuracion page rendered (lang: {get_language()})")