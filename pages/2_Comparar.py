import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from utils.database import get_all_players_index, obtener_percentiles_molde
from utils.search import buscar_jugadores_fuzzy, format_player_label
from utils.logger import setup_logger
from utils.i18n import language_selector, t, get_language
from utils.filters import (
    render_economic_filters_sidebar,
    aplicar_filtros_economicos,
    calcular_proyeccion_mejorada,
    mostrar_badge_proyeccion
)
from utils.insights_adaptativos import generar_insights_comparacion


logger = setup_logger(__name__)

st.set_page_config(page_title=t("compare_title"), layout="wide", page_icon="⚖️")

# Selector de idioma
language_selector()

st.title(t("compare_title"))
st.markdown(t("compare_subtitle"))

# Verificar cliente
if 'client' not in st.session_state:
    from utils.database import get_bigquery_client
    st.session_state.client = get_bigquery_client()

client = st.session_state.client

if not client:
    st.error(f"❌ {t('connection_error')} BigQuery")
    st.stop()

# Cargar índice
with st.spinner(f"🔄 {t('loading')}..."):
    df_players_index = get_all_players_index(client)

st.sidebar.success(f"✅ {len(df_players_index):,} {t('unique_players').lower()}")

st.sidebar.divider()

config_filtros = render_economic_filters_sidebar(
    default_max_value=50,
    default_age_range=(16, 40),
    default_young_prospects=False,
    expanded=False
)

# Sidebar - Configuración
st.sidebar.header(t("select_players"))

num_jugadores = st.sidebar.radio(
    t("num_players"),
    options=[2, 3, 4],
    index=0,
    help=t("num_players_help")
)

st.sidebar.divider()

# Almacenar jugadores seleccionados
jugadores_seleccionados = []

# Búsqueda de cada jugador
for i in range(num_jugadores):
    st.sidebar.markdown(f"### {t('player_num').format(i+1)}")
    
    nombre = st.sidebar.text_input(
        t("search_player_num").format(i+1),
        placeholder="Ej: Retegui, Borja..." if get_language() == 'es' else "e.g., Retegui, Borja...",
        key=f"buscar_{i}"
    )
    
    if nombre:
        temp = st.sidebar.selectbox(
            t("season_player_num").format(i+1),
            options=[2025, 2024, 2023, 2022, 2021],
            index=0,
            key=f"temp_{i}"
        )
        
        df_search = buscar_jugadores_fuzzy(nombre, temp, df_players_index, 70)

        if not df_search.empty:
            df_search = aplicar_filtros_economicos(
                df_search,
                config_filtros,
                prefijo_columnas=""
            )
        
        if not df_search.empty:
            df_search['label'] = df_search.apply(
                lambda x: format_player_label(x, include_relevancia=True), 
                axis=1
            )
            
            seleccion = st.sidebar.selectbox(
                t("select_version_num").format(i+1),
                df_search['label'],
                key=f"select_{i}"
            )
            
            row = df_search[df_search['label'] == seleccion].iloc[0]
            
            # Obtener percentiles
            percentiles = obtener_percentiles_molde(
                player_id=int(row['player_id']),
                temporada=int(row['temporada_anio']),
                _client=client
            )
            
            jugador_data = {
                'nombre': row['player'],
                'equipo': row['equipo_principal'],
                'posicion': row['posicion'],
                'temporada': int(row['temporada_anio']),
                'rating': row['rating_promedio'],
                'xG': row['xG_p90'],
                'goals': row['goals_p90'],
                'partidos': int(row['partidos_jugados']),
                'edad': row.get('edad_promedio', 99), 
                'valor': row.get('valor_mercado', 0),
                'percentiles': percentiles
            }
            
            jugadores_seleccionados.append(jugador_data)
        else:
            st.sidebar.warning(f"❌ {t('not_found')} {i+1}")
    
    st.sidebar.divider()

