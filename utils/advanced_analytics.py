"""
Módulo de Análisis Avanzado
Aprovecha TODAS las columnas de v_dashboard_scouting_completo
"""

import streamlit as st
import pandas as pd
from google.cloud import bigquery
from typing import Optional, List, Dict
from utils.logger import setup_logger, log_query_performance
import time

logger = setup_logger(__name__)

PROJECT_ID = "proyecto-scouting-futbol"
DATASET = "dm_scouting"


# ========== 1. BÚSQUEDA CON ARQUETIPOS ==========
@st.cache_data(ttl=3600)
def buscar_por_arquetipo(
    arquetipo: str,
    temporada: int,
    min_rating: float = 6.0,
    max_valor: float = 50.0,
    _client: bigquery.Client = None
) -> pd.DataFrame:
    """
    Busca jugadores de un arquetipo específico
    Aprovecha: arquetipo_nombre, valor_millones, rating_promedio
    """
    start_time = time.time()
    
    sql = f"""
    SELECT 
        nombre_jugador,
        equipo_principal,
        posicion,
        edad_promedio,
        valor_millones,
        rating_promedio,
        arquetipo_nombre,
        xG_p90,
        xA_p90,
        prog_passes_p90,
        recoveries_p90,
        partidos_jugados,
        total_minutos
    FROM `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo`
    WHERE temporada_anio = {temporada}
      AND arquetipo_nombre LIKE '%{arquetipo}%'
      AND rating_promedio >= {min_rating}
      AND valor_millones <= {max_valor}
      AND total_minutos >= 300
    ORDER BY rating_promedio DESC
    LIMIT 50
    """
    
    df = _client.query(sql).to_dataframe()
    
    duration = time.time() - start_time
    log_query_performance(logger, f"buscar_por_arquetipo ({arquetipo})", duration, len(df))
    
    return df


# ========== 2. ANÁLISIS DE PROYECCIÓN DE VALOR ==========
@st.cache_data(ttl=3600)
def top_proyecciones_valor(
    posicion: Optional[str] = None,
    temporada: int = 2025,
    min_delta_pct: float = 15.0,
    _client: bigquery.Client = None
) -> pd.DataFrame:
    """
    Encuentra jugadores con alta proyección de revalorización
    Aprovecha: delta_proyectado_pct, valor_proyectado_millones
    """
    start_time = time.time()
    
    filtro_posicion = f"AND posicion = '{posicion}'" if posicion else ""
    
    sql = f"""
    SELECT 
        nombre_jugador,
        equipo_principal,
        posicion,
        edad_promedio,
        valor_millones,
        valor_proyectado_millones,
        delta_proyectado_pct,
        rating_promedio,
        xG_p90,
        xA_p90,
        arquetipo_nombre,
        partidos_jugados
    FROM `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo`
    WHERE temporada_anio = {temporada}
      AND delta_proyectado_pct >= {min_delta_pct}
      AND valor_millones IS NOT NULL
      AND valor_proyectado_millones IS NOT NULL
      {filtro_posicion}
      AND total_minutos >= 300
    ORDER BY delta_proyectado_pct DESC, valor_millones ASC
    LIMIT 30
    """
    
    df = _client.query(sql).to_dataframe()
    
    duration = time.time() - start_time
    log_query_performance(logger, "top_proyecciones_valor", duration, len(df))
    
    return df


# ========== 3. ANÁLISIS DE SIMILARES CON DETALLES ==========
@st.cache_data(ttl=3600)
def obtener_similares_expandidos(
    player_id: str,
    temporada: int,
    _client: bigquery.Client = None
) -> pd.DataFrame:
    """
    Obtiene los 5 similares con TODOS sus detalles
    Aprovecha: similares_top5 (ARRAY de STRUCT)
    """
    start_time = time.time()
    
    sql = f"""
    WITH Base AS (
        SELECT 
            nombre_jugador as jugador_origen,
            posicion,
            similares_top5
        FROM `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo`
        WHERE CAST(player_id AS STRING) = '{player_id}'
          AND temporada_anio = {temporada}
    )
    
    SELECT 
        jugador_origen,
        posicion,
        similar.nombre as jugador_similar,
        similar.equipo as equipo_similar,
        similar.edad as edad_similar,
        similar.valor_millones as valor_similar,
        similar.score_similitud,
        similar.rank_similitud,
        
        -- Unir con detalles completos del similar
        det.rating_promedio,
        det.xG_p90,
        det.xA_p90,
        det.prog_passes_p90,
        det.recoveries_p90,
        det.arquetipo_nombre,
        det.delta_proyectado_pct
        
    FROM Base,
    UNNEST(similares_top5) as similar
    
    LEFT JOIN `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo` det
      ON CAST(det.player_id AS STRING) = similar.jugador_similar_id
      AND det.temporada_anio = {temporada}
    
    ORDER BY similar.rank_similitud
    """
    
    df = _client.query(sql).to_dataframe()
    
    duration = time.time() - start_time
    log_query_performance(logger, "obtener_similares_expandidos", duration, len(df))
    
    return df


