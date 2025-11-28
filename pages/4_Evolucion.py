import streamlit as st

from utils.database import get_all_players_index, obtener_evolucion_jugador
from utils.search import normalizar_texto
from utils.visualization import mostrar_timeline_evolucion
from utils.logger import setup_logger
from utils.i18n import language_selector, t, get_language

logger = setup_logger(__name__)

st.set_page_config(page_title=t("evolution_title"), layout="wide", page_icon="📈")

# Selector de idioma
language_selector()

st.title(t("evolution_title"))
st.markdown(t("evolution_subtitle"))

# Verificar cliente
if 'client' not in st.session_state:
    from utils.database import get_bigquery_client
    st.session_state.client = get_bigquery_client()

client = st.session_state.client

if not client:
    st.error(f"❌ {t('connection_error')} BigQuery")
    st.stop()

# Cargar índice COMPLETO (todas las temporadas)
with st.spinner(f"{t('loading')}..."):
    df_players_index = get_all_players_index(client)

# Sidebar - Búsqueda SIN filtro de temporada
st.sidebar.header(t("search_player"))

nombre_buscar = st.sidebar.text_input(
    t("player_name"), 
    placeholder="Ej: Valentin Gomez, Retegui..." if get_language() == 'es' else "e.g., Valentin Gomez, Retegui...",
    help=t("evolution_help")
)

umbral_fuzzy = st.sidebar.slider(
    t("search_tolerance"),
    min_value=50,
    max_value=100,
    value=70,
    step=5,
    help=t("fuzzy_help")
)

if nombre_buscar:
    from thefuzz import process, fuzz
    
    # Búsqueda fuzzy GLOBAL (sin filtro de temporada)
    nombre_normalizado = normalizar_texto(nombre_buscar).upper()
    
    # Búsqueda exacta primero
    df_search = df_players_index[
        df_players_index['player_normalizado'].str.upper().str.contains(nombre_normalizado, na=False) |
        df_players_index['player'].str.upper().str.contains(nombre_buscar.upper(), na=False)
    ].copy()
    
    # Si no hay exactos, usar fuzzy
    if df_search.empty:
        nombres_normalizados = df_players_index['player_normalizado'].tolist()
        matches = process.extract(
            nombre_normalizado, 
            nombres_normalizados,
            scorer=fuzz.partial_ratio,
            limit=30
        )
        
        # Manejar formato nuevo de thefuzz
        if matches and len(matches[0]) == 2:
            matches_validos = []
            for match, score in matches:
                if score >= umbral_fuzzy:
                    idx = nombres_normalizados.index(match) if match in nombres_normalizados else None
                    if idx is not None:
                        matches_validos.append((match, score, idx))
        else:
            matches_validos = [(match, score, idx) for match, score, idx in matches if score >= umbral_fuzzy]
        
        if matches_validos:
            indices = [idx for _, _, idx in matches_validos]
            scores = [score for _, score, _ in matches_validos]
            df_search = df_players_index.iloc[indices].copy()
            df_search['relevancia'] = scores
    
    if not df_search.empty:
        # Agrupar por player_id para eliminar duplicados
        df_search_unique = df_search.sort_values('temporada_anio', ascending=False).groupby('player_id').first().reset_index()
        
        # Formatear labels con club ACTUAL
        df_search_unique['label'] = df_search_unique.apply(
            lambda x: f"{x['player']} | {x['equipo_principal']} | {x['posicion']} | ⭐{x['rating_promedio']:.1f}",
            axis=1
        )
        
        st.sidebar.success(t("results_found").format(len(df_search_unique)))
        
        seleccion_label = st.sidebar.selectbox(
            f"📋 {t('select_player_list')}", 
            df_search_unique['label']
        )
        
        row_origen = df_search_unique[df_search_unique['label'] == seleccion_label].iloc[0]
        player_id = int(row_origen['player_id'])
        nombre_jugador = row_origen['player']
        
        st.divider()
        
        # Información básica
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(f"👤 {t('player_name') if get_language() == 'en' else 'Jugador'}", nombre_jugador)
        with col2:
            st.metric(f"⚽ {t('current_club')}", row_origen['equipo_principal'])
        with col3:
            st.metric(f"📊 {t('position')}", row_origen['posicion'])
        with col4:
            st.metric(f"⭐ {t('current_rating')}", f"{row_origen['rating_promedio']:.2f}")
        
        st.divider()
        
        # Obtener evolución
        with st.spinner(f"🔄 {t('loading_history')}..."):
            df_evo = obtener_evolucion_jugador(player_id, client)
        
        if not df_evo.empty and len(df_evo) >= 2:
            # Mostrar timeline
            mostrar_timeline_evolucion(
                player_id=player_id,
                nombre_jugador=nombre_jugador,
                df_evo=df_evo
            )
            
            # Análisis adicional
            st.divider()
            st.markdown(f"### 🔍 {t('trends_analysis')}")
            
            col_trend1, col_trend2, col_trend3 = st.columns(3)
            
            # Calcular tendencias
            rating_inicial = df_evo.iloc[0]['rating_promedio']
            rating_final = df_evo.iloc[-1]['rating_promedio']
            delta_rating = rating_final - rating_inicial
            
            xg_inicial = df_evo.iloc[0]['xG_p90']
            xg_final = df_evo.iloc[-1]['xG_p90']
            delta_xg = xg_final - xg_inicial
            
            partidos_total = df_evo['partidos_jugados'].sum()
            
            with col_trend1:
                st.metric(
                    f"📊 {t('rating_evolution')}", 
                    f"{rating_final:.2f}",
                    delta=f"{delta_rating:+.2f} {t('vs_first_season')}"
                )
            
            with col_trend2:
                st.metric(
                    f"🎯 {t('xg_evolution')}", 
                    f"{xg_final:.2f}",
                    delta=f"{delta_xg:+.2f} {t('vs_first_season')}"
                )
            
            with col_trend3:
                st.metric(
                    f"🏃 {t('total_matches')}", 
                    f"{partidos_total}"
                )
            
            # Insights automáticos
            st.markdown(f"#### 💡 {t('automatic_insights')}")
            
            if delta_rating > 0.5:
                st.success(t("improved_significantly").format(nombre_jugador, delta_rating))
            elif delta_rating < -0.5:
                st.warning(t("declined_rating").format(nombre_jugador, delta_rating))
            else:
                st.info(t("stable_performance").format(nombre_jugador))
            
            # Mejor temporada
            mejor_temp = df_evo.loc[df_evo['rating_promedio'].idxmax()]
            st.success(f"🏆 {t('best_season')}: {int(mejor_temp['temporada_anio'])} {t('with_rating')} {mejor_temp['rating_promedio']:.2f}")
        
        elif df_evo.empty:
            st.warning(t("no_historical_data").format(nombre_jugador))
            if get_language() == 'es':
                st.info("Verifica que el jugador tenga registros en la base de datos.")
            else:
                st.info("Verify that the player has records in the database.")
        else:
            st.warning(t("insufficient_seasons").format(nombre_jugador))
            st.info(t("need_2_seasons"))
    
    else:
        st.sidebar.warning(f"❌ {t('not_found')}")
        if get_language() == 'es':
            st.sidebar.markdown("""
            **💡 Sugerencias:**
            - Reduce el umbral de tolerancia
            - Verifica la ortografía del nombre
            - Prueba con solo el apellido
            
            **Ejemplos que funcionan:**
            - "Alvares" encuentra "Julián Álvarez"
            - "Retegui" encuentra todas las temporadas de Retegui
            """)
        else:
            st.sidebar.markdown("""
            **💡 Suggestions:**
            - Reduce the tolerance threshold
            - Check the name spelling
            - Try with just the last name
            
            **Examples that work:**
            - "Alvares" finds "Julián Álvarez"
            - "Retegui" finds all Retegui's seasons
            """)

