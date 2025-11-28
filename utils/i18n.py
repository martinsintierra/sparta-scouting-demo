"""
Sistema de InternacionalizaciÃ³n (i18n) para Scouting Pro AI
Soporta mÃºltiples idiomas con estructura modular
"""

import streamlit as st
from typing import Dict, Any
from pathlib import Path
import json

# Diccionario completo de traducciones
TRANSLATIONS = {
    "es": {
        # NavegaciÃ³n
        "app_title": "Scouting Pro",
        "page_home": "Inicio",
        "page_search": "Buscar",
        "page_compare": "Comparar",
        "page_pca": "Explorador PCA",
        "page_evolution": "EvoluciÃ³n",
        "page_config": "ConfiguraciÃ³n",
        "page_glossary": "Glosario",
        
        # Home
        "home_title": "Recurso de Scouting - Motor Vectorial de Similitud",
        "home_subtitle": "Sistema de recomendaciÃ³n basado en **K-Nearest Neighbors** con ponderaciÃ³n por posiciÃ³n y decay temporal.",
        "home_description": "Encuentra jugadores similares usando xG, xA, pases progresivos, recuperaciones y mÃ¡s.",
        "home_coverage": "Actualmente cubre Liga Profesional Argentina (2021-2025) y Primera B Nacional (2025)",
        "system_stats": "EstadÃ­sticas del Sistema",
        "unique_players": "Jugadores Ãšnicos",
        "similarity_relations": "Relaciones de Similitud",
        "seasons": "Temporadas",
        "get_started": "Comenzar",
        "main_features": "CaracterÃ­sticas Principales",
        "model_precision": "PrecisiÃ³n del Modelo",
        "analyzed_metrics": "MÃ©tricas Analizadas",
        "available_tools": "Herramientas Disponibles",
        "performance": "Performance",
        "suggestion": "Sugerencia",
        "suggestion_text": "EmpezÃ¡ explorando la secciÃ³n Buscar para encontrar jugadores similares a tu perfil ideal.",
        "more_info": "Para mÃ¡s informaciÃ³n, consultÃ¡ el Glosario en la barra lateral!",
        
        # Buscar
        "search_title": "Buscar Jugadores Similares",
        "search_subtitle": "EncontrÃ¡ jugadores con perfiles estadÃ­sticos similares usando bÃºsqueda inteligente.",
        "search_config": "ConfiguraciÃ³n de BÃºsqueda",
        "search_player": "Buscar Jugador",
        "search_placeholder": "Ej: Retegui, Borja, Arce",
        "search_help": "BÃºsqueda inteligente: EscribÃ­ con errores de tipeo, sin tildes o mayÃºsculas. ¡No pasa nada!",
        "origin_season": "Temporada Origen",
        "min_similarity": "Similitud MÃ­nima %",
        "advanced_options": "Opciones Avanzadas",
        "fuzzy_tolerance": "Tolerancia de bÃºsqueda (fuzzy)",
        "fuzzy_help": "Mayor = mÃ¡s estricto. Menor = encuentra mÃ¡s resultados con errores de tipeo",
        "results_found": "Encontrados {} resultados",
        "fuzzy_match": "resultados similares (fuzzy match)",
        "exact_match": "resultados exactos",
        "select_version": "SeleccionÃ¡ versiÃ³n del jugador:",
        "mold_profile": "Perfil del Molde",
        "team": "Equipo",
        "season": "Temporada",
        "position": "PosiciÃ³n",
        "rating": "Rating",
        "matches": "Partidos",
        "similar_players": "Jugadores Similares",
        "similarity_interpretation": "Â¿CÃ³mo interpretar el porcentaje de similitud?",
        "tab_season_2025": "Temporada 2025",
        "tab_season_2024": "Temporada 2024",
        "tab_all_seasons": "Todas las Temporadas",
        "best_match": "Mejor Match",
        "average": "Promedio",
        "quality": "Calidad",
        "view_details": "Ver detalles de:",
        "view_full_table": "Ver tabla completa de resultados",
        "no_results": "No se encontraron jugadores similares con score >= {}%",
        "search_suggestions": "Sugerencias",
        "reduce_min_similarity": "Reduce el porcentaje mÃ­nimo de similitud",
        "try_another_season": "Prueba con otra temporada",
        "verify_position_data": "Verifica que existan datos para esta posiciÃ³n",
        "start_typing": "ArrancÃ¡ escribiendo el nombre de un jugador en la barra lateral",
        "how_to_use": "CÃ³mo usar esta herramienta",
        
        # Comparar
        "compare_title": "Comparar Jugadores",
        "compare_subtitle": "ComparÃ¡ hasta 4 jugadores lado a lado para identificar fortalezas y debilidades.",
        "select_players": "Seleccionar Jugadores",
        "num_players": "NÃºmero de jugadores a comparar",
        "num_players_help": "SeleccionÃ¡ cuÃ¡ntos jugadores querÃ©s comparar",
        "player_num": "Jugador {}",
        "search_player_num": "Buscar jugador {}",
        "season_player_num": "Temporada jugador {}",
        "select_version_num": "Seleccionar versiÃ³n {}",
        "comparing_players": "Comparando {} jugadores",
        "comparative_table": "Tabla Comparativa",
        "comparative_radar": "Radar Comparativo (Percentiles)",
        "strengths_analysis": "AnÃ¡lisis de Fortalezas Relativas",
        "top_3_strengths": "Top 3 Fortalezas",
        "improvement_areas": "Ãreas de Mejora",
        "automatic_insights": "Insights AutomÃ¡ticos",
        "best_rating": "Mejor Rating",
        "top_scorer": "MÃ¡s Goleador",
        "best_xg": "Mejor xG",
        "search_2_players": "BuscÃ¡ al menos 2 jugadores en la barra lateral para comenzar la comparaciÃ³n",
        
        # PCA
        "pca_title": "Explorador PCA - Mapa de Similitudes",
        "pca_subtitle": "VisualizÃ¡ jugadores en un espacio bidimensional usando **PCA (Principal Component Analysis)**.",
        "pca_description": "Jugadores cercanos en el mapa tienen perfiles estadÃ­sticos similares.",
        "select_player": "Seleccionar Jugador",
        "search_help_pca": "BuscÃ¡ el jugador que quieres destacar en el mapa",
        "season_analysis": "Temporada para AnÃ¡lisis",
        "search_tolerance": "Tolerancia de bÃºsqueda",
        "select_player_list": "Selecciona jugador:",
        "calculating_pca": "Calculando PCA...",
        "insufficient_data": "No hay suficientes datos para {} en temporada {}",
        "what_is_pca": "Â¿QuÃ© es el anÃ¡lisis PCA?",
        "start_searching": "Comienza buscando un jugador en la barra lateral",
        "variance_explained": "Varianza Explicada (PC1+PC2)",
        "players_analyzed": "Jugadores Analizados",
        "very_similar_players": "Jugadores Muy Similares",
        "view_top_10": "Ver los 10 jugadores mÃ¡s similares (por distancia PCA)",
        
        # EvoluciÃ³n
        "evolution_title": "EvoluciÃ³n HistÃ³rica de Jugadores",
        "evolution_subtitle": "Analiza cÃ³mo ha evolucionado el rendimiento de un jugador a travÃ©s de las temporadas.",
        "player_name": "Nombre del jugador",
        "evolution_help": "EscribÃ­ el nombre y verÃ¡s todas sus temporadas disponibles",
        "current_club": "Club Actual",
        "current_rating": "Rating Actual",
        "loading_history": "Cargando datos histÃ³ricos...",
        "trends_analysis": "AnÃ¡lisis de Tendencias",
        "rating_evolution": "EvoluciÃ³n del Rating",
        "xg_evolution": "EvoluciÃ³n xG/90",
        "total_matches": "Partidos Totales",
        "vs_first_season": "vs primera temp",
        "automatic_insights": "Insights AutomÃ¡ticos",
        "improved_significantly": "{} ha mejorado significativamente su rating ({:+.2f} puntos)",
        "declined_rating": "{} ha experimentado una caÃ­da en su rating ({:+.2f} puntos)",
        "stable_performance": "{} ha mantenido un rendimiento estable a lo largo de las temporadas",
        "best_season": "Mejor temporada",
        "with_rating": "con rating",
        "no_historical_data": "No se encontraron datos histÃ³ricos para {}",
        "insufficient_seasons": "No hay suficientes datos histÃ³ricos para {}",
        "need_2_seasons": "Se necesitan al menos 2 temporadas con 300+ minutos jugados para visualizar evoluciÃ³n.",
        
        # ConfiguraciÃ³n
        "config_title": "ConfiguraciÃ³n y Mantenimiento",
        "config_subtitle": "Panel de control para gestionar cachÃ©, logs y configuraciones del sistema.",
        "cache_tab": "CachÃ©",
        "logs_tab": "Logs",
        "about_tab": "Acerca de",
        "cache_management": "GestiÃ³n de CachÃ©",
        "disk_cache": "CachÃ© en Disco",
        "memory_cache": "CachÃ© en Memoria",
        "cache_active": "CachÃ© activo",
        "size": "TamaÃ±o",
        "age": "AntigÃ¼edad",
        "hours": "horas",
        "clear_disk_cache": "Limpiar CachÃ© en Disco",
        "clear_memory_cache": "Limpiar CachÃ© de Streamlit",
        "cache_cleared": "CachÃ© eliminado. Recarga la pÃ¡gina para regenerar.",
        "when_to_clear": "CuÃ¡ndo limpiar el cachÃ©",
        "system_logs": "Logs del Sistema",
        "log_files_found": "Encontrados {} archivos de log",
        "select_log_file": "Seleccionar archivo de log",
        "num_lines": "NÃºmero de lÃ­neas a mostrar",
        "filter_level": "Filtrar por nivel",
        "load_logs": "Cargar Logs",
        "export_logs": "Exportar Logs",
        "download_today_logs": "Descargar Logs del DÃ­a",
        "download": "Descargar",
        
        # Glosario
        "glossary_title": "Glosario y Contexto TÃ©cnico",
        "glossary_subtitle": "GuÃ­a de interpretaciÃ³n, conceptos tÃ©cnicos y limitaciones del sistema.",
        "metrics_glossary": "Glosario de MÃ©tricas",
        "technical_concepts": "Conceptos TÃ©cnicos",
        "limitations": "Limitaciones y Uso Responsable",
        
        # MÃ©tricas comunes
        "age": "Edad",
        "height": "Altura",
        "foot": "Pie",
        "country": "PaÃ­s",
        "value": "Valor",
        "contract": "Contrato",
        "goals": "Goles",
        "assists": "Asist.",
        "progressive_passes": "Prog. Pass",
        "dribbles": "Dribbles",
        "recoveries": "Recuperaciones",
        "aerial_duels": "AÃ©reos",
        
        # Mensajes comunes
        "loading": "Cargando...",
        "error": "Error",
        "success": "Ã‰xito",
        "warning": "Advertencia",
        "info": "InformaciÃ³n",
        "not_found": "No encontrado",
        "connection_error": "Error de conexiÃ³n",
        "no_data": "Sin datos disponibles",
    },
    
    "en": {
        # Navigation
        "app_title": "Scouting Pro",
        "page_home": "Home",
        "page_search": "Search",
        "page_compare": "Compare",
        "page_pca": "PCA Explorer",
        "page_evolution": "Evolution",
        "page_config": "Settings",
        "page_glossary": "Glossary",
        
        # Home
        "home_title": "Scouting Resource - Vector Similarity Engine",
        "home_subtitle": "Recommendation system based on **K-Nearest Neighbors** with position-specific weighting and temporal decay.",
        "home_description": "Find similar players using xG, xA, progressive passes, recoveries and more.",
        "home_coverage": "Currently covers Argentine Professional League (2021-2025) and Primera B Nacional (2025)",
        "system_stats": "System Statistics",
        "unique_players": "Unique Players",
        "similarity_relations": "Similarity Relations",
        "seasons": "Seasons",
        "get_started": "Get Started",
        "main_features": "Main Features",
        "model_precision": "Model Precision",
        "analyzed_metrics": "Analyzed Metrics",
        "available_tools": "Available Tools",
        "performance": "Performance",
        "suggestion": "Tip",
        "suggestion_text": "Start by exploring the Search section to find players similar to your ideal profile.",
        "more_info": "For more information, check the Glossary in the sidebar!",
        
        # Search
        "search_title": "Search Similar Players",
        "search_subtitle": "Find players with similar statistical profiles using intelligent search.",
        "search_config": "Search Configuration",
        "search_player": "Search Player",
        "search_placeholder": "e.g., Retegui, Borja, Arce",
        "search_help": "Smart search: Type with typos, without accents or capitals. It's okay!",
        "origin_season": "Origin Season",
        "min_similarity": "Minimum Similarity %",
        "advanced_options": "Advanced Options",
        "fuzzy_tolerance": "Search tolerance (fuzzy)",
        "fuzzy_help": "Higher = stricter. Lower = finds more results with typos",
        "results_found": "Found {} results",
        "fuzzy_match": "similar results (fuzzy match)",
        "exact_match": "exact results",
        "select_version": "Select player version:",
        "mold_profile": "Mold Profile",
        "team": "Team",
        "season": "Season",
        "position": "Position",
        "rating": "Rating",
        "matches": "Matches",
        "similar_players": "Similar Players",
        "similarity_interpretation": "How to interpret similarity percentage?",
        "tab_season_2025": "Season 2025",
        "tab_season_2024": "Season 2024",
        "tab_all_seasons": "All Seasons",
        "best_match": "Best Match",
        "average": "Average",
        "quality": "Quality",
        "view_details": "View details:",
        "view_full_table": "View complete results table",
        "no_results": "No similar players found with score >= {}%",
        "search_suggestions": "Suggestions",
        "reduce_min_similarity": "Reduce minimum similarity percentage",
        "try_another_season": "Try another season",
        "verify_position_data": "Verify that data exists for this position",
        "start_typing": "Start typing a player's name in the sidebar",
        "how_to_use": "How to use this tool",
        
        # Compare
        "compare_title": "Compare Players",
        "compare_subtitle": "Compare up to 4 players side by side to identify strengths and weaknesses.",
        "select_players": "Select Players",
        "num_players": "Number of players to compare",
        "num_players_help": "Select how many players you want to compare",
        "player_num": "Player {}",
        "search_player_num": "Search player {}",
        "season_player_num": "Season player {}",
        "select_version_num": "Select version {}",
        "comparing_players": "Comparing {} players",
        "comparative_table": "Comparative Table",
        "comparative_radar": "Comparative Radar (Percentiles)",
        "strengths_analysis": "Relative Strengths Analysis",
        "top_3_strengths": "Top 3 Strengths",
        "improvement_areas": "Improvement Areas",
        "automatic_insights": "Automatic Insights",
        "best_rating": "Best Rating",
        "top_scorer": "Top Scorer",
        "best_xg": "Best xG",
        "search_2_players": "Search at least 2 players in the sidebar to start comparison",
        
        # PCA
        "pca_title": "PCA Explorer - Similarity Map",
        "pca_subtitle": "Visualize players in a two-dimensional space using **PCA (Principal Component Analysis)**.",
        "pca_description": "Players close on the map have similar statistical profiles.",
        "select_player": "Select Player",
        "search_help_pca": "Search for the player you want to highlight on the map",
        "season_analysis": "Season for Analysis",
        "search_tolerance": "Search tolerance",
        "select_player_list": "Select player:",
        "calculating_pca": "Calculating PCA...",
        "insufficient_data": "Not enough data for {} in season {}",
        "what_is_pca": "What is PCA analysis?",
        "start_searching": "Start by searching for a player in the sidebar",
        "variance_explained": "Variance Explained (PC1+PC2)",
        "players_analyzed": "Players Analyzed",
        "very_similar_players": "Very Similar Players",
        "view_top_10": "View top 10 most similar players (by PCA distance)",
        
        # Evolution
        "evolution_title": "Player Historical Evolution",
        "evolution_subtitle": "Analyze how a player's performance has evolved through seasons.",
        "player_name": "Player name",
        "evolution_help": "Type the name and you'll see all available seasons",
        "current_club": "Current Club",
        "current_rating": "Current Rating",
        "loading_history": "Loading historical data...",
        "trends_analysis": "Trends Analysis",
        "rating_evolution": "Rating Evolution",
        "xg_evolution": "xG/90 Evolution",
        "total_matches": "Total Matches",
        "vs_first_season": "vs first season",
        "automatic_insights": "Automatic Insights",
        "improved_significantly": "{} has significantly improved their rating ({:+.2f} points)",
        "declined_rating": "{} has experienced a rating decline ({:+.2f} points)",
        "stable_performance": "{} has maintained stable performance throughout seasons",
        "best_season": "Best season",
        "with_rating": "with rating",
        "no_historical_data": "No historical data found for {}",
        "insufficient_seasons": "Not enough historical data for {}",
        "need_2_seasons": "At least 2 seasons with 300+ minutes played needed to visualize evolution.",
        
        # Settings
        "config_title": "Settings and Maintenance",
        "config_subtitle": "Control panel to manage cache, logs and system settings.",
        "cache_tab": "Cache",
        "logs_tab": "Logs",
        "about_tab": "About",
        "cache_management": "Cache Management",
        "disk_cache": "Disk Cache",
        "memory_cache": "Memory Cache",
        "cache_active": "Cache active",
        "size": "Size",
        "age": "Age",
        "hours": "hours",
        "clear_disk_cache": "Clear Disk Cache",
        "clear_memory_cache": "Clear Streamlit Cache",
        "cache_cleared": "Cache cleared. Reload page to regenerate.",
        "when_to_clear": "When to clear cache",
        "system_logs": "System Logs",
        "log_files_found": "Found {} log files",
        "select_log_file": "Select log file",
        "num_lines": "Number of lines to show",
        "filter_level": "Filter by level",
        "load_logs": "Load Logs",
        "export_logs": "Export Logs",
        "download_today_logs": "Download Today's Logs",
        "download": "Download",
        
        # Glossary
        "glossary_title": "Glossary and Technical Context",
        "glossary_subtitle": "Interpretation guide, technical concepts and system limitations.",
        "metrics_glossary": "Metrics Glossary",
        "technical_concepts": "Technical Concepts",
        "limitations": "Limitations and Responsible Use",
        
        # Common metrics
        "age": "Age",
        "height": "Height",
        "foot": "Foot",
        "country": "Country",
        "value": "Value",
        "contract": "Contract",
        "goals": "Goals",
        "assists": "Assists",
        "progressive_passes": "Prog. Pass",
        "dribbles": "Dribbles",
        "recoveries": "Recoveries",
        "aerial_duels": "Aerial",
        
        # Common messages
        "loading": "Loading...",
        "error": "Error",
        "success": "Success",
        "warning": "Warning",
        "info": "Information",
        "not_found": "Not found",
        "connection_error": "Connection error",
        "no_data": "No data available",
    }
}


