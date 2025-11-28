"""
Scouting Pro AI - Utilities Module
===================================

Módulo centralizado con toda la lógica de negocio separada de la UI.

Módulos disponibles:
- database: Conexión a BigQuery y queries optimizadas
- search: Búsqueda fuzzy y normalización de texto
- visualization: Componentes visuales (tarjetas, radares, mapas PCA)
- logger: Sistema de logging estructurado

Uso:
    from utils.database import get_bigquery_client, obtener_similares
    from utils.search import buscar_jugadores_fuzzy
    from utils.visualization import mostrar_tarjeta_jugador
    from utils.logger import setup_logger

Autor: martinsintierra
Versión: 2.0.0
"""

__version__ = "2.0.0"
__author__ = "martinsintierra"

# Imports principales para facilitar uso
from .logger import setup_logger, log_query_performance, log_cache_event, log_user_action
from .database import (
    get_bigquery_client,
    get_all_players_index,
    obtener_similares,
    obtener_evolucion_jugador,
    obtener_datos_pca,
    obtener_percentiles_molde,
    get_system_stats
)
from .search import (
    normalizar_texto,
    buscar_jugadores_fuzzy,
    format_player_label
)
from .visualization import (
    mostrar_tarjeta_jugador_comparativa,
    mostrar_timeline_evolucion,
    mostrar_mapa_pca
)

__all__ = [
    # Logger
    'setup_logger',
    'log_query_performance',
    'log_cache_event',
    'log_user_action',
    
    # Database
    'get_bigquery_client',
    'get_all_players_index',
    'obtener_similares',
    'obtener_evolucion_jugador',
    'obtener_datos_pca',
    'obtener_percentiles_molde',
    'get_system_stats',
    
    # Search
    'normalizar_texto',
    'buscar_jugadores_fuzzy',
    'format_player_label',
    
    # Visualization
    'mostrar_tarjeta_jugador_comparativa',
    'mostrar_timeline_evolucion',
    'mostrar_mapa_pca',
]