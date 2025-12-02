"""
Sistema de Visualización Adaptativo por Posición
Muestra métricas relevantes según el rol del jugador
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Tuple
from utils.i18n import t, get_language


def get_position_metrics(posicion: str) -> Dict[str, List[Tuple[str, str, str]]]:
    """
    Retorna métricas relevantes por posición
    
    Returns:
        Dict con:
        - 'primary': Métricas principales (6 columnas)
        - 'radar': Métricas para radar chart (6-7 dimensiones)
        - 'labels': Labels traducidos
    """
    lang = get_language()
    
    # Mapeo de posiciones normalizadas
    pos_normalizada = posicion.lower()
    

    if 'arquero' in pos_normalizada or 'goalkeeper' in pos_normalizada or 'portero' in pos_normalizada or 'goleiro' in pos_normalizada:
        return {
            'primary': [
                ('destino_rating', '⭐ Rating', 'rating_promedio'),
                ('destino_saves', '🧤 Atajadas', 'saves_p90'),
                ('destino_saves_pct', '📊 % Ataj.', 'saves_pct'),
                ('destino_clean_sheets', '🛡️ Valla Inv.', 'clean_sheets_pct'),
                ('destino_sweeper', '🏃 Sweeper', 'sweeper_p90'),
                ('destino_claims', '✊ Salidas', 'claims_p90')
            ],
            'radar': [
                ('pct_saves', 'Saves' if lang == 'en' else 'Atajadas'),
                ('pct_saves_pct', 'Save %' if lang == 'en' else '% Ataj.'),
                ('pct_clean_sheets', 'Clean Sheets' if lang == 'en' else 'Vallas Inv.'),
                ('pct_sweeper', 'Sweeper' if lang == 'en' else 'Sweeper'),
                ('pct_rating', 'Rating' if lang == 'en' else 'Rating')
            ]
        }

    elif 'delantero' in pos_normalizada or 'forward' in pos_normalizada:
        return {
            'primary': [
                ('destino_rating', '⭐ Rating', 'rating_promedio'),
                ('destino_goles', '⚽ Goles', 'goals_p90'),
                ('destino_xg', '🎯 xG', 'xG_p90'),
                ('destino_asistencias', '🅰️ Asist.', 'assists_p90'),
                ('destino_xa', '📤 xA', 'xA_p90'),
                ('destino_dribbles', '🎪 Dribbles', 'dribbles_p90')
            ],
            'radar': [
                ('pct_xG', 'xG' if lang == 'en' else 'xG'),
                ('pct_xA', 'xA' if lang == 'en' else 'xA'),
                ('pct_dribbles', 'Dribbles' if lang == 'en' else 'Dribbles'),
                ('pct_prog_passes', 'Prog. Pass' if lang == 'en' else 'Pases Prog.'),
                ('pct_aerial', 'Aerial' if lang == 'en' else 'Aéreos'),
                ('pct_rating', 'Rating' if lang == 'en' else 'Rating')
            ]
        }
    
    elif 'mediocampista' in pos_normalizada or 'midfielder' in pos_normalizada or 'medio' in pos_normalizada:
        return {
            'primary': [
                ('destino_rating', '⭐ Rating', 'rating_promedio'),
                ('destino_prog_passes', '⬆️ Prog. Pass', 'prog_passes_p90'),
                ('destino_xa', '📤 xA', 'xA_p90'),
                ('destino_asistencias', '🅰️ Asist.', 'assists_p90'),
                ('destino_recoveries', '🔄 Recup.', 'recoveries_p90'),
                ('destino_dribbles', '🎪 Dribbles', 'dribbles_p90')
            ],
            'radar': [
                ('pct_prog_passes', 'Prog. Pass' if lang == 'en' else 'Pases Prog.'),
                ('pct_xA', 'xA' if lang == 'en' else 'xA'),
                ('pct_dribbles', 'Dribbles' if lang == 'en' else 'Dribbles'),
                ('pct_recoveries', 'Recoveries' if lang == 'en' else 'Recuperaciones'),
                ('pct_xG', 'xG' if lang == 'en' else 'xG'),
                ('pct_rating', 'Rating' if lang == 'en' else 'Rating')
            ]
        }
    
    elif 'defensor' in pos_normalizada or 'defender' in pos_normalizada or 'defensa' in pos_normalizada:
        return {
            'primary': [
                ('destino_rating', '⭐ Rating', 'rating_promedio'),
                ('destino_recoveries', '🔄 Recup.', 'recoveries_p90'),
                ('destino_aereos', '✈️ Aéreos', 'aerial_won_p90'),
                ('destino_prog_passes', '⬆️ Prog. Pass', 'prog_passes_p90'),
                ('destino_tackles', '🛡️ Tackles', 'tackles_p90'),
                ('destino_interceptions', '🚧 Interc.', 'interceptions_p90')
            ],
            'radar': [
                ('pct_aerial', 'Aerial' if lang == 'en' else 'Aéreos'),
                ('pct_recoveries', 'Recoveries' if lang == 'en' else 'Recuperaciones'),
                ('pct_tackles', 'Tackles' if lang == 'en' else 'Tackles'),
                ('pct_interceptions', 'Interceptions' if lang == 'en' else 'Intercepciones'),
                ('pct_prog_passes', 'Prog. Pass' if lang == 'en' else 'Pases Prog.'),
                ('pct_rating', 'Rating' if lang == 'en' else 'Rating')
            ]
        }
    
    else:
        # Fallback genérico (arquero, lateral, etc.)
        return {
            'primary': [
                ('destino_rating', '⭐ Rating', 'rating_promedio'),
                ('destino_recoveries', '🔄 Recup.', 'recoveries_p90'),
                ('destino_prog_passes', '⬆️ Prog. Pass', 'prog_passes_p90'),
                ('destino_aereos', '✈️ Aéreos', 'aerial_won_p90'),
                ('destino_xa', '📤 xA', 'xA_p90'),
                ('destino_xg', '🎯 xG', 'xG_p90')
            ],
            'radar': [
                ('pct_rating', 'Rating' if lang == 'en' else 'Rating'),
                ('pct_prog_passes', 'Prog. Pass' if lang == 'en' else 'Pases Prog.'),
                ('pct_recoveries', 'Recoveries' if lang == 'en' else 'Recuperaciones'),
                ('pct_aerial', 'Aerial' if lang == 'en' else 'Aéreos'),
                ('pct_xA', 'xA' if lang == 'en' else 'xA'),
                ('pct_xG', 'xG' if lang == 'en' else 'xG')
            ]
        }


def mostrar_tarjeta_jugador_adaptativa(jugador_detalle: pd.Series, molde: pd.Series, unique_key: str):
    """
    Renderiza tarjeta con métricas ADAPTADAS a la posición del jugador
    
    Args:
        jugador_detalle: Serie con datos del jugador similar
        molde: Serie con datos del jugador molde
        unique_key: Clave única para widgets
    """
    from utils.visualization import calcular_proyeccion_valor
    
    with st.container():
        st.markdown("---")
        
        # Calcular proyección
        proyeccion = calcular_proyeccion_valor(jugador_detalle)
        
        # ========== HEADER ==========
        col_header1, col_header2, col_header3 = st.columns([3, 1, 1])
        
        with col_header1:
            nombre_display = f"{proyeccion['emoji']} {jugador_detalle['destino_nombre']}" if proyeccion['emoji'] else jugador_detalle['destino_nombre']
            st.markdown(f"### {nombre_display}")
            st.caption(f"{jugador_detalle['destino_equipo']} | {jugador_detalle['posicion']}")
        
        with col_header2:
            st.markdown(f"""
            <div style='
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                padding: 10px;
                border-radius: 10px;
                text-align: center;
                color: white;
                font-weight: bold;
                box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3);
            '>
                {jugador_detalle['score_similitud']:.1f}% Match
            </div>
            """, unsafe_allow_html=True)
        
        with col_header3:
            st.caption(f"📅 Temp. {int(jugador_detalle['temporada_similar'])}")
        
        # ========== BADGE DE PROYECCIÓN ==========
        if proyeccion['delta_proyectado_pct'] > 10:
            lang = get_language()
            if lang == 'es':
                texto_proyeccion = f"Proyección: +{proyeccion['delta_proyectado_pct']:.0f}% valor en 1 año"
                if proyeccion['categoria'] == 'high_potential':
                    categoria_texto = "Alto Potencial"
                elif proyeccion['categoria'] == 'rising_star':
                    categoria_texto = "Estrella en Ascenso"
                else:
                    categoria_texto = "Emergente"
            else:
                texto_proyeccion = f"Projection: +{proyeccion['delta_proyectado_pct']:.0f}% value in 1 year"
                if proyeccion['categoria'] == 'high_potential':
                    categoria_texto = "High Potential"
                elif proyeccion['categoria'] == 'rising_star':
                    categoria_texto = "Rising Star"
                else:
                    categoria_texto = "Emerging"
            
            st.markdown(f"""
            <div style='
                background: {proyeccion['color']};
                padding: 12px 20px;
                border-radius: 8px;
                text-align: center;
                color: white;
                font-weight: 600;
                font-size: 15px;
                margin-bottom: 15px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.15);
            '>
                {proyeccion['emoji']} {categoria_texto} | {texto_proyeccion}
            </div>
            """, unsafe_allow_html=True)
        
        # ========== MÉTRICAS GENERALES ==========
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.metric("🎂 Edad", f"{int(jugador_detalle['destino_edad'])}")
        with col2:
            altura = jugador_detalle.get('destino_altura')
            st.metric("📏 Altura", f"{altura:.0f} cm" if pd.notnull(altura) else "N/A")
        with col3:
            pie = jugador_detalle.get('destino_pie')
            st.metric("🦶 Pie", pie if pd.notnull(pie) else "N/A")
        with col4:
            st.metric("🌍 País", jugador_detalle.get('destino_nacionalidad', 'N/A'))
        with col5:
            valor = jugador_detalle.get('destino_valor')
            if pd.notnull(valor) and valor > 0:
                st.metric("💰 Valor", f"€{valor/1000:.0f}K")
            else:
                st.metric("💰 Valor", "N/A")
        with col6:
            contrato = jugador_detalle.get('destino_contrato')
            st.metric("📄 Contrato", str(contrato)[:4] if pd.notnull(contrato) else "N/A")
        
        # ========== STATS ADAPTATIVAS POR POSICIÓN ==========
        posicion = jugador_detalle['posicion']
        config = get_position_metrics(posicion)
        
        lang = get_language()
        if lang == 'es':
            stats_header = f"📊 Estadísticas por 90 minutos (vs Molde) - {posicion}"
        else:
            stats_header = f"📊 Stats per 90 minutes (vs Template) - {posicion}"
        
        st.markdown(f"#### {stats_header}")
        
        # Mostrar métricas primarias dinámicamente
        cols_stats = st.columns(6)
        
        for idx, (col_nombre, emoji_label, col_molde) in enumerate(config['primary']):
            with cols_stats[idx]:
                valor_similar = jugador_detalle.get(col_nombre, 0)
                valor_molde = molde.get(col_molde, 0)
                
                if pd.notnull(valor_similar) and pd.notnull(valor_molde):
                    delta = valor_similar - valor_molde
                    st.metric(
                        emoji_label,
                        f"{valor_similar:.2f}",
                        delta=f"{delta:+.2f}"
                    )
                else:
                    st.metric(emoji_label, f"{valor_similar:.2f}" if pd.notnull(valor_similar) else "N/A")
        
        # ========== RADAR ADAPTATIVO ==========
        radar_title = t('comparative_radar') if lang == 'en' else "Radar Comparativo (Percentiles)"
        st.markdown(f"#### 🎯 {radar_title}")
        
        # Construir radar dinámicamente según posición
        categories = [label for _, label in config['radar']]
        
        values_similar = []
        values_molde = []
        
        for col_pct, _ in config['radar']:
            # Valor del jugador similar
            val_sim = jugador_detalle.get(col_pct.replace('pct_', 'destino_pct_'), 0.5)
            if pd.isna(val_sim):
                val_sim = 0.5
            values_similar.append(val_sim * 100)
            
            # Valor del molde
            val_mold = molde.get(col_pct, 0.5)
            if pd.isna(val_mold):
                val_mold = 0.5
            values_molde.append(val_mold * 100)
        
        fig = go.Figure()
        
        # Molde (trazo gris)
        fig.add_trace(go.Scatterpolar(
            r=values_molde,
            theta=categories,
            fill='toself',
            name=f"{molde['player']} (Molde)",
            line_color='rgba(150, 150, 150, 0.6)',
            fillcolor='rgba(150, 150, 150, 0.2)'
        ))
        
        # Jugador similar (trazo destacado)
        fig.add_trace(go.Scatterpolar(
            r=values_similar,
            theta=categories,
            fill='toself',
            name=jugador_detalle['destino_nombre'],
            line_color='#667eea',
            fillcolor='rgba(102, 126, 234, 0.3)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            height=450,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5
            )
        )
        
        st.plotly_chart(fig, use_container_width=True, key=f"radar_{unique_key}")
        
        # ========== CONTEXTO ADICIONAL ==========
        col_ctx1, col_ctx2 = st.columns(2)
        with col_ctx1:
            st.info(f"📈 Partidos: {int(jugador_detalle['destino_partidos'])}")
        with col_ctx2:
            st.info(f"⏱️ Minutos: {int(jugador_detalle['destino_minutos'])}")


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    st.title("Sistema de Métricas Adaptativas por Posición")
    
    st.markdown("""
    ### 🎯 Métricas mostradas según posición
    
    **Delanteros:**
    - Rating, Goles, xG, Asistencias, xA, Dribbles
    - Radar: xG, xA, Dribbles, Pases Prog., Aéreos, Rating
    
    **Mediocampistas:**
    - Rating, Pases Prog., xA, Asistencias, Recuperaciones, Dribbles
    - Radar: Pases Prog., xA, Dribbles, Recuperaciones, xG, Rating
    
    **Defensores:**
    - Rating, Recuperaciones, Aéreos, Pases Prog., Tackles, Intercepciones
    - Radar: Aéreos, Recuperaciones, Tackles, Intercepciones, Pases Prog., Rating
    
    ### 📊 Ventajas del sistema adaptativo
    
    1. **Relevancia:** Muestra métricas importantes para cada rol
    2. **Comparabilidad:** Solo compara jugadores en métricas que importan para su posición
    3. **Aprovecha datos:** Usa todas las columnas disponibles en BigQuery
    4. **Extensible:** Fácil agregar nuevas posiciones o métricas
    """)
    
    # Ejemplo visual
    posiciones = ['Delantero', 'Mediocampista', 'Defensor']
    
    for pos in posiciones:
        with st.expander(f"📋 Ver configuración para {pos}"):
            config = get_position_metrics(pos)
            
            st.markdown("**Métricas Primarias (6 columnas):**")
            for col, label, _ in config['primary']:
                st.write(f"- {label}: `{col}`")
            
            st.markdown("**Radar Chart (6 dimensiones):**")
            for col, label in config['radar']:
                st.write(f"- {label}: `{col}`")