# ========== 4. BÚSQUEDA MULTI-CRITERIO AVANZADA ==========
@st.cache_data(ttl=3600)
def busqueda_multi_criterio(
    posicion: str,
    temporada: int,
    edad_max: int = 25,
    valor_max: float = 20.0,
    min_rating: float = 6.5,
    min_pct_xg: float = 0.60,
    min_delta_pct: float = 10.0,
    _client: bigquery.Client = None
) -> pd.DataFrame:
    """
    Búsqueda ultra-específica con múltiples criterios
    Caso de uso: "Jóvenes promesas con potencial de revalorización"
    """
    start_time = time.time()
    
    sql = f"""
    SELECT 
        nombre_jugador,
        equipo_principal,
        edad_promedio,
        valor_millones,
        valor_proyectado_millones,
        delta_proyectado_pct,
        rating_promedio,
        xG_p90,
        xA_p90,
        
        -- Percentiles (para filtrar elite)
        pct_xG,
        pct_xA,
        pct_prog_passes,
        pct_rating,
        
        arquetipo_nombre,
        partidos_jugados,
        
        -- Acceso a similares
        similares_top5[OFFSET(0)].nombre as similar_1,
        similares_top5[OFFSET(0)].score_similitud as score_1
        
    FROM `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo`
    WHERE temporada_anio = {temporada}
      AND posicion = '{posicion}'
      AND edad_promedio <= {edad_max}
      AND valor_millones <= {valor_max}
      AND rating_promedio >= {min_rating}
      AND pct_xG >= {min_pct_xg}
      AND delta_proyectado_pct >= {min_delta_pct}
      AND total_minutos >= 500  -- Más de 500 minutos = datos confiables
    ORDER BY delta_proyectado_pct DESC, rating_promedio DESC
    LIMIT 20
    """
    
    df = _client.query(sql).to_dataframe()
    
    duration = time.time() - start_time
    log_query_performance(logger, "busqueda_multi_criterio", duration, len(df))
    
    return df


# ========== 5. ANÁLISIS DE OPORTUNIDADES POR ARQUETIPO ==========
@st.cache_data(ttl=3600)
def top_oportunidades_por_arquetipo(
    temporada: int = 2025,
    _client: bigquery.Client = None
) -> pd.DataFrame:
    """
    Encuentra el mejor jugador de cada arquetipo en cada rango de precio
    Caso de uso: "Quiero el mejor 'Goleador Aereo' económico"
    """
    start_time = time.time()
    
    sql = f"""
    WITH Rangos AS (
        SELECT
            arquetipo_nombre,
            CASE 
                WHEN valor_millones < 10 THEN 'Económico (<€10M)'
                WHEN valor_millones < 30 THEN 'Medio (€10-30M)'
                ELSE 'Premium (>€30M)'
            END as rango_precio,
            nombre_jugador,
            equipo_principal,
            posicion,
            edad_promedio,
            valor_millones,
            valor_proyectado_millones,
            delta_proyectado_pct,
            rating_promedio,
            xG_p90,
            xA_p90,
            ROW_NUMBER() OVER (
                PARTITION BY 
                    arquetipo_nombre,
                    CASE 
                        WHEN valor_millones < 10 THEN 'Económico (<€10M)'
                        WHEN valor_millones < 30 THEN 'Medio (€10-30M)'
                        ELSE 'Premium (>€30M)'
                    END
                ORDER BY rating_promedio DESC, delta_proyectado_pct DESC
            ) as rank
        FROM `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo`
        WHERE temporada_anio = {temporada}
          AND arquetipo_nombre IS NOT NULL
          AND valor_millones IS NOT NULL
          AND total_minutos >= 300
    )
    SELECT * 
    FROM Rangos
    WHERE rank = 1
    ORDER BY arquetipo_nombre, rango_precio
    """
    
    df = _client.query(sql).to_dataframe()
    
    duration = time.time() - start_time
    log_query_performance(logger, "top_oportunidades_por_arquetipo", duration, len(df))
    
    return df


# ========== 6. ANÁLISIS DE EVOLUCIÓN CON PROYECCIÓN ==========
@st.cache_data(ttl=3600)
def analisis_evolucion_con_proyeccion(
    player_id: int,
    _client: bigquery.Client = None
) -> pd.DataFrame:
    """
    Evolución histórica + proyección futura
    Aprovecha: todas las temporadas + valor_proyectado
    """
    start_time = time.time()
    
    sql = f"""
    SELECT 
        temporada_anio,
        equipo_principal,
        rating_promedio,
        xG_p90,
        xA_p90,
        valor_millones,
        valor_proyectado_millones,
        delta_proyectado_pct,
        arquetipo_nombre,
        partidos_jugados,
        total_minutos,
        
        -- Percentiles para ver evolución de rendimiento relativo
        pct_rating,
        pct_xG,
        pct_xA
        
    FROM `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo`
    WHERE player_id = {player_id}
    ORDER BY temporada_anio
    """
    
    df = _client.query(sql).to_dataframe()
    
    duration = time.time() - start_time
    log_query_performance(logger, "analisis_evolucion_con_proyeccion", duration, len(df))
    
    return df


