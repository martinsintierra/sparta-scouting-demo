import streamlit as st
import sys
from pathlib import Path


from utils.database import get_all_players_index, obtener_evolucion_jugador
from utils.search import buscar_jugadores_fuzzy
from utils.visualization import mostrar_timeline_evolucion
from utils.logger import setup_logger

logger = setup_logger(__name__)

st.set_page_config(page_title="Evolución de Jugadores", layout="wide", page_icon="📈")

st.title("📈 Evolución Histórica de Jugadores")
st.markdown("Analiza cómo ha evolucionado el rendimiento de un jugador a través de las temporadas.")

# Verificar cliente
if 'client' not in st.session_state:
    from utils.database import get_bigquery_client
    st.session_state.client = get_bigquery_client()

client = st.session_state.client

if not client:
    st.error("❌ Error de conexión con BigQuery")
    st.stop()

# Cargar índice
with st.spinner("🔄 Cargando índice de jugadores..."):
    df_players_index = get_all_players_index(client)

# Sidebar - Búsqueda
st.sidebar.header("🔍 Buscar Jugador")

nombre_buscar = st.sidebar.text_input(
    "Buscar Jugador", 
    placeholder="Ej: Ronaldo Martinez, Johan Carbonero...",
    help="Busca cualquier jugador para ver su evolución"
)

st.sidebar.info("💡 **Nota:** Se mostrarán todas las temporadas disponibles del jugador, independientemente del filtro inicial.")

# Usamos temporada más reciente para búsqueda inicial (pero luego mostramos todas)
temp_inicial = st.sidebar.selectbox(
    "Buscar en temporada",
    options=[2025, 2024, 2023, 2022, 2021],
    index=0,
    help="Busca al jugador primero en esta temporada. Luego se mostrarán TODAS sus temporadas."
)

umbral_fuzzy = st.sidebar.slider(
    "Tolerancia de búsqueda",
    min_value=50,
    max_value=100,
    value=70,
    step=5
)

if nombre_buscar:
    df_search = buscar_jugadores_fuzzy(
        nombre_buscar, 
        temp_inicial, 
        df_players_index,
        umbral_fuzzy
    )
    
    if not df_search.empty:
        # Formatear labels
        from utils.search import format_player_label
        df_search['label'] = df_search.apply(
            lambda x: format_player_label(x, include_relevancia=True), 
            axis=1
        )
        
        seleccion_label = st.sidebar.selectbox(
            "📋 Selecciona jugador:", 
            df_search['label']
        )
        
        row_origen = df_search[df_search['label'] == seleccion_label].iloc[0]
        player_id = int(row_origen['player_id'])
        nombre_jugador = row_origen['player']
        
        st.divider()
        
        # Información básica
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👤 Jugador", nombre_jugador)
        with col2:
            st.metric("⚽ Equipo Actual", row_origen['equipo_principal'])
        with col3:
            st.metric("📊 Posición", row_origen['posicion'])
        with col4:
            st.metric("⭐ Rating", f"{row_origen['rating_promedio']:.2f}")
        
        st.divider()
        
        # Obtener evolución
        with st.spinner("🔄 Cargando datos históricos..."):
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
            st.markdown("### 🔍 Análisis de Tendencias")
            
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
                    "📊 Evolución del Rating", 
                    f"{rating_final:.2f}",
                    delta=f"{delta_rating:+.2f} vs primera temp"
                )
            
            with col_trend2:
                st.metric(
                    "🎯 Evolución xG/90", 
                    f"{xg_final:.2f}",
                    delta=f"{delta_xg:+.2f} vs primera temp"
                )
            
            with col_trend3:
                st.metric(
                    "🏃 Partidos Totales", 
                    f"{partidos_total}"
                )
            
            # Insights automáticos
            st.markdown("#### 💡 Insights Automáticos")
            
            if delta_rating > 0.5:
                st.success(f"✅ {nombre_jugador} ha **mejorado significativamente** su rating ({delta_rating:+.2f} puntos)")
            elif delta_rating < -0.5:
                st.warning(f"⚠️ {nombre_jugador} ha experimentado una **caída** en su rating ({delta_rating:+.2f} puntos)")
            else:
                st.info(f"ℹ️ {nombre_jugador} ha mantenido un rendimiento **estable** a lo largo de las temporadas")
            
            # Mejor temporada
            mejor_temp = df_evo.loc[df_evo['rating_promedio'].idxmax()]
            st.success(f"🏆 **Mejor temporada:** {int(mejor_temp['temporada_anio'])} con rating {mejor_temp['rating_promedio']:.2f}")
        
        elif df_evo.empty:
            st.warning(f"⚠️ No se encontraron datos históricos para {nombre_jugador}")
            st.info("Verifica que el jugador tenga registros en la base de datos.")
        else:
            st.warning(f"⚠️ No hay suficientes datos históricos para {nombre_jugador}")
            st.info("Se necesitan al menos 2 temporadas con 300+ minutos jugados para visualizar evolución.")
    
    else:
        st.sidebar.warning("❌ No se encontraron jugadores con esos criterios")
        st.sidebar.markdown(f"""
        **💡 Sugerencias:**
        - Intenta con otra temporada de búsqueda
        - Reduce el umbral de tolerancia (⚙️ más abajo)
        - Verifica la ortografía del nombre
        - Prueba con solo el apellido
        
        **Ejemplos que funcionan:**
        - "Messi" ➜ encuentra "Lionel Messi"
        - "Alvares" ➜ encuentra "Julián Álvarez"
        - "CR7" ➜ prueba con "Cristiano" o "Ronaldo"
        """)

else:
    st.info("👈 Comienza buscando un jugador en la barra lateral")
    
    st.markdown("""
    ### 🎯 ¿Para qué sirve el análisis de evolución?
    
    **Esta herramienta te permite:**
    
    - 📈 Identificar **tendencias** de mejora o declive
    - 🔍 Detectar **cambios de rol** (ej: delantero que ahora juega más atrás)
    - 🎯 Evaluar **consistencia** a lo largo del tiempo
    - 🏆 Encontrar **picos de rendimiento** históricos
    - 📊 Comparar diferentes **métricas simultáneamente**
    
    **Casos de uso:**
    - Validar si un jugador joven está en **progresión**
    - Detectar si un veterano está en **declive**
    - Identificar jugadores con **picos de forma** predecibles
    - Analizar impacto de **cambios de equipo** o liga
    
    **Limitaciones:**
    - Solo muestra temporadas con 300+ minutos jugados
    - Cambios pueden deberse al contexto (equipo, lesiones, rol táctico)
    - Métricas no capturan intangibles (liderazgo, mentalidad)
    
    ---
    
    **💡 Consejo:** Usa esta herramienta junto con la búsqueda de similares para identificar jugadores en ascenso que podrían ser buenas oportunidades de mercado.
    """)