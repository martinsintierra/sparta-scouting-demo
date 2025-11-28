import streamlit as st
import sys
from pathlib import Path
import plotly.graph_objects as go
import pandas as pd

from utils.database import get_all_players_index, obtener_percentiles_molde
from utils.search import buscar_jugadores_fuzzy, format_player_label
from utils.logger import setup_logger

logger = setup_logger(__name__)

st.set_page_config(page_title="Comparar Jugadores", layout="wide", page_icon="⚖️")

st.title("Comparar Jugadores")
st.markdown("Compará hasta 4 jugadores lado a lado para identificar fortalezas y debilidades.")

# Verificar cliente
if 'client' not in st.session_state:
    from utils.database import get_bigquery_client
    st.session_state.client = get_bigquery_client()

client = st.session_state.client

if not client:
    st.error("❌ Error de conexión con BigQuery")
    st.stop()

# Cargar índice
with st.spinner("📄 Cargando índice de jugadores..."):
    df_players_index = get_all_players_index(client)

st.sidebar.success(f"✅ Índice cargado: {len(df_players_index):,} jugadores")

# Sidebar - Configuración
st.sidebar.header("Seleccionar Jugadores")

num_jugadores = st.sidebar.radio(
    "Número de jugadores a comparar",
    options=[2, 3, 4],
    index=0,
    help="Seleccioná cuántos jugadores querés comparar"
)

st.sidebar.divider()

# Almacenar jugadores seleccionados
if 'jugadores_comparacion' not in st.session_state:
    st.session_state.jugadores_comparacion = []

jugadores_seleccionados = []

# Búsqueda de cada jugador
for i in range(num_jugadores):
    st.sidebar.markdown(f"### Jugador {i+1}")
    
    nombre = st.sidebar.text_input(
        f"Buscar jugador {i+1}",
        placeholder="Ej: Retegui, Borja...",
        key=f"buscar_{i}"
    )
    
    if nombre:
        temp = st.sidebar.selectbox(
            f"Temporada jugador {i+1}",
            options=[2025, 2024, 2023, 2022, 2021],
            index=0,
            key=f"temp_{i}"
        )
        
        df_search = buscar_jugadores_fuzzy(nombre, temp, df_players_index, 70)
        
        if not df_search.empty:
            df_search['label'] = df_search.apply(
                lambda x: format_player_label(x, include_relevancia=True), 
                axis=1
            )
            
            seleccion = st.sidebar.selectbox(
                f"Seleccionar versión {i+1}",
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
                'percentiles': percentiles
            }
            
            jugadores_seleccionados.append(jugador_data)
        else:
            st.sidebar.warning(f"❌ No se encontró jugador {i+1}")
    
    st.sidebar.divider()

# Mostrar comparación si hay al menos 2 jugadores
if len(jugadores_seleccionados) >= 2:
    st.success(f"✅ Comparando {len(jugadores_seleccionados)} jugadores")
    
    # Tabla comparativa
    st.markdown("### Tabla Comparativa")
    
    # Preparar datos para tabla
    tabla_data = []
    for j in jugadores_seleccionados:
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
    
    df_tabla = pd.DataFrame(tabla_data)
    st.dataframe(df_tabla, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Radar comparativo
    st.markdown("### 🎯 Radar Comparativo (Percentiles)")
    
    categories = ['xG', 'xA', 'Pases Prog.', 'Dribbles', 'Recuperaciones', 'Aéreos', 'Rating']
    
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
    st.markdown("### 💪 Análisis de Fortalezas Relativas")
    
    cols = st.columns(len(jugadores_seleccionados))
    
    for idx, (col, jugador) in enumerate(zip(cols, jugadores_seleccionados)):
        with col:
            st.markdown(f"#### {jugador['nombre']}")
            
            p = jugador['percentiles']
            metricas = {
                'xG': p.get('pct_xG', 0.5) * 100,
                'xA': p.get('pct_xA', 0.5) * 100,
                'Pases Prog.': p.get('pct_prog_passes', 0.5) * 100,
                'Dribbles': p.get('pct_dribbles', 0.5) * 100,
                'Recuperaciones': p.get('pct_recoveries', 0.5) * 100,
                'Aéreos': p.get('pct_aerial', 0.5) * 100
            }
            
            # Top 3 fortalezas
            top_3 = sorted(metricas.items(), key=lambda x: x[1], reverse=True)[:3]
            
            st.success("**Top 3 Fortalezas:**")
            for metrica, valor in top_3:
                st.write(f"- {metrica}: Percentil {valor:.0f}")
            
            # Bottom 3 debilidades
            bottom_3 = sorted(metricas.items(), key=lambda x: x[1])[:3]
            
            st.warning("**Áreas de Mejora:**")
            for metrica, valor in bottom_3:
                st.write(f"- {metrica}: Percentil {valor:.0f}")
    
    st.divider()
    
    # Insights automáticos
    st.markdown("### 💡 Insights Automáticos")
    
    # Jugador con mejor rating
    mejor_rating = max(jugadores_seleccionados, key=lambda x: x['rating'])
    st.info(f"🏆 **Mejor Rating:** {mejor_rating['nombre']} con {mejor_rating['rating']:.2f}")
    
    # Jugador más goleador
    mejor_goleador = max(jugadores_seleccionados, key=lambda x: x['goals'])
    st.info(f"⚽ **Más Goleador:** {mejor_goleador['nombre']} con {mejor_goleador['goals']:.2f} goles/90")
    
    # Jugador con mejor xG
    mejor_xg = max(jugadores_seleccionados, key=lambda x: x['xG'])
    st.info(f"🎯 **Mejor xG:** {mejor_xg['nombre']} con {mejor_xg['xG']:.2f} xG/90")

else:
    st.info("👈 Buscá al menos 2 jugadores en la barra lateral para comenzar la comparación")
    
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

logger.info("Comparar page rendered successfully")