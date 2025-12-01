"""
Sistema de Filtros Económicos para Scouting Pro
Funcionalidad reutilizable en múltiples páginas - VERSIÓN CORREGIDA
"""

import streamlit as st
import pandas as pd
from typing import Dict, Optional, Tuple
from .i18n import t, get_language


def render_economic_filters_sidebar(
    default_max_value: int = 50,
    default_age_range: Tuple[int, int] = (16, 40),
    default_young_prospects: bool = False,
    expanded: bool = False
) -> Dict[str, any]:
    """
    Renderiza filtros económicos en sidebar y retorna configuración
    
    Args:
        default_max_value: Valor máximo por defecto (millones €)
        default_age_range: Rango de edad por defecto
        default_young_prospects: Toggle de jóvenes promesas por defecto
        expanded: Si el expander debe estar abierto
    
    Returns:
        Dict con configuración de filtros
    """
    with st.sidebar.expander(f"💰 {t('economic_filters')}", expanded=expanded):
        
        # Filtro de valor de mercado
        valor_max = st.slider(
            t("max_value"),
            min_value=0,
            max_value=50,
            value=default_max_value,
            step=1,
            help="Filtra jugadores por su valor de mercado máximo en millones de euros"
        )
        
        # Filtro de edad
        edad_min, edad_max = st.slider(
            t("age_range"),
            min_value=16,
            max_value=40,
            value=default_age_range,
            step=1,
            help="Define el rango de edad de los jugadores a buscar"
        )
        
        # Toggle para jóvenes promesas
        solo_jovenes = st.checkbox(
            t("young_prospects"),
            value=default_young_prospects,
            help=t("young_prospects_help")
        )
        
        # Filtros adicionales (opcionales)
        st.divider()
        
        # Filtro de contrato
        with st.expander("📄 Contrato", expanded=False):
            filtro_contrato_activo = st.checkbox(
                "Filtrar por vencimiento de contrato",
                value=False
            )
            
            if filtro_contrato_activo:
                filtro_contrato = st.slider(
                    "Contrato vence antes de:",
                    min_value=2024,
                    max_value=2030,
                    value=2026,
                    step=1,
                    help="Solo jugadores con contrato que vence antes del año seleccionado"
                )
            else:
                filtro_contrato = None
        
        # Filtro de nacionalidad
        with st.expander("🌍 Nacionalidad", expanded=False):
            filtro_nacionalidad_activo = st.checkbox(
                "Filtrar por nacionalidades",
                value=False
            )
            
            if filtro_nacionalidad_activo:
                lang = get_language()
                if lang == 'es':
                    paises_sugeridos = [
                        "Argentina", "Brasil", "Uruguay", "Chile", 
                        "Colombia", "Paraguay", "España", "Italia"
                    ]
                else:
                    paises_sugeridos = [
                        "Argentina", "Brazil", "Uruguay", "Chile", 
                        "Colombia", "Paraguay", "Spain", "Italy"
                    ]
                
                filtro_nacionalidad = st.multiselect(
                    "Selecciona países:",
                    options=paises_sugeridos,
                    default=None,
                    help="Filtra jugadores de las nacionalidades seleccionadas"
                )
            else:
                filtro_nacionalidad = None
    
    return {
        'valor_max': valor_max,
        'edad_min': edad_min,
        'edad_max': edad_max,
        'solo_jovenes': solo_jovenes,
        'filtro_contrato': filtro_contrato,
        'filtro_nacionalidad': filtro_nacionalidad
    }


