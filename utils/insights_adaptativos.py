"""
Sistema de Insights Adaptativos Multi-Jugador
Análisis inteligente según posiciones y perfiles
"""

import pandas as pd
from typing import List, Dict
from .i18n import t, get_language

def generar_insights_comparacion(jugadores: List[Dict]) -> List[str]:
    """
    Genera insights contextuales según posiciones y stats
    
    Args:
        jugadores: Lista de dicts con datos de cada jugador
    
    Returns:
        Lista de strings con insights
    """
    insights = []
    lang = get_language()
    
    # 1. Detectar si hay posiciones mixtas
    posiciones = [j['posicion'] for j in jugadores]
    posiciones_unicas = set(posiciones)
    
    if len(posiciones_unicas) > 1:
        if lang == 'es':
            insights.append("⚠️ **Comparando posiciones diferentes.** Los insights son limitados.")
        else:
            insights.append("⚠️ **Comparing different positions.** Insights are limited.")
    
    # 2. Análisis de mejor rendimiento GLOBAL
    mejor_rating = max(jugadores, key=lambda x: x['rating'])
    insights.append(
        f"🏆 **{t('best_overall_rating')}:** {mejor_rating['nombre']} ({mejor_rating['rating']:.2f})"
    )
    
    # 3. Insights por métrica clave
    mejor_goleador = max(jugadores, key=lambda x: x.get('goals', 0))
    if mejor_goleador['goals'] > 0.3:  # Solo si es relevante
        insights.append(
            f"⚽ **{t('top_scorer')}:** {mejor_goleador['nombre']} ({mejor_goleador['goals']:.2f} {t('goals_per_90')})"
        )
    
    mejor_xg = max(jugadores, key=lambda x: x['xG'])
    if mejor_xg['xG'] > 0.2:
        insights.append(
            f"🎯 **{t('best_xg_quality')}:** {mejor_xg['nombre']} ({mejor_xg['xG']:.2f} xG/90)"
        )
    
    # 4. Análisis de balance ofensivo/defensivo
    for j in jugadores:
        j['balance_of_def'] = (j.get('xG', 0) + j.get('xA', 0)) / max(j.get('recoveries', 0), 0.1)
    
    mas_ofensivo = max(jugadores, key=lambda x: x['balance_of_def'])
    mas_defensivo = min(jugadores, key=lambda x: x['balance_of_def'])
    
    if mas_ofensivo['balance_of_def'] > 2:
        insights.append(
            f"⚔️ **{t('pure_offensive')}:** {mas_ofensivo['nombre']}"
        )
    
    if mas_defensivo['balance_of_def'] < 0.5:
        insights.append(
            f"🛡️ **{t('pure_defensive')}:** {mas_defensivo['nombre']}"
        )
    
    # 5. Jugador más completo (mejor promedio de percentiles)
    for j in jugadores:
        percentiles = [
            j.get('pct_xG', 0.5),
            j.get('pct_xA', 0.5),
            j.get('pct_prog_passes', 0.5),
            j.get('pct_recoveries', 0.5)
        ]
        j['avg_percentile'] = sum(percentiles) / len(percentiles)
    
    mas_completo = max(jugadores, key=lambda x: x['avg_percentile'])
    insights.append(
        f"⭐ **{t('most_complete')}:** {mas_completo['nombre']} (avg percentil {mas_completo['avg_percentile']*100:.0f})"
    )
    
    return insights