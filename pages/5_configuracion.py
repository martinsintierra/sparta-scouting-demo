import streamlit as st
import sys
from pathlib import Path


from utils.logger import setup_logger
from utils.database import CACHE_FILE, CACHE_DIR

logger = setup_logger(__name__)

st.set_page_config(page_title="Configuración", layout="wide", page_icon="⚙️")

st.title("⚙️ Configuración y Mantenimiento")
st.markdown("Panel de control para gestionar caché, logs y configuraciones del sistema.")

# Tabs de configuración
tab_cache, tab_logs, tab_about = st.tabs(["💾 Caché", "📋 Logs", "ℹ️ Acerca de"])

# TAB 1: Gestión de Caché
with tab_cache:
    st.header("💾 Gestión de Caché")
    
    st.markdown("""
    El sistema utiliza caché en disco y en memoria para optimizar el rendimiento.
    
    **Tipos de caché:**
    - **Caché en disco** (24h): Índice completo de jugadores
    - **Caché en memoria** (1h): Queries específicas y resultados de similitud
    """)
    
    col_cache1, col_cache2 = st.columns(2)
    
    with col_cache1:
        st.markdown("### 📂 Caché en Disco")
        
        if CACHE_FILE.exists():
            import os
            import time
            
            size_mb = os.path.getsize(CACHE_FILE) / (1024 * 1024)
            age_hours = (time.time() - os.path.getmtime(CACHE_FILE)) / 3600
            
            st.success(f"✅ Caché activo")
            st.metric("Tamaño", f"{size_mb:.2f} MB")
            st.metric("Antigüedad", f"{age_hours:.1f} horas")
            
            if st.button("🗑️ Limpiar Caché en Disco", use_container_width=True):
                try:
                    CACHE_FILE.unlink()
                    logger.info("Caché en disco eliminado manualmente")
                    st.success("✅ Caché eliminado. Recarga la página para regenerar.")
                except Exception as e:
                    logger.error(f"Error eliminando caché: {e}")
                    st.error(f"❌ Error: {e}")
        else:
            st.info("ℹ️ No hay caché en disco actualmente")
    
    with col_cache2:
        st.markdown("### 🧠 Caché en Memoria")
        
        if st.button("🔄 Limpiar Caché de Streamlit", use_container_width=True):
            st.cache_data.clear()
            logger.info("Caché de Streamlit limpiado manualmente")
            st.success("✅ Caché en memoria limpiado")
        
        st.markdown("""
        **Cuándo limpiar el caché:**
        - Si ves datos desactualizados
        - Después de cambios en BigQuery
        - Si hay errores persistentes
        """)

# TAB 2: Visualización de Logs
with tab_logs:
    st.header("📋 Logs del Sistema")
    
    log_dir = Path("logs")
    
    if log_dir.exists():
        log_files = sorted(log_dir.glob("scouting_*.log"), reverse=True)
        
        if log_files:
            st.success(f"✅ Encontrados {len(log_files)} archivos de log")
            
            # Selector de archivo
            log_file_selected = st.selectbox(
                "Seleccionar archivo de log",
                options=log_files,
                format_func=lambda x: x.name
            )
            
            # Opciones de visualización
            col_log1, col_log2 = st.columns(2)
            with col_log1:
                num_lines = st.slider("Número de líneas a mostrar", 10, 500, 100)
            with col_log2:
                nivel_filtro = st.selectbox(
                    "Filtrar por nivel",
                    options=["TODOS", "INFO", "WARNING", "ERROR", "DEBUG"]
                )
            
            # Mostrar logs
            if st.button("📖 Cargar Logs", use_container_width=True):
                try:
                    with open(log_file_selected, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # Filtrar por nivel si es necesario
                    if nivel_filtro != "TODOS":
                        lines = [l for l in lines if nivel_filtro in l]
                    
                    # Mostrar últimas N líneas
                    lines_to_show = lines[-num_lines:]
                    
                    st.code("".join(lines_to_show), language="log")
                    
                    st.info(f"Mostrando {len(lines_to_show)} de {len(lines)} líneas totales")
                
                except Exception as e:
                    st.error(f"❌ Error leyendo logs: {e}")
        else:
            st.info("ℹ️ No hay archivos de log disponibles")
    else:
        st.info("ℹ️ Directorio de logs no existe aún")
    
    st.divider()
    
    # Exportar logs
    st.markdown("### 📤 Exportar Logs")
    if st.button("💾 Descargar Logs del Día", use_container_width=True):
        from datetime import datetime
        log_today = log_dir / f"scouting_{datetime.now().strftime('%Y%m%d')}.log"
        
        if log_today.exists():
            with open(log_today, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            st.download_button(
                label="⬇️ Descargar",
                data=log_content,
                file_name=log_today.name,
                mime="text/plain"
            )
        else:
            st.warning("⚠️ No hay logs para hoy")

# TAB 3: Información del Sistema
with tab_about:
    st.header("ℹ️ Acerca de Scouting Pro AI")
    
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
    │   └── 5_Configuracion.py # Este panel
    └── utils/
        ├── database.py            # Queries a BigQuery
        ├── search.py              # Búsqueda fuzzy
        ├── visualization.py       # Componentes visuales
        └── logger.py              # Sistema de logging
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
    
    ### 📝 Versión y Mantenimiento
    
    **Versión:** 2.0.0 (Arquitectura Modular)
    **Última Actualización:** Noviembre 2025
    
    **Mejoras Recientes:**
    - ✅ Estructura modular de 5 páginas
    - ✅ Sistema de logging avanzado
    - ✅ Separación de lógica en `/utils`
    - ✅ Caché persistente optimizado
    - ✅ Búsqueda fuzzy mejorada
    
    ---
    
    ### 🐛 Reportar Problemas
    
    Si encuentras errores:
    1. Revisa los logs en la pestaña "📋 Logs"
    2. Intenta limpiar el caché
    3. Recarga la página
    4. Contacta al equipo de desarrollo con el log del error
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

logger.info("Configuración page rendered")