def aplicar_filtros_economicos(
    df: pd.DataFrame, 
    config_filtros: Dict[str, any],
    prefijo_columnas: str = ""
) -> pd.DataFrame:
    """
    Aplica filtros económicos a un DataFrame - VERSIÓN CORREGIDA
    
    Args:
        df: DataFrame a filtrar
        config_filtros: Dict con configuración de filtros
        prefijo_columnas: Prefijo de columnas (ej: "destino_" para resultados de similitud)
    
    Returns:
        DataFrame filtrado
    """
    if df.empty:
        return df
    
    df_filtered = df.copy()
    
    # Nombres de columnas según prefijo
    col_valor = f"{prefijo_columnas}valor" if prefijo_columnas else "valor_mercado"
    col_edad = f"{prefijo_columnas}edad" if prefijo_columnas else "edad_promedio"
    col_rating = f"{prefijo_columnas}rating" if prefijo_columnas else "rating_promedio"
    col_contrato = f"{prefijo_columnas}contrato" if prefijo_columnas else "contrato_vence"
    col_nacionalidad = f"{prefijo_columnas}nacionalidad" if prefijo_columnas else "nacionalidad"
    
    # FILTRO 1: Valor de mercado (CORREGIDO)
    if col_valor in df_filtered.columns:
        # Detectar escala automáticamente usando valor medio
        valor_medio = df_filtered[col_valor].dropna().mean()
        
        if pd.isna(valor_medio):
            # Si no hay valores, skip
            pass
        elif valor_medio > 10_000:
            # Valores en unidades (ej: 5000000 = 5M)
            df_filtered['valor_millones'] = df_filtered[col_valor] / 1_000_000
        elif valor_medio > 10:
            # Valores en miles (ej: 5000 = 5M)
            df_filtered['valor_millones'] = df_filtered[col_valor] / 1_000
        else:
            # Valores ya en millones (ej: 5.0 = 5M)
            df_filtered['valor_millones'] = df_filtered[col_valor]
        
        # Filtrar (solo si existe la columna procesada)
        if 'valor_millones' in df_filtered.columns:
            df_filtered = df_filtered[
                df_filtered['valor_millones'].fillna(999) <= config_filtros['valor_max']
            ]
    
    # FILTRO 2: Rango de edad (CORREGIDO - maneja NaN)
    if col_edad in df_filtered.columns:
        df_filtered = df_filtered[df_filtered[col_edad].notna()]  # ✅ Eliminar NaN
        df_filtered = df_filtered[
            (df_filtered[col_edad] >= config_filtros['edad_min']) &
            (df_filtered[col_edad] <= config_filtros['edad_max'])
        ]
    
    # FILTRO 3: Jóvenes promesas
    if config_filtros['solo_jovenes']:
        if col_edad in df_filtered.columns and col_rating in df_filtered.columns:
            df_filtered = df_filtered[
                (df_filtered[col_edad] < 23) &
                (df_filtered[col_rating] > 6.5)
            ]
    
    # FILTRO 4: Vencimiento de contrato (CORREGIDO - maneja NaN)
    if config_filtros['filtro_contrato'] and col_contrato in df_filtered.columns:
        # Convertir a año si es fecha
        df_filtered['contrato_anio'] = pd.to_datetime(
            df_filtered[col_contrato], 
            errors='coerce'
        ).dt.year
        
        df_filtered = df_filtered[df_filtered['contrato_anio'].notna()]  # ✅ Eliminar NaN
        df_filtered = df_filtered[
            df_filtered['contrato_anio'] <= config_filtros['filtro_contrato']
        ]
    
    # FILTRO 5: Nacionalidad
    if config_filtros['filtro_nacionalidad'] and col_nacionalidad in df_filtered.columns:
        if len(config_filtros['filtro_nacionalidad']) > 0:
            df_filtered = df_filtered[
                df_filtered[col_nacionalidad].isin(config_filtros['filtro_nacionalidad'])
            ]
    
    return df_filtered


def mostrar_resumen_filtrado(
    total_original: int, 
    total_filtrado: int,
    config_filtros: Dict[str, any]
) -> None:
    """
    Muestra resumen del filtrado aplicado
    """
    lang = get_language()
    
    if total_filtrado < total_original:
        filtros_activos = []
        
        if config_filtros['valor_max'] < 50:
            filtros_activos.append(f"Valor ≤ €{config_filtros['valor_max']}M")
        
        if config_filtros['edad_min'] > 16 or config_filtros['edad_max'] < 40:
            filtros_activos.append(f"Edad {config_filtros['edad_min']}-{config_filtros['edad_max']}")
        
        if config_filtros['solo_jovenes']:
            filtros_activos.append("Jóvenes promesas" if lang == 'es' else "Young prospects")
        
        if config_filtros['filtro_contrato']:
            filtros_activos.append(f"Contrato ≤ {config_filtros['filtro_contrato']}")
        
        if config_filtros['filtro_nacionalidad']:
            paises = ', '.join(config_filtros['filtro_nacionalidad'][:2])
            if len(config_filtros['filtro_nacionalidad']) > 2:
                paises += "..."
            filtros_activos.append(f"País: {paises}")
        
        filtros_texto = " | ".join(filtros_activos)
        
        st.sidebar.info(
            f"🔎 {t('showing_filtered').format(total_filtrado)} "
            f"(de {total_original} totales)\n\n"
            f"**Filtros activos:** {filtros_texto}"
        )
    else:
        st.sidebar.success(f"✅ {total_filtrado} jugadores encontrados (sin filtros)")