# ========== 7. COMPARACIÓN CON SIMILARES DIRECTOS ==========
@st.cache_data(ttl=3600)
def comparar_con_similares(
    player_id: str,
    temporada: int,
    _client: bigquery.Client = None
) -> Dict[str, pd.DataFrame]:
    """
    Retorna jugador + sus 5 similares en formato comparativo
    """
    start_time = time.time()
    
    # Jugador principal
    sql_main = f"""
    SELECT 
        nombre_jugador,
        equipo_principal,
        posicion,
        edad_promedio,
        valor_millones,
        rating_promedio,
        xG_p90,
        xA_p90,
        prog_passes_p90,
        recoveries_p90,
        arquetipo_nombre,
        delta_proyectado_pct,
        
        -- Percentiles
        pct_rating,
        pct_xG,
        pct_xA,
        pct_prog_passes,
        pct_recoveries
        
    FROM `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo`
    WHERE CAST(player_id AS STRING) = '{player_id}'
      AND temporada_anio = {temporada}
    """
    
    df_main = _client.query(sql_main).to_dataframe()
    
    # Similares
    df_similares = obtener_similares_expandidos(player_id, temporada, _client)
    
    duration = time.time() - start_time
    log_query_performance(logger, "comparar_con_similares", duration)
    
    return {
        'jugador_principal': df_main,
        'similares': df_similares
    }


# ========== DEMO STREAMLIT ==========
if __name__ == "__main__":
    st.title("🔬 Analytics Avanzado - Aprovechando la View Completa")
    
    st.markdown("""
    ### 📊 Funcionalidades disponibles
    
    Este módulo aprovecha **TODAS** las columnas de `v_dashboard_scouting_completo`:
    
    1. **Búsqueda por Arquetipo** 
       - `arquetipo_nombre`, `valor_millones`, `rating_promedio`
    
    2. **Top Proyecciones de Valor**
       - `delta_proyectado_pct`, `valor_proyectado_millones`
    
    3. **Similares Expandidos**
       - `similares_top5` (ARRAY de STRUCT)
       - Expande detalles completos de cada similar
    
    4. **Búsqueda Multi-Criterio**
       - Combina posición, edad, valor, rating, percentiles, proyección
    
    5. **Oportunidades por Arquetipo**
       - Mejor jugador de cada arquetipo en cada rango de precio
    
    6. **Evolución con Proyección**
       - Histórico + futuro proyectado
    
    7. **Comparación con Similares**
       - Jugador + 5 similares con todos sus stats
    
    ---
    
    ### 🎯 Casos de uso reales
    
    **Scenario 1: "Necesito un '9' joven y barato con potencial"**
    ```python
    df = busqueda_multi_criterio(
        posicion='Delantero',
        temporada=2025,
        edad_max=23,
        valor_max=15.0,
        min_rating=6.8,
        min_pct_xg=0.70,
        min_delta_pct=15.0,
        _client=client
    )
    ```
    
    **Scenario 2: "¿Quién es el mejor 'Mediapunta Creativo' económico?"**
    ```python
    df = top_oportunidades_por_arquetipo(
        temporada=2025,
        _client=client
    )
    df_filtrado = df[
        (df['arquetipo_nombre'].str.contains('Creativo')) &
        (df['rango_precio'] == 'Económico (<€10M)')
    ]
    ```
    
    **Scenario 3: "¿Cómo ha evolucionado X y cuál es su proyección?"**
    ```python
    df = analisis_evolucion_con_proyeccion(
        player_id=12345,
        _client=client
    )
    # Graficar rating_promedio + valor_proyectado_millones en timeline
    ```
    
    **Scenario 4: "¿Quiénes son realmente similares a Julián Álvarez y cómo se comparan?"**
    ```python
    data = comparar_con_similares(
        player_id='67890',
        temporada=2024,
        _client=client
    )
    
    # data['jugador_principal'] → DataFrame con 1 fila
    # data['similares'] → DataFrame con 5 filas
    # Construir tabla comparativa o radar multi-jugador
    ```
    
    ---
    
    ### 🚀 Integración con Streamlit
    
    Estas funciones están diseñadas para:
    - **Cachear automáticamente** (1 hora)
    - **Loggear performance**
    - **Retornar DataFrames listos para visualizar**
    
    Ejemplo de uso en una página:
    ```python
    from utils.advanced_analytics import top_proyecciones_valor
    from utils.database import get_bigquery_client
    
    client = get_bigquery_client()
    df = top_proyecciones_valor(
        posicion='Mediocampista',
        temporada=2025,
        min_delta_pct=20.0,
        _client=client
    )
    
    st.dataframe(df)
    ```
    """)