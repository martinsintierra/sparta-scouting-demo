import streamlit as st
import pandas as pd
from utils.database import get_all_players_index, obtener_similares, obtener_percentiles_molde
from utils.search import buscar_jugadores_fuzzy, format_player_label
from utils.visualization_adaptive import mostrar_tarjeta_jugador_adaptativa
from utils.logger import setup_logger, log_user_action
from utils.i18n import language_selector, t, get_language
from utils.filters import (
    render_economic_filters_sidebar,
    aplicar_filtros_economicos,
    mostrar_resumen_filtrado,
    calcular_proyeccion_mejorada,
    mostrar_badge_proyeccion
)

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

st.sidebar.success(f"✅ Índice cargado: {len(df_players_index)} jugadores")

# ========== SIDEBAR - BÚSQUEDA Y FILTROS ==========
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

# ========== FILTROS ECONÓMICOS (MODULAR) ==========
config_filtros = render_economic_filters_sidebar(
    default_max_value=50,
    default_age_range=(16, 40),
    default_young_prospects=False,
    expanded=False
)

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

st.sidebar.divider()

# ========== BÚSQUEDA DE JUGADORES ==========
if nombre_buscar:
    try:
        # Búsqueda inicial
        df_search = buscar_jugadores_fuzzy(
            nombre_buscar, 
            temp_origen_filter, 
            df_players_index,
            umbral_fuzzy
        )
        
        if not df_search.empty:
            # APLICAR FILTROS ECONÓMICOS
            df_search_original = df_search.copy()
            df_search = aplicar_filtros_economicos(
                df_search, 
                config_filtros,
                prefijo_columnas=""  # Búsqueda inicial no tiene prefijo
            )
            
            # Mostrar resumen de filtrado
            mostrar_resumen_filtrado(
                total_original=len(df_search_original),
                total_filtrado=len(df_search),
                config_filtros=config_filtros
            )
            
            if df_search.empty:
                st.sidebar.warning(t('no_players_in_range'))
                st.warning(t('adjust_filters'))
                st.stop()
            
            # Indicador de tipo de match
            if 'relevancia' in df_search.columns and df_search['relevancia'].iloc[0] < 100:
                st.sidebar.success(
                    f"✅ {len(df_search)} resultados ({t('fuzzy_match')})"
                )
            else:
                st.sidebar.success(
                    f"✅ {len(df_search)} resultados ({t('exact_match')})"
                )
            
            # Formatear labels CON BADGE DE PROYECCIÓN
            def format_label_with_projection(row):
                proyeccion = calcular_proyeccion_mejorada(row)
                label_base = format_player_label(row, include_relevancia=True)
                
                if proyeccion['delta_proyectado_pct'] > 15:
                    return f"{proyeccion['emoji']} {label_base}"
                return label_base
            
            df_search['label'] = df_search.apply(format_label_with_projection, axis=1)
            
            seleccion_label = st.sidebar.selectbox(
                t("select_version"), 
                df_search['label']
            )
            
            # Recuperar datos del jugador seleccionado
            row_origen = df_search[df_search['label'] == seleccion_label].iloc[0]
            id_origen = str(row_origen['player_id'])
            temp_origen = int(row_origen['temporada_anio'])
            
            # Mostrar badge de proyección en sidebar
            proyeccion_seleccionado = calcular_proyeccion_mejorada(row_origen)
            if proyeccion_seleccionado['delta_proyectado_pct'] > 10:
                mostrar_badge_proyeccion(proyeccion_seleccionado, use_sidebar=True)
            
            log_user_action(logger, "jugador_seleccionado", {
                "player_id": id_origen,
                "nombre": row_origen['player'],
                "temporada": temp_origen,
                "language": get_language(),
                "filtros": config_filtros
            })
            
            # Obtener percentiles del molde
            percentiles_molde = obtener_percentiles_molde(
                player_id=int(id_origen),
                temporada=temp_origen,
                _client=client
            )
            
            row_origen_enriquecido = row_origen.copy()
            for key, value in percentiles_molde.items():
                row_origen_enriquecido[key] = value

            # ========== PERFIL DEL JUGADOR MOLDE (ADAPTATIVO) ==========
            st.divider()
            st.subheader(f"🎯 {t('mold_profile')}: {row_origen['player']}")
            
            # ✅ NUEVO: Importar configuración adaptativa
            from utils.visualization_adaptive import get_position_metrics
            
            posicion_molde = row_origen['posicion']
            config_molde = get_position_metrics(posicion_molde)
            
            # Métricas generales (siempre se muestran)
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                st.metric(f"⚽ {t('team')}", f"{row_origen['equipo_principal'][:15]}")
            with col2:
                st.metric(f"📅 {t('season')}", f"{temp_origen}")
            with col3:
                st.metric(f"📊 {t('position')}", f"{posicion_molde}")
            with col4:
                st.metric(f"⭐ {t('rating')}", f"{row_origen['rating_promedio']:.2f}")
            with col5:
                st.metric("🏃 Partidos", f"{int(row_origen['partidos_jugados'])}")
            with col6:
                st.metric("⏱️ Minutos", f"{int(row_origen.get('total_minutos', 0))}")
            
            # ✅ NUEVO: Mostrar stats ESPECÍFICAS de la posición
            st.markdown(f"#### 📊 Métricas Clave - {posicion_molde}")
            
            cols_stats = st.columns(6)
            
            metrics_to_show = config_molde['mold_metrics']

            # Desempaquetamos solo dos valores: la clave de la columna y la etiqueta
            for idx, (col_key, label) in enumerate(metrics_to_show):
                with cols_stats[idx]:
                    # Verificamos si la clave existe y si el valor no es nulo
                    if col_key in row_origen and pd.notna(row_origen[col_key]):
                        valor = row_origen[col_key]
                        st.metric(label, f"{valor:.2f}")
                    else:
                        st.metric(label, "N/A")
                        # Info de búsqueda
            st.info(
                f"💡 Buscando jugadores que jueguen estadísticamente como **{row_origen['player']} ({temp_origen})**"
                if get_language() == 'es' else
                f"💡 Searching for players who play statistically like **{row_origen['player']} ({temp_origen})**"
            )
            
            # ========== TABS DE RESULTADOS ==========
            st.divider()
            st.subheader(f"🔎 {t('similar_players')}")
            
            tab_2025, tab_2024, tab_todas = st.tabs([
                f"🆕 {t('tab_season_2025')}", 
                f"📅 {t('tab_season_2024')}", 
                f"📊 {t('tab_all_seasons')}"
            ])
            
            # ========== FUNCIÓN PARA MOSTRAR RESULTADOS EN CADA TAB ==========
            def mostrar_tab_temporada(temp_destino, key_suffix):
                df_results = obtener_similares(id_origen, temp_origen, temp_destino, min_score, client)
                
                # APLICAR FILTROS ECONÓMICOS A RESULTADOS
                if not df_results.empty:
                    df_results_original = df_results.copy()
                    
                    df_results = aplicar_filtros_economicos(
                        df_results,
                        config_filtros,
                        prefijo_columnas="destino_"  # Resultados tienen prefijo "destino_"
                    )
                    
                    # Mostrar resumen si hubo filtrado
                    if len(df_results) < len(df_results_original):
                        st.info(
                            f"🔎 {t('showing_filtered').format(len(df_results))} "
                            f"(de {len(df_results_original)} totales antes de filtros)"
                        )
                
                if not df_results.empty:
                    st.success(f"✅ {len(df_results)} {t('similar_players').lower()}")
                    
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
                    
                    # Selector de jugador CON BADGES
                    jugadores_lista = []
                    for _, row in df_results.iterrows():
                        proyeccion_similar = calcular_proyeccion_mejorada(row)
                        
                        label = (
                            f"{row['destino_nombre']} ({row['destino_equipo'][:12]}) - "
                            f"{row['score_similitud']:.1f}% | Temp {int(row['temporada_similar'])}"
                        )
                        
                        # Agregar emoji de proyección si aplica
                        if proyeccion_similar['delta_proyectado_pct'] > 15:
                            label = f"{proyeccion_similar['emoji']} {label}"
                        
                        # Badge de oportunidad
                        if proyeccion_similar.get('valor_oportunidad'):
                            label = f"💰 {label}"
                        
                        jugadores_lista.append(label)
                    
                    jugador_seleccionado = st.selectbox(
                        t("view_details"),
                        jugadores_lista,
                        key=f"select_{key_suffix}"
                    )
                    
                    idx = jugadores_lista.index(jugador_seleccionado)
                    jugador_detalle = df_results.iloc[idx]
                    
                    # ✅ CAMBIO CRÍTICO: Usar tarjeta ADAPTATIVA
                    mostrar_tarjeta_jugador_adaptativa(
                        jugador_detalle=jugador_detalle,
                        molde=row_origen_enriquecido,
                        unique_key=f"{key_suffix}_{idx}"
                    )
                    
                    # ✅ NUEVO: Tabla resumen expandible CON MÁS COLUMNAS
                    with st.expander(f"📋 {t('view_full_table')}"):
                        # Determinar columnas según posición
                        if 'arquero' in posicion_molde.lower() or 'goalkeeper' in posicion_molde.lower():
                            columnas_tabla = [
                                'destino_nombre', 'destino_equipo', 'posicion', 
                                'temporada_similar', 'score_similitud', 'destino_edad',
                                'destino_rating', 'destino_saves', 'destino_saves_pct',
                                'destino_clean_sheets', 'destino_partidos', 'destino_minutos'
                            ]
                        elif 'delantero' in posicion_molde.lower() or 'forward' in posicion_molde.lower():
                            columnas_tabla = [
                                'destino_nombre', 'destino_equipo', 'posicion', 
                                'temporada_similar', 'score_similitud', 'destino_edad',
                                'destino_rating', 'destino_goles', 'destino_xg', 
                                'destino_asistencias', 'destino_xa', 'destino_dribbles',
                                'destino_partidos', 'destino_minutos'
                            ]
                        elif 'medio' in posicion_molde.lower():
                            columnas_tabla = [
                                'destino_nombre', 'destino_equipo', 'posicion', 
                                'temporada_similar', 'score_similitud', 'destino_edad',
                                'destino_rating', 'destino_prog_passes', 'destino_xa',
                                'destino_recoveries', 'destino_dribbles',
                                'destino_partidos', 'destino_minutos'
                            ]
                        else:  # Defensores
                            columnas_tabla = [
                                'destino_nombre', 'destino_equipo', 'posicion', 
                                'temporada_similar', 'score_similitud', 'destino_edad',
                                'destino_rating', 'destino_recoveries', 'destino_aereos',
                                'destino_tackles', 'destino_interceptions',
                                'destino_partidos', 'destino_minutos'
                            ]
                        
                        # Filtrar solo columnas que existen
                        columnas_existentes = [col for col in columnas_tabla if col in df_results.columns]
                        df_display = df_results[columnas_existentes].copy()
                        
                        # Añadir columna de proyección
                        df_display['proyeccion'] = df_results.apply(
                            lambda x: calcular_proyeccion_mejorada(x)['descripcion'],
                            axis=1
                        )
                        
                        st.dataframe(df_display, use_container_width=True, hide_index=True)
                else:
                    st.warning(t("no_results").format(min_score))
                    st.markdown(f"""
                    **{t('search_suggestions')}:**
                    - {t('reduce_min_similarity')}
                    - {t('try_another_season')}
                    - {t('adjust_filters')}
                    """)
            
            # Renderizar cada tab
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
        3. **Aplicá filtros económicos** (opcional): valor máximo, rango de edad, jóvenes promesas
        4. **Explorá** los resultados en las diferentes tabs
        5. **Analizá** los perfiles detallados con radares y métricas **adaptadas a cada posición**
        
        La búsqueda es inteligente y tolerante a errores de tipeo.
        
        #### 🎯 Sistema Adaptativo por Posición
        
        Las métricas que se muestran varían según la posición:
        
        **⚽ Delanteros:**
        - Métricas ofensivas: Goles, xG, xA, Asistencias, Dribbles
        - Radar: xG, xA, Dribbles, Pases Prog., Aéreos, Rating
        
        **🎯 Mediocampistas:**
        - Balance ofensivo/defensivo: Pases Prog., xA, Recuperaciones, Dribbles
        - Radar: Pases Prog., xA, Dribbles, Recuperaciones, xG, Rating
        
        **🛡️ Defensores:**
        - Métricas defensivas: Recuperaciones, Aéreos, Tackles, Intercepciones
        - Radar: Aéreos, Recuperaciones, Tackles, Intercepciones, Pases Prog., Rating
        
        **🧤 Arqueros:**
        - Métricas específicas: Atajadas, % Atajadas, Vallas Invictas, Sweeper, Salidas
        - Radar: Saves, Save %, Clean Sheets, Sweeper, Rating
        
        #### 💎 Badges de Proyección
        Los jugadores con alto potencial de crecimiento aparecen con emojis:
        - 💎 **Prospecto Elite** (sub-21, rating >7.2)
        - 🌟 **Alto Potencial** (sub-21, rating >6.8)
        - ⭐ **Estrella en Ascenso** (sub-23, rating >7.0)
        - 💰 **OPORTUNIDAD** (bajo valor, alto rating)
        """)
    else:
        st.markdown("""
        ### 💡 How to use this tool
        
        1. **Type** the player's name in the sidebar
        2. **Select** the season and desired similarity level
        3. **Apply economic filters** (optional): max value, age range, young prospects
        4. **Explore** the results in different tabs
        5. **Analyze** detailed profiles with radars and metrics **adapted to each position**
        
        The search is smart and typo-tolerant.
        
        #### 🎯 Adaptive System by Position
        
        The metrics shown vary by position:
        
        **⚽ Forwards:**
        - Offensive metrics: Goals, xG, xA, Assists, Dribbles
        - Radar: xG, xA, Dribbles, Prog. Passes, Aerial, Rating
        
        **🎯 Midfielders:**
        - Offensive/defensive balance: Prog. Passes, xA, Recoveries, Dribbles
        - Radar: Prog. Passes, xA, Dribbles, Recoveries, xG, Rating
        
        **🛡️ Defenders:**
        - Defensive metrics: Recoveries, Aerial, Tackles, Interceptions
        - Radar: Aerial, Recoveries, Tackles, Interceptions, Prog. Passes, Rating
        
        **🧤 Goalkeepers:**
        - Specific metrics: Saves, Save %, Clean Sheets, Sweeper, Claims
        - Radar: Saves, Save %, Clean Sheets, Sweeper, Rating
        
        #### 💎 Projection Badges
        Players with high growth potential appear with emojis:
        - 💎 **Elite Prospect** (sub-21, rating >7.2)
        - 🌟 **High Potential** (sub-21, rating >6.8)
        - ⭐ **Rising Star** (sub-23, rating >7.0)
        - 💰 **OPPORTUNITY** (low value, high rating)
        """)

logger.info(f"Buscar page rendered with adaptive metrics (lang: {get_language()}, config: {config_filtros})")