def get_language() -> str:
    """
    Obtiene el idioma actual desde session_state
    
    Returns:
        CÃ³digo de idioma ('es' o 'en')
    """
    if 'language' not in st.session_state:
        st.session_state.language = 'es'  # EspaÃ±ol por defecto
    return st.session_state.language


def set_language(lang_code: str):
    """
    Establece el idioma de la aplicaciÃ³n
    
    Args:
        lang_code: CÃ³digo de idioma ('es' o 'en')
    """
    if lang_code in TRANSLATIONS:
        st.session_state.language = lang_code
    else:
        st.warning(f"Idioma '{lang_code}' no disponible. Usando espaÃ±ol.")
        st.session_state.language = 'es'


def t(key: str, **kwargs) -> str:
    """
    Traduce una clave al idioma actual
    
    Args:
        key: Clave de traducciÃ³n
        **kwargs: ParÃ¡metros para formateo de strings
    
    Returns:
        String traducido
    
    Ejemplo:
        >>> t("results_found", num=5)
        "Encontrados 5 resultados"
    """
    lang = get_language()
    translation = TRANSLATIONS.get(lang, TRANSLATIONS['es']).get(key, key)
    
    # Aplicar formateo si hay kwargs
    if kwargs:
        try:
            translation = translation.format(**kwargs)
        except (KeyError, IndexError):
            pass
    
    return translation