def calcular_proyeccion_mejorada(jugador: pd.Series) -> Dict[str, any]:
    """
    Calcula proyección de crecimiento con algoritmo mejorado
    """
    edad = jugador.get('destino_edad', jugador.get('edad_promedio', jugador.get('edad', 99)))
    rating = jugador.get('destino_rating', jugador.get('rating_promedio', jugador.get('rating', 0)))
    valor = jugador.get('destino_valor', jugador.get('valor_mercado', jugador.get('valor', 0)))
    partidos = jugador.get('destino_partidos', jugador.get('partidos_jugados', jugador.get('partidos', 0)))
    
    # Convertir valor a millones si es necesario (CORREGIDO)
    if pd.notna(valor):
        if valor > 10_000:
            valor_millones = valor / 1_000_000
        elif valor > 10:
            valor_millones = valor / 1_000
        else:
            valor_millones = valor
    else:
        valor_millones = 0
    
    # CATEGORIZACIÓN POR EDAD Y RATING
    if edad < 21 and rating > 7.2:
        categoria = 'elite_prospect'
        delta_proyectado_pct = 40
        emoji = '💎'
        color = '#8b5cf6'
        descripcion_es = "Prospecto Elite"
        descripcion_en = "Elite Prospect"
    
    elif edad < 21 and rating > 6.8:
        categoria = 'high_potential'
        delta_proyectado_pct = 30
        emoji = '🌟'
        color = '#10b981'
        descripcion_es = "Alto Potencial"
        descripcion_en = "High Potential"
    
    elif edad < 23 and rating > 7.0:
        categoria = 'rising_star'
        delta_proyectado_pct = 25
        emoji = '⭐'
        color = '#3b82f6'
        descripcion_es = "Estrella en Ascenso"
        descripcion_en = "Rising Star"
    
    elif edad < 23 and rating > 6.5:
        categoria = 'promising'
        delta_proyectado_pct = 18
        emoji = '📈'
        color = '#f59e0b'
        descripcion_es = "Promesa"
        descripcion_en = "Promising"
    
    elif edad < 25 and rating > 7.2:
        categoria = 'emerging'
        delta_proyectado_pct = 15
        emoji = '🚀'
        color = '#06b6d4'
        descripcion_es = "Emergente"
        descripcion_en = "Emerging"
    
    elif edad > 32 and rating > 7.0:
        categoria = 'veteran_quality'
        delta_proyectado_pct = -10
        emoji = '🎖️'
        color = '#6b7280'
        descripcion_es = "Veterano de Calidad"
        descripcion_en = "Quality Veteran"
    
    else:
        categoria = 'stable'
        delta_proyectado_pct = 0
        emoji = ''
        color = '#6b7280'
        descripcion_es = "Estable"
        descripcion_en = "Stable"
    
    # FACTOR DE VALOR (oportunidad de mercado)
    valor_oportunidad = False
    if valor_millones < 5 and rating > 6.8 and partidos > 10:
        valor_oportunidad = True
        delta_proyectado_pct += 10
    
    lang = get_language()
    descripcion = descripcion_es if lang == 'es' else descripcion_en
    
    return {
        'categoria': categoria,
        'delta_proyectado_pct': delta_proyectado_pct,
        'emoji': emoji,
        'color': color,
        'descripcion': descripcion,
        'valor_oportunidad': valor_oportunidad,
        'edad': edad,
        'rating': rating,
        'valor_millones': valor_millones
    }


def mostrar_badge_proyeccion(proyeccion: Dict[str, any], use_sidebar: bool = False) -> None:
    """
    Renderiza badge visual de proyección
    """
    lang = get_language()
    
    if proyeccion['delta_proyectado_pct'] > 10:
        
        if lang == 'es':
            texto_proyeccion = f"Proyección: {proyeccion['delta_proyectado_pct']:+.0f}% valor en 12 meses"
            if proyeccion['valor_oportunidad']:
                texto_proyeccion += " | 💰 OPORTUNIDAD"
        else:
            texto_proyeccion = f"Projection: {proyeccion['delta_proyectado_pct']:+.0f}% value in 12 months"
            if proyeccion['valor_oportunidad']:
                texto_proyeccion += " | 💰 OPPORTUNITY"
        
        badge_html = f"""
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
            {proyeccion['emoji']} {proyeccion['descripcion']} | {texto_proyeccion}
        </div>
        """
        
        if use_sidebar:
            st.sidebar.markdown(badge_html, unsafe_allow_html=True)
        else:
            st.markdown(badge_html, unsafe_allow_html=True)