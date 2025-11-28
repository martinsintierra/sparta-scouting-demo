import streamlit as st
import sys
from pathlib import Path

# Añadir directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import get_all_players_index, obtener_similares
from utils.search import buscar_jugadores_fuzzy, format_player_label
from utils.visualization import mostrar_tarjeta_jugador
from utils.logger import setup_logger, log_user_action

logger = setup_logger(__name__)

# Configuración
st.set_page_config(page_title="Buscar Jugadores", layout="wide", page_icon="🔍")

st.title("🔍 Buscar Jugadores Similares")
st.markdown("Encuentra jugadores con perfiles estadísticos similares usando búsqueda inteligente.")

# Verificar cliente
if 'client' not in st.session_state:
    from utils.database import get_bigquery_client
    st.session_state.client = get_bigquery_client()

client = st.session_state.client

if not client:
    st.error("❌ Error de conexión con BigQuery")
    st.stop()

# Cargar índice de jugadores (solo primera vez)
with st.spinner("📄 Cargando índice de jugadores..."):
    df_players_index = get_all_players_index(client)

st.sidebar.success(f"✅ Índice cargado: {len(df_players_index):,} jugadores")

# Sidebar - Búsqueda y filtros
st.sidebar.header("🔍 Configuración de Búsqueda")

nombre_buscar = st.sidebar.text_input(
    "Buscar Jugador", 
    placeholder="Ej: Messi, Alvarez, Echeverri",
    help="💡 **Búsqueda inteligente:** Escribe con errores de tipeo, sin tildes o mayúsculas. ¡Funciona igual!"
)

col_filtro1, col_filtro2 = st.sidebar.columns(2)
with col_filtro1:
    temp_origen_filter = st.selectbox(
        "Temporada Origen",
        options=[2025, 2024, 2023, 2022, 2021],
        index=1
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

# Búsqueda de jugadores
if nombre_buscar:
    try:
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
            
            # Formatear labels
            df_search['label'] = df_search.apply(
                lambda x: format_player_label(x, include_relevancia=True), 
                axis=1
            )
            
            seleccion_label = st.sidebar.selectbox(
                "📋 Selecciona versión del jugador:", 
                df_search['label']
            )
            
            # Recuperar datos
            row_origen = df_search[df_search['label'] == seleccion_label].iloc[0]
            id_origen = str(row_origen['player_id'])
            temp_origen = int(row_origen['temporada_anio'])
            
            log_user_action(logger, "jugador_seleccionado", {
                "player_id": id_origen,
                "nombre": row_origen['player'],
                "temporada": temp_origen
            })
            
            # Perfil del jugador seleccionado
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
            
            # Tabs de resultados
            st.divider()
            st.subheader("🔎 Jugadores Similares")
            
            tab_2025, tab_2024, tab_todas = st.tabs([
                "🆕 Temporada 2025", 
                "📅 Temporada 2024", 
                "📊 Todas las Temporadas"
            ])
            
            # Función auxiliar para mostrar resultados
            def mostrar_tab_temporada(temp_destino, key_suffix):
                df_results = obtener_similares(id_origen, temp_origen, temp_destino, min_score, client)
                
                if not df_results.empty:
                    st.success(f"✅ Encontrados {len(df_results)} jugadores similares")
                    
                    # Selector
                    jugadores_lista = [
                        f"{row['destino_nombre']} ({row['destino_equipo']}) - {row['score_similitud']:.1f}% | Temp {int(row['temporada_similar'])}" 
                        for _, row in df_results.iterrows()
                    ]
                    
                    jugador_seleccionado = st.selectbox(
                        "Ver detalles de:",
                        jugadores_lista,
                        key=f"select_{key_suffix}"
                    )
                    
                    idx = jugadores_lista.index(jugador_seleccionado)
                    jugador_detalle = df_results.iloc[idx]
                    
                    # Mostrar tarjeta
                    mostrar_tarjeta_jugador(jugador_detalle, f"{key_suffix}_{idx}")
                    
                    # Tabla resumen
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
                        
                        st.dataframe(df_display, use_container_width=True, hide_index=True)
                else:
                    st.warning(f"⚠️ No se encontraron jugadores similares con score >= {min_score}%")
                    st.markdown("""
                    **Sugerencias:**
                    - Reduce el porcentaje mínimo de similitud
                    - Prueba con otra temporada
                    - Verifica que existan datos para esta posición
                    """)
            
            with tab_2025:
                mostrar_tab_temporada(2025, "2025")
            
            with tab_2024:
                mostrar_tab_temporada(2024, "2024")
            
            with tab_todas:
                mostrar_tab_temporada(None, "todas")
        
        else:
            st.sidebar.warning("❌ No se encontraron jugadores con esos criterios")
            st.sidebar.info(f"""
            **💡 Tips de búsqueda:**
            - Intenta con menos letras (ej: "Mes" en vez de "Messi")
            - Reduce la tolerancia fuzzy (⚙️ Opciones Avanzadas)
            - Cambia la temporada de origen
            
            **Ejemplos que funcionan:**
            - "Mesii" → encuentra "Messi"
            - "Alvares" → encuentra "Álvarez"  
            """)
    
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}", exc_info=True)
        st.error(f"⚠️ Error en la consulta: {e}")

else:
    st.info("👈 Comienza escribiendo el nombre de un jugador en la barra lateral")
    
    st.markdown("""
    ### 💡 Cómo usar esta herramienta
    
    1. **Escribe** el nombre del jugador en la barra lateral
    2. **Selecciona** la temporada y nivel de similitud deseado
    3. **Explora** los resultados en las diferentes tabs
    4. **Analiza** los perfiles detallados con radares y métricas
    
    La búsqueda es inteligente y tolerante a errores de tipeo.
    """)