# Mostrar comparación si hay al menos 2 jugadores
if len(jugadores_seleccionados) >= 2:
    st.success(t("comparing_players").format(len(jugadores_seleccionados)))
    
    # Tabla comparativa
    st.markdown(f"### {t('comparative_table')}")
    
    # Preparar datos para tabla
    tabla_data = []
    for j in jugadores_seleccionados:
        if get_language() == 'es':
            tabla_data.append({
                'Jugador': j['nombre'],
                'Equipo': j['equipo'],
                'Posición': j['posicion'],
                'Temporada': j['temporada'],
                '⭐ Rating': f"{j['rating']:.2f}",
                '⚽ Goles/90': f"{j['goals']:.2f}",
                '🎯 xG/90': f"{j['xG']:.2f}",
                '🏃 Partidos': j['partidos']
            })
        else:
            tabla_data.append({
                'Player': j['nombre'],
                'Team': j['equipo'],
                'Position': j['posicion'],
                'Season': j['temporada'],
                '⭐ Rating': f"{j['rating']:.2f}",
                '⚽ Goals/90': f"{j['goals']:.2f}",
                '🎯 xG/90': f"{j['xG']:.2f}",
                '🏃 Matches': j['partidos']

            })
            
    for jugador in jugadores_seleccionados:
        proyeccion = calcular_proyeccion_mejorada(
            pd.Series({
                'destino_edad': jugador.get('edad', 99),
                'destino_rating': jugador['rating'],
                'destino_valor': jugador.get('valor', 0),
                'destino_partidos': jugador['partidos']
            })
        )
        
    if proyeccion['delta_proyectado_pct'] > 10:
        st.info(f"{proyeccion['emoji']} {jugador['nombre']}: {proyeccion['descripcion']}")
    
    df_tabla = pd.DataFrame(tabla_data)
    st.dataframe(df_tabla, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Radar comparativo
    st.markdown(f"### 🎯 {t('comparative_radar')}")
    
    if get_language() == 'es':
        categories = ['xG', 'xA', 'Pases Prog.', 'Dribbles', 'Recuperaciones', 'Aéreos', 'Rating']
    else:
        categories = ['xG', 'xA', 'Prog. Passes', 'Dribbles', 'Recoveries', 'Aerial', 'Rating']
    
    fig = go.Figure()
    
    colores = ['#667eea', '#f59e0b', '#10b981', '#ef4444']
    
    for idx, jugador in enumerate(jugadores_seleccionados):
        p = jugador['percentiles']
        values = [
            p.get('pct_xG', 0.5) * 100,
            p.get('pct_xA', 0.5) * 100,
            p.get('pct_prog_passes', 0.5) * 100,
            p.get('pct_dribbles', 0.5) * 100,
            p.get('pct_recoveries', 0.5) * 100,
            p.get('pct_aerial', 0.5) * 100,
            p.get('pct_rating', 0.5) * 100
        ]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=f"{jugador['nombre']} ({jugador['temporada']})",
            line_color=colores[idx % len(colores)],
            fillcolor=f"rgba{tuple(list(int(colores[idx % len(colores)][i:i+2], 16) for i in (1, 3, 5)) + [0.2])}"
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Análisis de fortalezas
    st.markdown(f"### 💪 {t('strengths_analysis')}")
    
    cols = st.columns(len(jugadores_seleccionados))
    
    for idx, (col, jugador) in enumerate(zip(cols, jugadores_seleccionados)):
        with col:
            st.markdown(f"#### {jugador['nombre']}")
            
            p = jugador['percentiles']
            
            if get_language() == 'es':
                metricas = {
                    'xG': p.get('pct_xG', 0.5) * 100,
                    'xA': p.get('pct_xA', 0.5) * 100,
                    'Pases Prog.': p.get('pct_prog_passes', 0.5) * 100,
                    'Dribbles': p.get('pct_dribbles', 0.5) * 100,
                    'Recuperaciones': p.get('pct_recoveries', 0.5) * 100,
                    'Aéreos': p.get('pct_aerial', 0.5) * 100
                }
            else:
                metricas = {
                    'xG': p.get('pct_xG', 0.5) * 100,
                    'xA': p.get('pct_xA', 0.5) * 100,
                    'Prog. Passes': p.get('pct_prog_passes', 0.5) * 100,
                    'Dribbles': p.get('pct_dribbles', 0.5) * 100,
                    'Recoveries': p.get('pct_recoveries', 0.5) * 100,
                    'Aerial': p.get('pct_aerial', 0.5) * 100
                }
            
            # Top 3 fortalezas
            top_3 = sorted(metricas.items(), key=lambda x: x[1], reverse=True)[:3]
            
            st.success(f"**{t('top_3_strengths')}:**")
            for metrica, valor in top_3:
                if get_language() == 'es':
                    st.write(f"- {metrica}: Percentil {valor:.0f}")
                else:
                    st.write(f"- {metrica}: Percentile {valor:.0f}")
            
            # Bottom 3 debilidades
            bottom_3 = sorted(metricas.items(), key=lambda x: x[1])[:3]
            
            st.warning(f"**{t('improvement_areas')}:**")
            for metrica, valor in bottom_3:
                if get_language() == 'es':
                    st.write(f"- {metrica}: Percentil {valor:.0f}")
                else:
                    st.write(f"- {metrica}: Percentile {valor:.0f}")
    
    st.divider()
    
    # Insights automáticos
    st.markdown(f"### 💡 {t('automatic_insights')}")
    
    jugadores_data = []
    for j in jugadores_seleccionados:
        p = j['percentiles']
        jugadores_data.append({
            'nombre': j['nombre'],
            'posicion': j['posicion'],
            'rating': j['rating'],
            'goals': j.get('goals', 0),
            'xG': j['xG'],
            'xA': j.get('xA', 0),
            'prog_passes': j.get('prog_passes', 0),
            'recoveries': j.get('recoveries', 0),
            'pct_xG': p.get('pct_xG', 0.5),
            'pct_xA': p.get('pct_xA', 0.5),
            'pct_prog_passes': p.get('pct_prog_passes', 0.5),
            'pct_recoveries': p.get('pct_recoveries', 0.5)
        })

    # Generar insights
    insights = generar_insights_comparacion(jugadores_data)

    # Mostrar insights
    for insight in insights:
        st.success(insight)

else:
    st.info(t("search_2_players"))
    
    # Casos de uso según idioma
    if get_language() == 'es':
        st.markdown("""
        ### 💡 Cómo usar esta herramienta
        
        1. **Seleccioná** el número de jugadores a comparar (2-4)
        2. **Buscá** cada jugador usando la barra lateral
        3. **Elegí** la temporada específica de cada uno
        4. **Analizá** la tabla comparativa y el radar
        
        **Casos de uso:**
        - Comparar candidatos para un mismo puesto
        - Evaluar evolución del mismo jugador en diferentes temporadas
        - Analizar diferentes perfiles para una posición
        - Identificar fortalezas complementarias en un plantel
        """)
    else:
        st.markdown("""
        ### 💡 How to use this tool
        
        1. **Select** the number of players to compare (2-4)
        2. **Search** for each player using the sidebar
        3. **Choose** the specific season for each one
        4. **Analyze** the comparative table and radar
        
        **Use cases:**
        - Compare candidates for the same position
        - Evaluate same player's evolution across seasons
        - Analyze different profiles for a position
        - Identify complementary strengths in a squad
        """)

logger.info(f"Comparar page rendered (lang: {get_language()})")