def language_selector():
    """
    Renderiza un selector de idioma en la sidebar
    
    Usage:
        from utils.i18n import language_selector
        language_selector()
    """
    st.sidebar.markdown("---")
    
    current_lang = get_language()
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button(
            "🇪🇸 EspaÃ±ol" if current_lang != 'es' else "✅ EspaÃ±ol",
            use_container_width=True,
            type="primary" if current_lang == 'es' else "secondary"
        ):
            set_language('es')
            st.rerun()
    
    with col2:
        if st.button(
            "🇬🇧 English" if current_lang != 'en' else "✅ English",
            use_container_width=True,
            type="primary" if current_lang == 'en' else "secondary"
        ):
            set_language('en')
            st.rerun()
    
    st.sidebar.caption(f"Current: {'EspaÃ±ol' if current_lang == 'es' else 'English'}")


def get_available_languages() -> Dict[str, str]:
    """
    Obtiene lista de idiomas disponibles
    
    Returns:
        Diccionario con cÃ³digos y nombres de idiomas
    """
    return {
        'es': '🇪🇸 EspaÃ±ol',
        'en': '🇬🇧 English'
    }


# Helper functions para casos comunes
def translate_position(position: str) -> str:
    """Traduce posiciones de jugador"""
    positions = {
        'es': {
            'Forward': 'Delantero',
            'Midfielder': 'Mediocampista',
            'Defender': 'Defensor',
            'Goalkeeper': 'Arquero'
        },
        'en': {
            'Delantero': 'Forward',
            'Mediocampista': 'Midfielder',
            'Defensor': 'Defender',
            'Arquero': 'Goalkeeper'
        }
    }
    
    lang = get_language()
    return positions.get(lang, {}).get(position, position)


def translate_month(month: int) -> str:
    """Traduce nombres de meses"""
    months = {
        'es': ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
               'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
        'en': ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']
    }
    
    lang = get_language()
    return months[lang][month - 1]