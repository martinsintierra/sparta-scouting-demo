import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from .logger import setup_logger
from .i18n import t, get_language
from utils.visualization_adaptive import (
    get_position_metrics,
    mostrar_tarjeta_jugador_adaptativa
)


logger = setup_logger(__name__)


def calcular_proyeccion_valor(jugador: pd.Series) -> dict:
    """
    Calcula proyección de crecimiento basada en edad, rating y tendencias
    
    Args:
        jugador: Serie con datos del jugador
    
    Returns:
        Dict con proyección estimada y clasificación
    """
    edad = jugador.get('destino_edad', 99)
    rating = jugador.get('destino_rating', 0)
    
    # Lógica de proyección simple
    if edad < 21 and rating > 7.0:
        return {
            'delta_proyectado_pct': 25,
            'categoria': 'high_potential',
            'emoji': '🌟',
            'color': '#10b981'
        }
    elif edad < 23 and rating > 6.8:
        return {
            'delta_proyectado_pct': 18,
            'categoria': 'rising_star',
            'emoji': '⭐',
            'color': '#3b82f6'
        }
    elif edad < 25 and rating > 7.2:
        return {
            'delta_proyectado_pct': 12,
            'categoria': 'emerging',
            'emoji': '📈',
            'color': '#8b5cf6'
        }
    else:
        return {
            'delta_proyectado_pct': 0,
            'categoria': 'stable',
            'emoji': '',
            'color': '#6b7280'
        }


def mostrar_tarjeta_jugador_comparativa(jugador_detalle: pd.Series, molde: pd.Series, unique_key: str):
    """
    Renderiza tarjeta de detalle con comparación directa contra el molde
    INCLUYE: Badge de proyección de valor
    
    Args:
        jugador_detalle: Serie con datos del jugador similar
        molde: Serie con datos del jugador molde
        unique_key: Clave única para widgets
    """
    with st.container():
        st.markdown("---")
        
        # Calcular proyección
        proyeccion = calcular_proyeccion_valor(jugador_detalle)
        
        # ========== HEADER CON BADGE DE PROYECCIÓN ==========
        col_header1, col_header2, col_header3 = st.columns([3, 1, 1])
        
        with col_header1:
            # Nombre con emoji de proyección si aplica
            nombre_display = f"{proyeccion['emoji']} {jugador_detalle['destino_nombre']}" if proyeccion['emoji'] else jugador_detalle['destino_nombre']
            st.markdown(f"### {nombre_display}")
            st.caption(f"{jugador_detalle['destino_equipo']} | {jugador_detalle['posicion']}")
        
        with col_header2:
            # Badge de similitud
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
        
        # ========== BADGE DE PROYECCIÓN (SI APLICA) ==========
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
        
        # ========== MÉTRICAS PRINCIPALES ==========
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
        
        # ========== STATS COMPARATIVAS ==========
        lang = get_language()
        if lang == 'en':
            stats_header = "Comparative Stats per 90 minutes (vs Template)"
        else:
            stats_header = "Estadísticas por 90 minutos (vs Molde)"
        
        st.markdown(f"#### 📊 {stats_header}")
        
        col_stat1, col_stat2, col_stat3, col_stat4, col_stat5, col_stat6 = st.columns(6)
        
        # Helper para calcular delta
        def calc_delta(similar_val, molde_val):
            if pd.notnull(similar_val) and pd.notnull(molde_val):
                return similar_val - molde_val
            return None
        
        with col_stat1:
            delta_rating = calc_delta(jugador_detalle['destino_rating'], molde['rating_promedio'])
            st.metric(
                "⭐ Rating", 
                f"{jugador_detalle['destino_rating']:.2f}",
                delta=f"{delta_rating:+.2f}" if delta_rating is not None else None
            )
        with col_stat2:
            delta_goles = calc_delta(jugador_detalle['destino_goles'], molde.get('goals_p90', 0))
            st.metric(
                "⚽ Goles", 
                f"{jugador_detalle['destino_goles']:.2f}",
                delta=f"{delta_goles:+.2f}" if delta_goles is not None else None
            )
        with col_stat3:
            delta_xg = calc_delta(jugador_detalle['destino_xg'], molde['xG_p90'])
            st.metric(
                "🎯 xG", 
                f"{jugador_detalle['destino_xg']:.2f}",
                delta=f"{delta_xg:+.2f}" if delta_xg is not None else None
            )
        with col_stat4:
            delta_asist = calc_delta(jugador_detalle['destino_asistencias'], molde.get('assists_p90', 0))
            st.metric(
                "🅰️ Asist.", 
                f"{jugador_detalle['destino_asistencias']:.2f}",
                delta=f"{delta_asist:+.2f}" if delta_asist is not None else None
            )
        with col_stat5:
            delta_xa = calc_delta(jugador_detalle['destino_xa'], molde.get('xA_p90', 0))
            st.metric(
                "📤 xA", 
                f"{jugador_detalle['destino_xa']:.2f}",
                delta=f"{delta_xa:+.2f}" if delta_xa is not None else None
            )
        with col_stat6:
            delta_prog = calc_delta(jugador_detalle['destino_prog_passes'], molde.get('prog_passes_p90', 0))
            st.metric(
                "⬆️ Prog. Pass", 
                f"{jugador_detalle['destino_prog_passes']:.2f}",
                delta=f"{delta_prog:+.2f}" if delta_prog is not None else None
            )
        
        # ========== RADAR COMPARATIVO ==========
        radar_title = t('comparative_radar') if lang == 'en' else "Radar Comparativo (Percentiles)"
        st.markdown(f"#### 🎯 {radar_title}")
        
        categories = ['xG', 'xA', 'Pases Prog.', 'Dribbles', 'Recuperaciones']
        
        values_similar = [
            jugador_detalle.get('destino_pct_xg', 0) * 100,
            jugador_detalle.get('destino_pct_xa', 0) * 100,
            jugador_detalle.get('destino_pct_prog', 0) * 100,
            jugador_detalle.get('destino_pct_dribbles', 0) * 100,
            jugador_detalle.get('destino_pct_recov', 0) * 100,
        ]
        
        values_molde = [
            molde.get('pct_xG', 0.5) * 100 if 'pct_xG' in molde else 50,
            molde.get('pct_xA', 0.5) * 100 if 'pct_xA' in molde else 50,
            molde.get('pct_prog_passes', 0.5) * 100 if 'pct_prog_passes' in molde else 50,
            molde.get('pct_dribbles', 0.5) * 100 if 'pct_dribbles' in molde else 50,
            molde.get('pct_recoveries', 0.5) * 100 if 'pct_recoveries' in molde else 50,
        ]
        
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


