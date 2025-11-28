import streamlit as st
from utils.database import get_all_players_index, obtener_similares, obtener_percentiles_molde
from utils.search import buscar_jugadores_fuzzy, format_player_label
from utils.visualization import mostrar_tarjeta_jugador_comparativa
from utils.logger import setup_logger, log_user_action
from utils.i18n import language_selector, t, get_language

logger = setup_logger(__name__)

# Configuración
st.set_page_config(page_title=t("page_search"), layout="wide", page_icon="🔍")

# Selector de idioma
language_selector()

st.title(t("search_title"))
st.markdown(t("search_subtitle"))

# Verificar cliente
if 'client' not in st.session_state:
    from utils.database import get_bigquery_client
    st.session_state.client = get_bigquery_client()

client = st.session_state.client

if not client:
    st.error(f"❌ {t('connection_error')} BigQuery")
    st.stop()

# Cargar índice de jugadores (solo primera vez)
with st.spinner(f"🔄 {t('loading')}..."):
    df_players_index = get_all_players_index(client)

st.sidebar.success(f"✅ {t('index_loaded', num=len(df_players_index))}")

# Sidebar - Búsqueda y filtros
st.sidebar.header(f"🔍 {t('search_config')}")

nombre_buscar = st.sidebar.text_input(
    t("search_player"), 
    placeholder=t("search_placeholder"),
    help=t("search_help")
)

col_filtro1, col_filtro2 = st.sidebar.columns(2)
with col_filtro1:
    temp_origen_filter = st.selectbox(
        t("origin_season"),
        options=[2025, 2024, 2023, 2022, 2021],
        index=0
    )

with col_filtro2:
    min_score = st.slider(
        t("min_similarity"),
        min_value=0,
        max_value=100,
        value=30,
        step=5
    )

st.sidebar.divider()