else:
    st.info(t("start_searching"))
    
    # Explicación según idioma
    if get_language() == 'es':
        st.markdown("""
        ### 🎯 ¿Para qué sirve el análisis de evolución?
        
        Esta herramienta te permite:
        
        - 📈 Identificar tendencias de mejora o declive
        - 🔍 Detectar cambios de rol (ej: delantero que ahora juega más atrás)
        - 🎯 Evaluar consistencia a lo largo del tiempo
        - 🏆 Encontrar picos de rendimiento históricos
        - 📊 Comparar diferentes métricas simultáneamente
        
        **Casos de uso:**
        - Validar si un jugador joven está en progresión
        - Detectar si un veterano está en declive
        - Identificar jugadores con picos de forma predecibles
        - Analizar impacto de cambios de equipo o liga
        
        **Limitaciones:**
        - Solo muestra temporadas con 300+ minutos jugados
        - Cambios pueden deberse al contexto (equipo, lesiones, rol táctico)
        - Métricas no capturan intangibles (liderazgo, mentalidad)
        """)
    else:
        st.markdown("""
        ### 🎯 What is evolution analysis for?
        
        This tool allows you to:
        
        - 📈 Identify improvement or decline trends
        - 🔍 Detect role changes (e.g., striker now playing deeper)
        - 🎯 Evaluate consistency over time
        - 🏆 Find historical performance peaks
        - 📊 Compare different metrics simultaneously
        
        **Use cases:**
        - Validate if a young player is progressing
        - Detect if a veteran is declining
        - Identify players with predictable form peaks
        - Analyze impact of team or league changes
        
        **Limitations:**
        - Only shows seasons with 300+ minutes played
        - Changes may be due to context (team, injuries, tactical role)
        - Metrics don't capture intangibles (leadership, mentality)
        """)

logger.info(f"Evolution page rendered (lang: {get_language()})")