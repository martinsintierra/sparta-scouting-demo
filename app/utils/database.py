import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from pathlib import Path
import time
import os
from typing import Optional
from .logger import setup_logger, log_query_performance, log_cache_event

logger = setup_logger(__name__)

# Configuración
PROJECT_ID = "proyecto-scouting-futbol"
DATASET = "dm_scouting"
CACHE_DIR = Path(".streamlit_cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_FILE = CACHE_DIR / "players_index.parquet"
CACHE_EXPIRY_HOURS = 24


def get_bigquery_client() -> Optional[bigquery.Client]:
    """
    Obtiene cliente de BigQuery con manejo robusto de credenciales
    
    Returns:
        Cliente de BigQuery o None si falla
    """
    try:
        if "gcp_service_account" in st.secrets:
            key_dict = st.secrets["gcp_service_account"]
            creds = service_account.Credentials.from_service_account_info(key_dict)
            client = bigquery.Client(credentials=creds, project=key_dict["project_id"])
            logger.info("Cliente BigQuery inicializado desde Streamlit secrets")
            return client
        else:
            client = bigquery.Client(project=PROJECT_ID)
            logger.info("Cliente BigQuery inicializado con credenciales locales")
            return client
    except Exception as e:
        logger.error(f"Error inicializando BigQuery client: {e}")
        st.error(f"❌ Error de conexión: {e}")
        return None


def cache_is_valid() -> bool:
    """Verifica si el caché en disco es válido (menos de 24 horas)"""
    if not CACHE_FILE.exists():
        logger.debug("Cache file no existe")
        return False
    
    file_age_hours = (time.time() - os.path.getmtime(CACHE_FILE)) / 3600
    is_valid = file_age_hours < CACHE_EXPIRY_HOURS
    
    if is_valid:
        logger.info(f"Cache válido | Edad: {file_age_hours:.1f}h")
    else:
        logger.info(f"Cache expirado | Edad: {file_age_hours:.1f}h")
    
    return is_valid


@st.cache_data(ttl=86400)
def get_all_players_index(_client: bigquery.Client) -> pd.DataFrame:
    """
    Descarga índice completo de jugadores con caché persistente
    
    Args:
        _client: Cliente de BigQuery
    
    Returns:
        DataFrame con índice de jugadores
    """
    start_time = time.time()
    
    # Intentar cargar desde disco primero
    if cache_is_valid():
        try:
            df = pd.read_parquet(CACHE_FILE)
            log_cache_event(logger, "hit", "players_index")
            st.sidebar.info("📂 Datos cargados desde caché local")
            return df
        except Exception as e:
            logger.warning(f"Error leyendo caché: {e}")
            log_cache_event(logger, "miss", "players_index")
    
    # Si no hay caché válido, consultar BigQuery
    log_cache_event(logger, "miss", "players_index")
    st.sidebar.info("☁️ Descargando datos desde BigQuery...")
    
    sql_index = f"""
        SELECT 
            player_id,
            nombre_jugador as player,
            equipo_principal, 
            temporada_anio,
            posicion,
            rating_promedio, 
            goals_p90,
            xG_p90,
            partidos_jugados,
            total_minutos
        FROM `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo`
        WHERE total_minutos >= 300
        ORDER BY temporada_anio DESC, rating_promedio DESC
    """
    
    df = _client.query(sql_index).to_dataframe()
    
    duration = time.time() - start_time
    log_query_performance(logger, "get_all_players_index", duration, len(df))
    
    # Pre-procesar columna normalizada
    from .search import normalizar_texto
    df['player_normalizado'] = df['player'].apply(normalizar_texto)
    
    # Guardar en disco
    try:
        df.to_parquet(CACHE_FILE)
        logger.info(f"Caché guardado en disco | {len(df)} registros")
        st.sidebar.success("💾 Caché guardado en disco")
    except Exception as e:
        logger.warning(f"No se pudo guardar caché: {e}")
    
    return df


@st.cache_data(ttl=3600)
def get_players_by_season(temporada: int, _df_index: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra jugadores por temporada (caché selectivo)
    
    Args:
        temporada: Año de la temporada
        _df_index: DataFrame completo de jugadores
    
    Returns:
        DataFrame filtrado por temporada
    """
    df_filtered = _df_index[_df_index['temporada_anio'] == temporada].copy()
    logger.debug(f"Filtrado por temporada {temporada} | {len(df_filtered)} jugadores")
    return df_filtered


@st.cache_data(ttl=3600)
def obtener_similares(
    id_origen: str, 
    temp_origen: int, 
    temp_destino: Optional[int], 
    min_score: float, 
    _client: bigquery.Client
) -> pd.DataFrame:
    """
    Obtiene jugadores similares para una temporada específica
    
    Args:
        id_origen: ID del jugador origen
        temp_origen: Temporada del jugador origen
        temp_destino: Temporada destino (None = todas)
        min_score: Score mínimo de similitud
        _client: Cliente BigQuery
    
    Returns:
        DataFrame con jugadores similares
    """
    start_time = time.time()
    
    condicion_temp = f"AND s.temporada_similar = {temp_destino}" if temp_destino else ""
    
    sql_similitud = f"""
        SELECT 
            s.jugador_similar_id,
            v.nombre_jugador as destino_nombre, 
            v.equipo_principal as destino_equipo, 
            v.posicion,
            s.temporada_similar,
            s.score_similitud,
            s.rank_similitud,
            v.edad_promedio as destino_edad, 
            v.valor_mercado as destino_valor,
            v.rating_promedio as destino_rating,
            v.goals_p90 as destino_goles,
            v.assists_p90 as destino_asistencias,
            v.xG_p90 as destino_xg,
            v.xA_p90 as destino_xa,
            v.prog_passes_p90 as destino_prog_passes,
            v.dribbles_p90 as destino_dribbles,
            v.recoveries_p90 as destino_recoveries,
            v.aerial_won_p90 as destino_aereos,
            v.partidos_jugados as destino_partidos,
            v.total_minutos as destino_minutos,
            v.nacionalidad as destino_nacionalidad,
            v.altura as destino_altura,
            v.pie as destino_pie,
            v.contrato_vence as destino_contrato,
            v.pct_xG as destino_pct_xg,
            v.pct_xA as destino_pct_xa,
            v.pct_prog_passes as destino_pct_prog,
            v.pct_dribbles as destino_pct_dribbles,
            v.pct_recoveries as destino_pct_recov
        FROM `{PROJECT_ID}.{DATASET}.scouting_similitud_pro_v2` s
        JOIN `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo` v
          ON CAST(v.player_id AS STRING) = s.jugador_similar_id
          AND v.temporada_anio = s.temporada_similar
        WHERE s.jugador_origen_id = '{id_origen}'
          AND s.temporada_origen = {temp_origen}
          {condicion_temp}
          AND s.score_similitud >= {min_score}
        ORDER BY s.score_similitud DESC 
        LIMIT 50
    """
    
    df = _client.query(sql_similitud).to_dataframe()
    
    duration = time.time() - start_time
    log_query_performance(logger, f"obtener_similares (temp={temp_destino})", duration, len(df))
    
    return df


@st.cache_data(ttl=3600)
def obtener_evolucion_jugador(player_id: int, _client: bigquery.Client) -> pd.DataFrame:
    """
    Obtiene la evolución histórica de un jugador
    
    Args:
        player_id: ID del jugador
        _client: Cliente BigQuery
    
    Returns:
        DataFrame con evolución temporal
    """
    start_time = time.time()
    
    sql_evolucion = f"""
        SELECT 
            temporada_anio,
            rating_promedio,
            xG_p90,
            xA_p90,
            goals_p90,
            assists_p90,
            prog_passes_p90,
            partidos_jugados,
            total_minutos
        FROM `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo`
        WHERE player_id = {player_id}
        ORDER BY temporada_anio
    """
    
    df = _client.query(sql_evolucion).to_dataframe()
    
    duration = time.time() - start_time
    log_query_performance(logger, "obtener_evolucion_jugador", duration, len(df))
    
    return df


@st.cache_data(ttl=3600)
def obtener_datos_pca(posicion: str, temporada: int, _client: bigquery.Client) -> pd.DataFrame:
    """
    Obtiene datos de percentiles para análisis PCA
    
    Args:
        posicion: Posición del jugador
        temporada: Temporada
        _client: Cliente BigQuery
    
    Returns:
        DataFrame con percentiles
    """
    start_time = time.time()
    
    sql_pca = f"""
        SELECT 
            player_id,
            nombre_jugador,
            equipo_principal,
            valor_millones,
            rating_promedio,
            pct_xG,
            pct_xA,
            pct_prog_passes,
            pct_dribbles,
            pct_recoveries,
            pct_aerial,
            pct_rating
        FROM `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo`
        WHERE posicion = '{posicion}'
          AND temporada_anio = {temporada}
          AND total_minutos >= 300
          AND pct_xG IS NOT NULL
          AND pct_xA IS NOT NULL
    """
    
    df = _client.query(sql_pca).to_dataframe()
    
    duration = time.time() - start_time
    log_query_performance(logger, f"obtener_datos_pca ({posicion})", duration, len(df))
    
    return df


def get_system_stats(_client: bigquery.Client) -> dict:
    """
    Obtiene estadísticas generales del sistema
    
    Returns:
        Diccionario con métricas clave
    """
    start_time = time.time()
    
    query_jugadores = f"""
        SELECT COUNT(DISTINCT player_id) as total_jugadores
        FROM `{PROJECT_ID}.{DATASET}.v_dashboard_scouting_completo`
    """
    
    query_relaciones = f"""
        SELECT COUNT(*) as total_relaciones
        FROM `{PROJECT_ID}.{DATASET}.scouting_similitud_pro_v2`
    """
    
    total_jugadores = _client.query(query_jugadores).to_dataframe().iloc[0]['total_jugadores']
    total_relaciones = _client.query(query_relaciones).to_dataframe().iloc[0]['total_relaciones']
    
    duration = time.time() - start_time
    log_query_performance(logger, "get_system_stats", duration)
    
    return {
        "total_jugadores": int(total_jugadores),
        "total_relaciones": int(total_relaciones),
        "temporadas": "2021-2025"
    }