# Opciones avanzadas
with st.sidebar.expander(f"⚙️ {t('advanced_options')}"):
    umbral_fuzzy = st.slider(
        t("fuzzy_tolerance"),
        min_value=50,
        max_value=100,
        value=70,
        step=5,
        help=t("fuzzy_help")
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
                st.sidebar.success(t("results_found").format(len(df_search)) + f" ({t('fuzzy_match')})")
            else:
                st.sidebar.success(t("results_found").format(len(df_search)) + f" ({t('exact_match')})")
            
            # Formatear labels
            df_search['label'] = df_search.apply(
                lambda x: format_player_label(x, include_relevancia=True), 
                axis=1
            )
            
            seleccion_label = st.sidebar.selectbox(
                t("select_version"), 
                df_search['label']
            )
            
            # Recuperar datos
            row_origen = df_search[df_search['label'] == seleccion_label].iloc[0]
            id_origen = str(row_origen['player_id'])
            temp_origen = int(row_origen['temporada_anio'])
            
            log_user_action(logger, "jugador_seleccionado", {
                "player_id": id_origen,
                "nombre": row_origen['player'],
                "temporada": temp_origen,
                "language": get_language()
            })
            
            percentiles_molde = obtener_percentiles_molde(
                player_id=int(id_origen),
                temporada=temp_origen,
                _client=client
            )
            
            row_origen_enriquecido = row_origen.copy()
            for key, value in percentiles_molde.items():
                row_origen_enriquecido[key] = value

            # Perfil del jugador seleccionado
            st.divider()
            st.subheader(f"🎯 {t('mold_profile')}: {row_origen['player']}")
            
            # Métricas principales
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                st.metric(f"⚽ {t('team')}", f"{row_origen['equipo_principal']}")
            with col2:
                st.metric(f"📅 {t('season')}", f"{temp_origen}")
            with col3:
                st.metric(f"📊 {t('position')}", f"{row_origen['posicion']}")
            with col4:
                st.metric(f"⭐ {t('rating')}", f"{row_origen['rating_promedio']:.2f}")
            with col5:
                st.metric("🎯 xG/90", f"{row_origen['xG_p90']:.2f}")
            with col6:
                st.metric(f"🏃 {t('matches')}", f"{row_origen['partidos_jugados']}")
            
            # Info de búsqueda
            lang = get_language()
            if lang == 'es':
                st.info(f"💡 Buscando jugadores que jueguen estadísticamente como **{row_origen['player']} ({temp_origen})**")
            else:
                st.info(f"💡 Searching for players who play statistically like **{row_origen['player']} ({temp_origen})**")
            
            # Tabs de resultados
            st.divider()
            st.subheader(f"🔎 {t('similar_players')}")
            
            tab_2025, tab_2024, tab_todas = st.tabs([
                f"🆕 {t('tab_season_2025')}", 
                f"📅 {t('tab_season_2024')}", 
                f"📊 {t('tab_all_seasons')}"
            ])
            
            # Función auxiliar para mostrar resultados
            def mostrar_tab_temporada(temp_destino, key_suffix):
                df_results = obtener_similares(id_origen, temp_origen, temp_destino, min_score, client)
                
                if not df_results.empty:
                    st.success(f"✅ {t('results_found').format(len(df_results))}")
                    
                    # Distribución de scores
                    max_score = df_results['score_similitud'].max()
                    avg_score = df_results['score_similitud'].mean()
                    
                    col_info1, col_info2, col_info3 = st.columns(3)
                    with col_info1:
                        st.metric(f"🎯 {t('best_match')}", f"{max_score:.1f}%")
                    with col_info2:
                        st.metric(f"📊 {t('average')}", f"{avg_score:.1f}%")
                    with col_info3:
                        if max_score >= 45:
                            calidad = "Excellent" if get_language() == 'en' else "Excelente"
                        elif max_score >= 35:
                            calidad = "Good" if get_language() == 'en' else "Bueno"
                        elif max_score >= 25:
                            calidad = "Acceptable" if get_language() == 'en' else "Aceptable"
                        else:
                            calidad = "Low" if get_language() == 'en' else "Bajo"
                        st.metric(f"✅ {t('quality')}", calidad)
                    
                    # Selector
                    jugadores_lista = [
                        f"{row['destino_nombre']} ({row['destino_equipo']}) - {row['score_similitud']:.1f}% | Temp {int(row['temporada_similar'])}" 
                        for _, row in df_results.iterrows()
                    ]
                    
                    jugador_seleccionado = st.selectbox(
                        t("view_details"),
                        jugadores_lista,
                        key=f"select_{key_suffix}"
                    )
                    
                    idx = jugadores_lista.index(jugador_seleccionado)
                    jugador_detalle = df_results.iloc[idx]
                    
                    # Mostrar tarjeta COMPARATIVA
                    mostrar_tarjeta_jugador_comparativa(
                        jugador_detalle=jugador_detalle,
                        molde=row_origen_enriquecido,
                        unique_key=f"{key_suffix}_{idx}"
                    )
                    
                    # Tabla resumen
                    with st.expander(f"📋 {t('view_full_table')}"):
                        df_display = df_results[[
                            'destino_nombre', 'destino_equipo', 'posicion', 
                            'temporada_similar', 'score_similitud', 'destino_edad',
                            'destino_rating', 'destino_xg', 'destino_xa', 
                            'destino_partidos', 'destino_minutos'
                        ]].copy()
                        
                        # Traducir headers
                        if get_language() == 'en':
                            df_display.columns = [
                                'Player', 'Team', 'Pos', 'Season', 'Match%', 'Age',
                                'Rating', 'xG/90', 'xA/90', 'MP', 'Minutes'
                            ]
                        else:
                            df_display.columns = [
                                'Jugador', 'Equipo', 'Pos', 'Temp', 'Match%', 'Edad',
                                'Rating', 'xG/90', 'xA/90', 'PJ', 'Minutos'
                            ]
                        
                        st.dataframe(df_display, use_container_width=True, hide_index=True)
                else:
                    st.warning(t("no_results").format(min_score))
                    st.markdown(f"""
                    **{t('search_suggestions')}:**
                    - {t('reduce_min_similarity')}
                    - {t('try_another_season')}
                    - {t('verify_position_data')}
                    """)
            
            with tab_2025:
                mostrar_tab_temporada(2025, "2025")
            
            with tab_2024:
                mostrar_tab_temporada(2024, "2024")
            
            with tab_todas:
                mostrar_tab_temporada(None, "todas")
        
        else:
            st.sidebar.warning(f"❌ {t('not_found')}")
    
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}", exc_info=True)
        st.error(f"⚠️ {t('error')}: {e}")

else:
    st.info(t("start_typing"))
    
    # Instrucciones según idioma
    if get_language() == 'es':
        st.markdown("""
        ### 💡 Cómo usar esta herramienta
        
        1. **Escribí** el nombre del jugador en la barra lateral
        2. **Seleccioná** la temporada y nivel de similitud deseado
        3. **Explorá** los resultados en las diferentes tabs
        4. **Analizá** los perfiles detallados con radares y métricas
        
        La búsqueda es inteligente y tolerante a errores de tipeo.
        """)
    else:
        st.markdown("""
        ### 💡 How to use this tool
        
        1. **Type** the player's name in the sidebar
        2. **Select** the season and desired similarity level
        3. **Explore** the results in different tabs
        4. **Analyze** detailed profiles with radars and metrics
        
        The search is smart and typo-tolerant.
        """)

logger.info(f"Buscar page rendered (lang: {get_language()})")