def mostrar_timeline_evolucion(player_id: int, nombre_jugador: str, df_evo: pd.DataFrame):
    """
    Renderiza timeline de evolución del jugador
    """
    if df_evo.empty or len(df_evo) < 2:
        st.info(f"📊 No hay suficientes datos históricos para {nombre_jugador}")
        return
    
    st.markdown(f"#### 📈 Evolución Histórica: {nombre_jugador}")
    
    # Selector de métricas
    col_select1, col_select2 = st.columns(2)
    
    metricas_disponibles = {
        'rating_promedio': '⭐ Rating',
        'xG_p90': '🎯 xG por 90min',
        'xA_p90': '📤 xA por 90min',
        'goals_p90': '⚽ Goles por 90min',
        'assists_p90': '🅰️ Asistencias por 90min',
        'prog_passes_p90': '⬆️ Pases Progresivos por 90min'
    }
    
    with col_select1:
        metrica_principal = st.selectbox(
            "Métrica Principal",
            options=list(metricas_disponibles.keys()),
            format_func=lambda x: metricas_disponibles[x],
            key=f"timeline_main_{player_id}"
        )
    
    with col_select2:
        metrica_secundaria = st.selectbox(
            "Métrica Secundaria (opcional)",
            options=[None] + list(metricas_disponibles.keys()),
            format_func=lambda x: "Ninguna" if x is None else metricas_disponibles[x],
            key=f"timeline_sec_{player_id}"
        )
    
    # Crear figura
    fig = go.Figure()
    
    # Línea principal
    fig.add_trace(go.Scatter(
        x=df_evo['temporada_anio'],
        y=df_evo[metrica_principal],
        mode='lines+markers',
        name=metricas_disponibles[metrica_principal],
        line=dict(color='#667eea', width=3),
        marker=dict(size=10),
        hovertemplate='<b>Temp %{x}</b><br>%{y:.2f}<extra></extra>'
    ))
    
    # Línea secundaria
    if metrica_secundaria and metrica_secundaria != metrica_principal:
        fig.add_trace(go.Scatter(
            x=df_evo['temporada_anio'],
            y=df_evo[metrica_secundaria],
            mode='lines+markers',
            name=metricas_disponibles[metrica_secundaria],
            line=dict(color='#f59e0b', width=3, dash='dash'),
            marker=dict(size=8),
            yaxis='y2',
            hovertemplate='<b>Temp %{x}</b><br>%{y:.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            yaxis2=dict(
                title=metricas_disponibles[metrica_secundaria],
                overlaying='y',
                side='right',
                showgrid=False
            )
        )
    
    fig.update_layout(
        title=f"Evolución de {nombre_jugador} ({df_evo['temporada_anio'].min()}-{df_evo['temporada_anio'].max()})",
        xaxis_title="Temporada",
        yaxis_title=metricas_disponibles[metrica_principal],
        hovermode='x unified',
        height=450,
        showlegend=True,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla resumen
    with st.expander("📋 Ver datos completos"):
        df_display = df_evo.copy()
        df_display.columns = [
            'Temporada', 'Rating', 'xG/90', 'xA/90', 
            'Goles/90', 'Asist/90', 'ProgPass/90', 'PJ', 'Minutos'
        ]
        st.dataframe(df_display, use_container_width=True, hide_index=True)


def mostrar_mapa_pca(
    player_id_seleccionado: int, 
    posicion: str, 
    temporada: int, 
    nombre_jugador: str, 
    df_pca: pd.DataFrame
):
    """
    Renderiza mapa PCA con el jugador destacado
    """
    if df_pca.empty or len(df_pca) < 10:
        st.warning(f"⚠️ Insuficientes datos para PCA en {posicion} (temporada {temporada})")
        return
    
    st.markdown(f"#### 🗺️ Mapa de Similitud (PCA): {posicion} - Temp {temporada}")
    st.caption("Reducción dimensional de percentiles estadísticos. Jugadores cercanos tienen perfiles similares.")
    
    # Preparar datos
    columnas_pca = ['pct_xG', 'pct_xA', 'pct_prog_passes', 'pct_dribbles', 'pct_recoveries', 'pct_aerial', 'pct_rating']
    X = df_pca[columnas_pca].fillna(0).values
    
    # Normalizar y PCA
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    df_pca['PC1'] = X_pca[:, 0]
    df_pca['PC2'] = X_pca[:, 1]
    
    # Identificar jugador seleccionado
    df_pca['es_seleccionado'] = df_pca['player_id'] == player_id_seleccionado
    df_pca['color'] = df_pca['es_seleccionado'].map({True: 'Jugador Seleccionado', False: 'Otros'})
    df_pca['size'] = df_pca['es_seleccionado'].map({True: 15, False: 8})
    
    # Scatter plot
    fig = px.scatter(
        df_pca,
        x='PC1',
        y='PC2',
        color='color',
        size='size',
        hover_name='nombre_jugador',
        hover_data={
            'equipo_principal': True,
            'rating_promedio': ':.2f',
            'valor_millones': ':.1f',
            'PC1': False,
            'PC2': False,
            'color': False,
            'size': False
        },
        color_discrete_map={
            'Jugador Seleccionado': '#ef4444',
            'Otros': '#667eea'
        },
        title=f"Mapa de Perfiles - {posicion} ({len(df_pca)} jugadores)"
    )
    
    fig.update_traces(marker=dict(line=dict(width=1, color='white'), opacity=0.7))
    
    fig.update_layout(
        height=500,
        xaxis_title=f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% varianza)",
        yaxis_title=f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% varianza)",
        showlegend=True,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Métricas
    col_var1, col_var2, col_var3 = st.columns(3)
    with col_var1:
        st.metric("🎯 Varianza Explicada (PC1+PC2)", 
                  f"{(pca.explained_variance_ratio_[0] + pca.explained_variance_ratio_[1])*100:.1f}%")
    with col_var2:
        st.metric("👥 Jugadores Analizados", len(df_pca))
    with col_var3:
        if df_pca['es_seleccionado'].any():
            idx_seleccionado = df_pca[df_pca['es_seleccionado']].index[0]
            pc1_sel = df_pca.loc[idx_seleccionado, 'PC1']
            pc2_sel = df_pca.loc[idx_seleccionado, 'PC2']
            
            df_pca['distancia'] = np.sqrt(
                (df_pca['PC1'] - pc1_sel)**2 + (df_pca['PC2'] - pc2_sel)**2
            )
            
            umbral_cercania = df_pca['distancia'].quantile(0.10)
            cercanos = len(df_pca[df_pca['distancia'] <= umbral_cercania]) - 1
            st.metric("🎪 Jugadores Muy Similares", f"{cercanos}")
    
    # Top 10 más cercanos
    with st.expander("🔍 Ver los 10 jugadores más similares (por distancia PCA)"):
        if df_pca['es_seleccionado'].any():
            df_cercanos = df_pca[~df_pca['es_seleccionado']].nsmallest(10, 'distancia')
            df_cercanos_display = df_cercanos[[
                'nombre_jugador', 'equipo_principal', 'rating_promedio', 
                'valor_millones', 'distancia'
            ]].copy()
            df_cercanos_display.columns = ['Jugador', 'Equipo', 'Rating', 'Valor (€M)', 'Distancia PCA']
            df_cercanos_display['Distancia PCA'] = df_cercanos_display['Distancia PCA'].round(3)
            st.dataframe(df_cercanos_display, use_container_width=True, hide_index=True)
