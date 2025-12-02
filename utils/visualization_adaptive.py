"""
Sistema de Visualización Adaptativo por Posición - CORREGIDO
✅ Usa nombres de columnas reales de BigQuery (sin prefijo destino_)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Tuple
from utils.i18n import t, get_language


def get_position_metrics(posicion: str) -> Dict[str, List[Tuple[str, str, str]]]:
    """
    Retorna métricas relevantes por posición
    
    ✅ CORREGIDO: Usa nombres de columnas reales de BigQuery
    
    Estructura de tuplas:
    - [0]: Nombre columna en jugador_similar (SIN prefijo destino_)
    - [1]: Label con emoji para display
    - [2]: Nombre columna en molde (para comparación)
    """
    lang = get_language()
    
    # Mapeo de posiciones normalizadas
    pos_normalizada = posicion.lower()
    

    if 'arquero' in pos_normalizada or 'goalkeeper' in pos_normalizada or 'portero' in pos_normalizada or 'goleiro' in pos_normalizada:
        return {
            'primary': [
                ('rating_promedio', '⭐ Rating', 'rating_promedio'),
                ('saves_p90', '🧤 Atajadas', 'saves_p90'),
                ('saves_pct', '📊 % Ataj.', 'saves_pct'),
                ('clean_sheets_pct', '🛡️ Valla Inv.', 'clean_sheets_pct'),
                ('sweeper_p90', '🏃 Sweeper', 'sweeper_p90'),
                ('claims_p90', '✊ Salidas', 'claims_p90')
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
                ('rating_promedio', '⭐ Rating', 'rating_promedio'),
                ('goals_p90', '⚽ Goles', 'goals_p90'),
                ('xG_p90', '🎯 xG', 'xG_p90'),
                ('assists_p90', '🅰️ Asist.', 'assists_p90'),
                ('xA_p90', '📤 xA', 'xA_p90'),
                ('dribbles_p90', '🎪 Dribbles', 'dribbles_p90')
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
                ('rating_promedio', '⭐ Rating', 'rating_promedio'),
                ('prog_passes_p90', '⬆️ Prog. Pass', 'prog_passes_p90'),
                ('xA_p90', '📤 xA', 'xA_p90'),
                ('assists_p90', '🅰️ Asist.', 'assists_p90'),
                ('recoveries_p90', '🔄 Recup.', 'recoveries_p90'),
                ('dribbles_p90', '🎪 Dribbles', 'dribbles_p90')
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
                ('rating_promedio', '⭐ Rating', 'rating_promedio'),
                ('recoveries_p90', '🔄 Recup.', 'recoveries_p90'),
                ('aerial_won_p90', '✈️ Aéreos', 'aerial_won_p90'),
                ('prog_passes_p90', '⬆️ Prog. Pass', 'prog_passes_p90'),
                ('tackles_p90', '🛡️ Tackles', 'tackles_p90'),
                ('interceptions_p90', '🚧 Interc.', 'interceptions_p90')
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
        # Fallback genérico
        return {
            'primary': [
                ('rating_promedio', '⭐ Rating', 'rating_promedio'),
                ('recoveries_p90', '🔄 Recup.', 'recoveries_p90'),
                ('prog_passes_p90', '⬆️ Prog. Pass', 'prog_passes_p90'),
                ('aerial_won_p90', '✈️ Aéreos', 'aerial_won_p90'),
                ('xA_p90', '📤 xA', 'xA_p90'),
                ('xG_p90', '🎯 xG', 'xG_p90')
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
    
    ✅ CORREGIDO: Busca columnas reales de BigQuery
    
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
            # ✅ CORREGIDO: Nombre del jugador
            nombre = jugador_detalle.get('nombre_jugador', jugador_detalle.get('jugador_similar', 'N/A'))
            nombre_display = f"{proyeccion['emoji']} {nombre}" if proyeccion['emoji'] else nombre
            st.markdown(f"### {nombre_display}")
            
            # ✅ CORREGIDO: Equipo y posición
            equipo = jugador_detalle.get('equipo_principal', jugador_detalle.get('equipo_similar', 'N/A'))
            posicion = jugador_detalle.get('posicion', 'N/A')
            st.caption(f"{equipo} | {posicion}")
        
        with col_header2:
            score = jugador_detalle.get('score_similitud', 0)
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
                {score:.1f}% Match
            </div>
            """, unsafe_allow_html=True)
        
        with col_header3:
            temporada = jugador_detalle.get('temporada_anio', jugador_detalle.get('temporada_similar', 2025))
            st.caption(f"📅 Temp. {int(temporada)}")
        
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
            edad = jugador_detalle.get('edad_promedio', jugador_detalle.get('edad_similar', 0))
            st.metric("🎂 Edad", f"{int(edad)}" if pd.notnull(edad) else "N/A")
        
        with col2:
            altura = jugador_detalle.get('altura', 0)
            st.metric("📏 Altura", f"{altura:.0f} cm" if pd.notnull(altura) and altura > 0 else "N/A")
        
        with col3:
            pie = jugador_detalle.get('pie', 'N/A')
            st.metric("🦶 Pie", pie if pd.notnull(pie) else "N/A")
        
        with col4:
            pais = jugador_detalle.get('nacionalidad', 'N/A')
            st.metric("🌍 País", pais if pd.notnull(pais) else "N/A")
        
        with col5:
            valor = jugador_detalle.get('valor_mercado', jugador_detalle.get('valor_mercado_similar', 0))
            if pd.notnull(valor) and valor > 0:
                st.metric("💰 Valor", f"€{valor/1000:.0f}K")
            else:
                st.metric("💰 Valor", "N/A")
        
        with col6:
            contrato = jugador_detalle.get('contrato_vence', 'N/A')
            st.metric("📄 Contrato", str(contrato)[:4] if pd.notnull(contrato) else "N/A")
        
        # ========== STATS ADAPTATIVAS POR POSICIÓN ==========
        config = get_position_metrics(posicion)
        
        lang = get_language()
        if lang == 'es':
            stats_header = f"📊 Estadísticas por 90 minutos (vs Molde) - {posicion}"
        else:
            stats_header = f"📊 Stats per 90 minutes (vs Template) - {posicion}"
        
        st.markdown(f"#### {stats_header}")
        
        # ✅ CORREGIDO: Usar nombres de columnas reales
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
                    st.metric(
                        emoji_label, 
                        f"{valor_similar:.2f}" if pd.notnull(valor_similar) else "N/A"
                    )
        
        # ========== RADAR ADAPTATIVO ==========
        radar_title = t('comparative_radar') if lang == 'en' else "Radar Comparativo (Percentiles)"
        st.markdown(f"#### 🎯 {radar_title}")
        
        # Construir radar dinámicamente según posición
        categories = [label for _, label in config['radar']]
        
        values_similar = []
        values_molde = []
        
        for col_pct, _ in config['radar']:
            # ✅ CORREGIDO: Usar nombre de columna real
            val_sim = jugador_detalle.get(col_pct, 0.5)
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
            name=f"{molde.get('player', 'Molde')}",
            line_color='rgba(150, 150, 150, 0.6)',
            fillcolor='rgba(150, 150, 150, 0.2)'
        ))
        
        # Jugador similar (trazo destacado)
        fig.add_trace(go.Scatterpolar(
            r=values_similar,
            theta=categories,
            fill='toself',
            name=nombre,
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
            partidos = jugador_detalle.get('partidos_jugados', 0)
            st.info(f"📈 Partidos: {int(partidos)}" if pd.notnull(partidos) else "📈 Partidos: N/A")
        with col_ctx2:
            minutos = jugador_detalle.get('total_minutos', 0)
            st.info(f"⏱️ Minutos: {int(minutos)}" if pd.notnull(minutos) else "⏱️ Minutos: N/A")


# ========== DEBUGGING HELPER ==========
def debug_columnas_disponibles(df: pd.DataFrame):
    """Helper para verificar qué columnas tiene tu DataFrame"""
    st.sidebar.markdown("### 🔍 Debug: Columnas disponibles")
    st.sidebar.code("\n".join(sorted(df.columns)))
    
    # Verificar columnas críticas
    columnas_criticas = [
        'rating_promedio', 'recoveries_p90', 'tackles_p90', 
        'interceptions_p90', 'aerial_won_p90', 'prog_passes_p90'
    ]
    
    st.sidebar.markdown("### ✅ Columnas críticas:")
    for col in columnas_criticas:
        if col in df.columns:
            st.sidebar.success(f"✓ {col}")
        else:
            st.sidebar.error(f"✗ {col} FALTA")