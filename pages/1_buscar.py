import streamlit as st
import sys
from pathlib import Path

from utils.database import get_all_players_index, obtener_similares, obtener_percentiles_molde
from utils.search import buscar_jugadores_fuzzy, format_player_label
from utils.visualization import mostrar_tarjeta_jugador_comparativa
from utils.logger import setup_logger, log_user_action

logger = setup_logger(__name__)

# Configuración
st.set_page_config(page_title="Buscar Jugadores", layout="wide", page_icon="🔍")

st.title("Buscar Jugadores Similares")
st.markdown("Encontrá jugadores con perfiles estadísticos similares usando búsqueda inteligente.")

# Verificar cliente
if 'client' not in st.session_state:
    from utils.database import get_bigquery_client
    st.session_state.client = get_bigquery_client()

client = st.session_state.client

if not client:
    st.error("❌ Error de conexión con BigQuery")
    st.stop()

# Cargar índice de jugadores (solo primera vez)
with st.spinner("🔄 Cargando índice de jugadores..."):
    df_players_index = get_all_players_index(client)

st.sidebar.success(f"✅ Índice cargado: {len(df_players_index):,} jugadores")

# Sidebar - Búsqueda y filtros
st.sidebar.header("🔍 Configuración de Búsqueda")

nombre_buscar = st.sidebar.text_input(
    "Buscar Jugador", 
    placeholder="Ej: Retegui, Borja, Arce",
    help="💡 **Búsqueda inteligente:** Escribí con errores de tipeo, sin tildes o mayúsculas. !No pasa nada!"
)

col_filtro1, col_filtro2 = st.sidebar.columns(2)
with col_filtro1:
    temp_origen_filter = st.selectbox(
        "Temporada Origen",
        options=[2025, 2024, 2023, 2022, 2021],
        index=0
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
                st.sidebar.success(f"Encontrados {len(df_search)} resultados similares (fuzzy match)")
            else:
                st.sidebar.success(f"Encontrados {len(df_search)} resultados exactos")
            
            # Formatear labels
            df_search['label'] = df_search.apply(
                lambda x: format_player_label(x, include_relevancia=True), 
                axis=1
            )
            
            seleccion_label = st.sidebar.selectbox(
                "Seleccioná versión del jugador:", 
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
            
            percentiles_molde = obtener_percentiles_molde(
            player_id=int(id_origen),
            temporada=temp_origen,
            _client=client
        )
            # Agregar percentiles al row_origen para que la tarjeta comparativa los use
            row_origen_enriquecido = row_origen.copy()
            for key, value in percentiles_molde.items():
            row_origen_enriquecido[key] = value

            # Perfil EXPANDIDO del jugador seleccionado
            st.divider()
            st.subheader(f"🎯 Perfil del Molde: {row_origen['player']}")
            
            # Métricas principales (6 columnas)
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
            
            # NUEVO: Stats expandidas del molde
            with st.expander("📊 Ver estadísticas completas del molde", expanded=False):
                col_stat1, col_stat2, col_stat3, col_stat4, col_stat5, col_stat6 = st.columns(6)
                
                with col_stat1:
                    st.metric("⚽ Goles/90", f"{row_origen.get('goals_p90', 0):.2f}")
                with col_stat2:
                    st.metric("🅰️ Asist/90", f"{row_origen.get('assists_p90', 0):.2f}")
                with col_stat3:
                    st.metric("📤 xA/90", f"{row_origen.get('xA_p90', 0):.2f}")
                with col_stat4:
                    st.metric("⬆️ Prog.Pass/90", f"{row_origen.get('prog_passes_p90', 0):.2f}")
                with col_stat5:
                    st.metric("🏃 Dribbles/90", f"{row_origen.get('dribbles_p90', 0):.2f}")
                with col_stat6:
                    st.metric("🔄 Recoveries/90", f"{row_origen.get('recoveries_p90', 0):.2f}")
            
            st.info(f"💡 Buscando jugadores que jueguen estadísticamente como **{row_origen['player']} ({temp_origen})**")
            
            # Tabs de resultados
            st.divider()
            st.subheader("🔎 Jugadores Similares")
            
            # NUEVO: Info sobre el score
            with st.expander("ℹ️ ¿Cómo interpretar el porcentaje de similitud?"):
                st.markdown("""
                El **score de similitud** mide qué tan parecidos son dos perfiles estadísticos en una escala de 0-100%:
                
                | Rango | Interpretación | Qué significa |
                |-------|----------------|---------------|
                | **50-100%** | Muy similar | Perfiles casi idénticos. Jugadores intercambiables estadísticamente. |
                | **40-49%** | Similar | Buen match. Comparten características principales pero con algunas diferencias. |
                | **30-39%** | Moderadamente similar | Match aceptable. Tienen puntos en común pero también diferencias notables. |
                | **20-29%** | Poco similar | Match débil. Solo comparten algunas características generales. |
                | **<20%** | Muy diferente | Perfiles distintos. Probablemente no sean buenas alternativas. |
                
                **Notas importantes:**
                - Scores >50% son raros porque implican perfiles casi idénticos
                - Un score de 40-45% ya es un match muy bueno en la práctica
                - El contexto importa: un 35% en delanteros puede ser mejor que un 45% en defensores
                - Scores bajos no significan que el jugador sea malo, solo que es diferente al molde
                
                **Tip:** Si no encontrás matches >40%, considera buscar jugadores de otras posiciones o ajustar el molde.
                """)
            
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
                    
                    # Mostrar distribución de scores
                    max_score = df_results['score_similitud'].max()
                    avg_score = df_results['score_similitud'].mean()
                    
                    col_info1, col_info2, col_info3 = st.columns(3)
                    with col_info1:
                        st.metric("🎯 Mejor Match", f"{max_score:.1f}%")
                    with col_info2:
                        st.metric("📊 Promedio", f"{avg_score:.1f}%")
                    with col_info3:
                        if max_score >= 45:
                            calidad = "Excelente"
                        elif max_score >= 35:
                            calidad = "Bueno"
                        elif max_score >= 25:
                            calidad = "Aceptable"
                        else:
                            calidad = "Bajo"
                        st.metric("✅ Calidad", calidad)
                    
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
                    
                    # NUEVO: Mostrar tarjeta COMPARATIVA con el molde
                    mostrar_tarjeta_jugador_comparativa(
                        jugador_detalle=jugador_detalle,
                        molde=row_origen_enriquecido,
                        unique_key=f"{key_suffix}_{idx}"
                    )
                    
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
            - Intentá con menos letras (ej: "Mes" en vez de "Messi")
            - Reduce la tolerancia fuzzy (⚙️ Opciones Avanzadas)
            - Cambiá la temporada de origen
            
            **Ejemplos que funcionan:**
            - "Alvares" → encuentra "Álvarez"  
            """)
    
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}", exc_info=True)
        st.error(f"⚠️ Error en la consulta: {e}")

else:
    st.info("Arrancá escribiendo el nombre de un jugador en la barra lateral")
    
    st.markdown("""
    ### 💡 Cómo usar esta herramienta
    
    1. **Escribí** el nombre del jugador en la barra lateral
    2. **Seleccioná** la temporada y nivel de similitud deseado
    3. **Explorá** los resultados en las diferentes tabs
    4. **Analizá** los perfiles detallados con radares y métricas
    
    La búsqueda es inteligente y tolerante a errores de tipeo.
    """)

logger.info("Buscar page rendered successfully")