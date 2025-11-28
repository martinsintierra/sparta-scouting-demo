import pandas as pd
import unicodedata
from thefuzz import process, fuzz
from .logger import setup_logger, log_user_action

logger = setup_logger(__name__)


def normalizar_texto(texto: str) -> str:
    """
    Elimina tildes y caracteres especiales para búsqueda
    
    Args:
        texto: String a normalizar
    
    Returns:
        String normalizado sin tildes
    """
    if not texto:
        return ""
    nfkd = unicodedata.normalize('NFD', texto)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)])


def buscar_jugadores_fuzzy(
    nombre: str, 
    temporada: int, 
    df_index: pd.DataFrame, 
    umbral_fuzzy: int = 70
) -> pd.DataFrame:
    """
    Búsqueda LOCAL ultra-rápida con tolerancia a errores (fuzzy matching)
    
    Args:
        nombre: Nombre a buscar
        temporada: Temporada objetivo
        df_index: DataFrame completo de jugadores
        umbral_fuzzy: Threshold de similitud (0-100)
    
    Returns:
        DataFrame con jugadores encontrados ordenados por relevancia
    """
    if df_index.empty or not nombre:
        return pd.DataFrame()
    
    log_user_action(logger, "buscar_jugador", {
        "nombre": nombre, 
        "temporada": temporada, 
        "umbral": umbral_fuzzy
    })
    
    # Filtrar por temporada primero
    from .database import get_players_by_season
    df_temp = get_players_by_season(temporada, df_index)
    
    if df_temp.empty:
        logger.warning(f"No hay jugadores en temporada {temporada}")
        return pd.DataFrame()
    
    # Normalizar término de búsqueda
    nombre_normalizado = normalizar_texto(nombre).upper()
    
    # PASO 1: Búsqueda exacta (substring)
    df_exacto = df_temp[
        df_temp['player_normalizado'].str.upper().str.contains(nombre_normalizado, na=False) |
        df_temp['player'].str.upper().str.contains(nombre.upper(), na=False)
    ].copy()
    
    if not df_exacto.empty:
        df_exacto['relevancia'] = 100
        logger.info(f"Búsqueda exacta | {len(df_exacto)} resultados | Query: '{nombre}'")
        return df_exacto.sort_values('rating_promedio', ascending=False).head(20)
    
    # PASO 2: Búsqueda fuzzy
    logger.info(f"Aplicando búsqueda fuzzy | Query: '{nombre}'")
    
    nombres_normalizados = df_temp['player_normalizado'].tolist()
    
    matches = process.extract(
        nombre_normalizado, 
        nombres_normalizados,
        scorer=fuzz.partial_ratio,
        limit=20
    )
    
    matches_validos = [(match, score, idx) for match, score, idx in matches if score >= umbral_fuzzy]
    
    if not matches_validos:
        logger.warning(f"Sin resultados fuzzy | Query: '{nombre}' | Umbral: {umbral_fuzzy}")
        return pd.DataFrame()
    
    indices = [idx for _, _, idx in matches_validos]
    scores = [score for _, score, _ in matches_validos]
    
    df_resultado = df_temp.iloc[indices].copy()
    df_resultado['relevancia'] = scores
    
    df_resultado = df_resultado.sort_values(
        ['relevancia', 'rating_promedio'], 
        ascending=[False, False]
    )
    
    logger.info(f"Búsqueda fuzzy exitosa | {len(df_resultado)} resultados | Mejor match: {df_resultado.iloc[0]['player']} ({scores[0]}%)")
    
    return df_resultado.head(20)


def format_player_label(row: pd.Series, include_relevancia: bool = False) -> str:
    """
    Formatea label de jugador para selectbox
    
    Args:
        row: Fila del DataFrame con datos del jugador
        include_relevancia: Si incluir score de relevancia
    
    Returns:
        String formateado para display
    """
    label = (
        f"{row['player']} | "
        f"{row['equipo_principal'][:12]} | "
        f"{row['posicion']} | "
        f"⭐{row['rating_promedio']:.1f} | "
        f"{int(row['partidos_jugados'])}P"
    )
    
    if include_relevancia and 'relevancia' in row and row['relevancia'] < 100:
        label = f"[{row['relevancia']:.0f}%] {label}"
    
    return label