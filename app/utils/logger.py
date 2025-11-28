import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name: str = "scouting_app", level: int = logging.INFO) -> logging.Logger:
    """
    Configura logger estructurado con formato consistente
    
    Args:
        name: Nombre del logger (generalmente __name__)
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Evitar duplicar handlers si ya existe
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Crear directorio de logs si no existe
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Formato estructurado
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola (solo WARNING+)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    
    # Handler para archivo (todos los niveles)
    log_file = log_dir / f"scouting_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def log_query_performance(logger: logging.Logger, query_name: str, duration: float, rows: int = None):
    """
    Log estandarizado para performance de queries
    
    Args:
        logger: Logger instance
        query_name: Nombre descriptivo de la query
        duration: Tiempo de ejecución en segundos
        rows: Número de filas retornadas (opcional)
    """
    msg = f"Query '{query_name}' ejecutada en {duration:.2f}s"
    if rows is not None:
        msg += f" | {rows} filas"
    
    if duration > 5:
        logger.warning(msg + " | ⚠️ Query lenta detectada")
    else:
        logger.info(msg)


def log_cache_event(logger: logging.Logger, event_type: str, key: str, hit: bool = None):
    """
    Log estandarizado para eventos de caché
    
    Args:
        logger: Logger instance
        event_type: 'hit', 'miss', 'refresh', 'clear'
        key: Identificador del caché
        hit: True si fue hit, False si miss (para type='access')
    """
    if event_type == "hit":
        logger.info(f"Cache HIT | {key}")
    elif event_type == "miss":
        logger.info(f"Cache MISS | {key} | Fetching from source")
    elif event_type == "refresh":
        logger.info(f"Cache REFRESH | {key}")
    elif event_type == "clear":
        logger.warning(f"Cache CLEAR | {key}")
    else:
        logger.debug(f"Cache {event_type.upper()} | {key}")


def log_user_action(logger: logging.Logger, action: str, details: dict = None):
    """
    Log estandarizado para acciones de usuario
    
    Args:
        logger: Logger instance
        action: Descripción de la acción
        details: Diccionario con contexto adicional
    """
    msg = f"User Action | {action}"
    if details:
        msg += f" | {details}"
    logger.info(msg)