def crear_cliente_bigquery():
    """
    Crea cliente BigQuery con manejo robusto de credenciales.
    """
    print(f"\n🔧 Inicializando cliente BigQuery...")
    
    try:
        # Método 1: Cliente con proyecto explícito
        from google.auth import default
        credentials, project = default()
        
        if not project:
            project = PROJECT_ID
            
        client = bigquery.Client(
            project=PROJECT_ID,
            credentials=credentials
        )
        
        # Test simple para verificar que funciona
        client.query("SELECT 1 as test").result()
        
        print(f"   ✓ Cliente inicializado correctamente")
        print(f"   ✓ Proyecto: {PROJECT_ID}")
        return client
        
    except Exception as e:
        print(f"   ❌ Error al inicializar: {type(e).__name__}")
        print(f"   📋 Detalles: {str(e)[:200]}")
        print(f"\n💡 Soluciones posibles:")
        print(f"   1. gcloud auth application-default login")
        print(f"   2. gcloud config set project {PROJECT_ID}")
        sys.exit(1)

from google.cloud import bigquery
from google.cloud import storage
from datetime import datetime, timedelta
import sys
import os

# --- CONFIGURACIÓN ---
PROJECT_ID = "proyecto-scouting-futbol"
BUCKET_NAME = "bucket-scouting-futbol-raw-data"
RAW_DATASET = "raw_scouting"

# Forzar autenticación explícita si estamos en Cloud Shell
os.environ['GOOGLE_CLOUD_PROJECT'] = PROJECT_ID

# Schema COMPLETO: 93 columnas
SCHEMA_COMPLETO = [
    # === IDENTIFICADORES (12) ===
    bigquery.SchemaField("liga", "STRING"),
    bigquery.SchemaField("temporada", "STRING"),
    bigquery.SchemaField("game_id", "INTEGER"),
    bigquery.SchemaField("fecha", "DATE"),
    bigquery.SchemaField("team", "STRING"),
    bigquery.SchemaField("player_name", "STRING"),
    bigquery.SchemaField("player_slug", "STRING"),
    bigquery.SchemaField("player_short_name", "STRING"),
    bigquery.SchemaField("player_id", "INTEGER"),
    bigquery.SchemaField("position", "STRING"),
    bigquery.SchemaField("is_substitute", "BOOL"),
    bigquery.SchemaField("shirt_number", "FLOAT"),
    
    # === METADATA FÍSICA Y ECONÓMICA (7) ===
    bigquery.SchemaField("height_cm", "FLOAT"),
    bigquery.SchemaField("age_at_match", "FLOAT"),
    bigquery.SchemaField("market_value_euro", "FLOAT"),
    bigquery.SchemaField("country", "STRING"),
    bigquery.SchemaField("country_iso2", "STRING"),
    bigquery.SchemaField("country_iso3", "STRING"),
    bigquery.SchemaField("user_popularity", "INTEGER"),
    
    # === RENDIMIENTO GENERAL (4) ===
    bigquery.SchemaField("minutes_played", "INTEGER"),
    bigquery.SchemaField("rating", "FLOAT"),
    bigquery.SchemaField("rating_alt", "FLOAT"),
    bigquery.SchemaField("touches", "INTEGER"),
    
    # === PRODUCCIÓN OFENSIVA (7) ===
    bigquery.SchemaField("goals", "INTEGER"),
    bigquery.SchemaField("assists", "INTEGER"),
    bigquery.SchemaField("xG", "FLOAT"),
    bigquery.SchemaField("xA", "FLOAT"),
    bigquery.SchemaField("big_chances_created", "INTEGER"),
    bigquery.SchemaField("big_chances_missed", "INTEGER"),
    bigquery.SchemaField("own_goals", "INTEGER"),
    
    # === TIROS (5) ===
    bigquery.SchemaField("shots_total", "INTEGER"),
    bigquery.SchemaField("shots_on_target", "INTEGER"),
    bigquery.SchemaField("shots_off_target", "INTEGER"),
    bigquery.SchemaField("shots_blocked", "INTEGER"),
    bigquery.SchemaField("shot_acc_pct", "FLOAT"),
    
    # === PASES GENERALES (4) ===
    bigquery.SchemaField("passes_total", "INTEGER"),
    bigquery.SchemaField("passes_acc", "INTEGER"),
    bigquery.SchemaField("pass_acc_pct", "FLOAT"),
    bigquery.SchemaField("key_passes", "INTEGER"),
    
    # === PASES LARGOS (3) ===
    bigquery.SchemaField("long_balls_total", "INTEGER"),
    bigquery.SchemaField("long_balls_acc", "INTEGER"),
    bigquery.SchemaField("long_balls_acc_pct", "FLOAT"),
    
    # === CENTROS (3) ===
    bigquery.SchemaField("crosses_total", "INTEGER"),
    bigquery.SchemaField("crosses_acc", "INTEGER"),
    bigquery.SchemaField("cross_acc_pct", "FLOAT"),
    
    # === PROGRESIÓN (6) ===
    bigquery.SchemaField("opp_half_passes_total", "INTEGER"),
    bigquery.SchemaField("opp_half_passes_acc", "INTEGER"),
    bigquery.SchemaField("opp_half_acc_pct", "FLOAT"),
    bigquery.SchemaField("own_half_passes_total", "INTEGER"),
    bigquery.SchemaField("own_half_passes_acc", "INTEGER"),
    bigquery.SchemaField("own_half_acc_pct", "FLOAT"),
    
    # === REGATES (3) ===
    bigquery.SchemaField("dribbles_completed", "INTEGER"),
    bigquery.SchemaField("dribbles_attempted", "INTEGER"),
    bigquery.SchemaField("dribble_success_pct", "FLOAT"),
    
    # === DEFENSA (9) ===
    bigquery.SchemaField("tackles_total", "INTEGER"),
    bigquery.SchemaField("tackles_won", "INTEGER"),
    bigquery.SchemaField("tackle_success_pct", "FLOAT"),
    bigquery.SchemaField("interceptions", "INTEGER"),
    bigquery.SchemaField("ball_recoveries", "INTEGER"),
    bigquery.SchemaField("clearances_total", "INTEGER"),
    bigquery.SchemaField("clearances_off_line", "INTEGER"),
    bigquery.SchemaField("blocked_shots", "INTEGER"),
    bigquery.SchemaField("errors_leading_to_shot", "INTEGER"),
    bigquery.SchemaField("dribbled_past", "INTEGER"),
    
    # === DUELOS (8) ===
    bigquery.SchemaField("duels_total", "INTEGER"),
    bigquery.SchemaField("duels_won", "INTEGER"),
    bigquery.SchemaField("duels_lost", "INTEGER"),
    bigquery.SchemaField("duel_success_pct", "FLOAT"),
    bigquery.SchemaField("aerial_total", "INTEGER"),
    bigquery.SchemaField("aerial_won", "INTEGER"),
    bigquery.SchemaField("aerial_lost", "INTEGER"),
    bigquery.SchemaField("aerial_success_pct", "FLOAT"),
    
    # === CONTROL Y PÉRDIDAS (3) ===
    bigquery.SchemaField("possession_lost", "INTEGER"),
    bigquery.SchemaField("dispossessed", "INTEGER"),
    bigquery.SchemaField("bad_controls", "INTEGER"),
    
    # === FALTAS Y DISCIPLINA (3) ===
    bigquery.SchemaField("fouls_committed", "INTEGER"),
    bigquery.SchemaField("was_fouled", "INTEGER"),
    bigquery.SchemaField("offsides", "INTEGER"),
    
    # === PENALES (3) ===
    bigquery.SchemaField("penalties_won", "INTEGER"),
    bigquery.SchemaField("penalties_conceded", "INTEGER"),
    bigquery.SchemaField("penalty_miss", "INTEGER"),
    
    # === ARQUEROS (9) ===
    bigquery.SchemaField("gk_saves", "INTEGER"),
    bigquery.SchemaField("gk_saves_inside_box", "INTEGER"),
    bigquery.SchemaField("gk_high_claims", "INTEGER"),
    bigquery.SchemaField("gk_crosses_not_claimed", "INTEGER"),
    bigquery.SchemaField("gk_punches", "INTEGER"),
    bigquery.SchemaField("gk_sweeper_total", "INTEGER"),
    bigquery.SchemaField("gk_sweeper_accurate", "INTEGER"),
    bigquery.SchemaField("gk_sweeper_acc_pct", "FLOAT"),
    bigquery.SchemaField("gk_penalty_save", "INTEGER"),
    
    # === METADATA EXTRA (3) ===
    bigquery.SchemaField("pie_preferido", "STRING"),
    bigquery.SchemaField("contrato_vence", "DATE"),
    bigquery.SchemaField("posiciones_detalle", "STRING"),
]


def obtener_ultima_fecha_cargada(client, table_id):
    """
    Obtiene la fecha más reciente en la tabla para cargas incrementales.
    """
    print(f"\n🔍 Buscando última fecha cargada...")
    
    try:
        query = f"""
        SELECT MAX(fecha) as ultima_fecha
        FROM `{table_id}`
        """
        result = list(client.query(query).result())
        
        if result and result[0].ultima_fecha:
            ultima_fecha = result[0].ultima_fecha
            print(f"   ✓ Última fecha en tabla: {ultima_fecha}")
            return ultima_fecha
        else:
            print(f"   ℹ️ Tabla vacía - se hará carga completa")
            return None
            
    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            print(f"   ℹ️ Tabla no existe - se creará con carga completa")
            return None
        else:
            print(f"   ⚠️ Error al consultar: {type(e).__name__}")
            print(f"   ℹ️ Se asumirá carga completa")
            return None


def validar_csv_en_gcs(bucket_name, blob_name):
    """
    Verifica que el archivo existe en GCS antes de intentar cargarlo.
    """
    print(f"\n🔍 Validando archivo en GCS...")
    print(f"   URI: gs://{bucket_name}/{blob_name}")
    
    # Simplemente verificar con gsutil, sin parsear output
    import subprocess
    result = subprocess.run(
        ['gsutil', 'stat', f'gs://{bucket_name}/{blob_name}'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"   ✓ Archivo encontrado y accesible")
        return True
    else:
        print(f"   ⚠️ No se pudo verificar el archivo")
        print(f"   ℹ️ Continuando de todas formas (BigQuery lo validará)...")
        return True  # No bloqueamos la ejecución


def cargar_incremental(client, gcs_uri, table_id, schema, fecha_desde=None):
    """
    Carga incremental usando tabla temporal + MERGE.
    Solo procesa registros nuevos desde fecha_desde.
    """
    print(f"\n🔄 CARGA INCREMENTAL")
    print(f"   Desde fecha: {fecha_desde or 'INICIO'}")
    
    # 1. Crear tabla temporal
    temp_table_id = f"{table_id}_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"\n📥 Paso 1: Cargando a tabla temporal...")
    print(f"   Tabla temp: {temp_table_id}")
    
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        write_disposition='WRITE_TRUNCATE',
        max_bad_records=100,
        encoding='UTF-8',
        autodetect=False,
        allow_quoted_newlines=True,
    )
    
    try:
        # Cargar CSV a tabla temporal
        load_job = client.load_table_from_uri(gcs_uri, temp_table_id, job_config=job_config)
        print(f"   ⏳ Cargando datos temporales...")
        load_job.result()
        
        temp_table = client.get_table(temp_table_id)
        filas_temp = temp_table.num_rows
        print(f"   ✓ Cargadas {filas_temp:,} filas a tabla temporal")
        
        # 2. Construir query MERGE
        print(f"\n🔀 Paso 2: Ejecutando MERGE...")
        
        # Filtro de fecha si existe
        where_clause = ""
        if fecha_desde:
            where_clause = f"WHERE fecha > '{fecha_desde}'"
        
        # Generar lista de columnas para UPDATE
        columnas_update = []
        for field in schema:
            col = field.name
            # No actualizar claves primarias
            if col not in ['game_id', 'player_id', 'fecha']:
                columnas_update.append(f"T.{col} = S.{col}")
        
        update_set = ",\n        ".join(columnas_update)
        
        # Generar lista de columnas para INSERT
        columnas = [field.name for field in schema]
        columnas_str = ", ".join(columnas)
        valores_str = ", ".join([f"S.{col}" for col in columnas])
        
        merge_query = f"""
        MERGE `{table_id}` T
        USING (
            SELECT * FROM `{temp_table_id}`
            {where_clause}
        ) S
        ON T.game_id = S.game_id 
           AND T.player_id = S.player_id 
           AND T.fecha = S.fecha
        WHEN MATCHED THEN
            UPDATE SET
                {update_set}
        WHEN NOT MATCHED THEN
            INSERT ({columnas_str})
            VALUES ({valores_str})
        """
        
        # Ejecutar MERGE
        merge_job = client.query(merge_query)
        merge_result = merge_job.result()
        
        # Obtener estadísticas del MERGE
        stats = merge_job._properties.get('statistics', {}).get('dml_stats', {})
        filas_insertadas = stats.get('inserted_row_count', 0)
        filas_actualizadas = stats.get('updated_row_count', 0)
        
        print(f"   ✓ MERGE completado:")
        print(f"      • Insertadas: {filas_insertadas:,} filas nuevas")
        print(f"      • Actualizadas: {filas_actualizadas:,} filas existentes")
        
        # 3. Limpiar tabla temporal
        print(f"\n🧹 Paso 3: Limpiando tabla temporal...")
        client.delete_table(temp_table_id)
        print(f"   ✓ Tabla temporal eliminada")
        
        # 4. Verificar resultado final
        tabla_final = client.get_table(table_id)
        print(f"\n✅ CARGA INCREMENTAL COMPLETADA")
        print(f"   Total filas en tabla: {tabla_final.num_rows:,}")
        print(f"   Tamaño tabla: {tabla_final.num_bytes / (1024*1024):.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR en carga incremental:")
        print(f"   {str(e)}")
        
        # Intentar limpiar tabla temporal
        try:
            client.delete_table(temp_table_id, not_found_ok=True)
            print(f"   ✓ Tabla temporal limpiada")
        except:
            pass
        
        return False


def cargar_completo(client, gcs_uri, table_id, schema):
    """
    Carga completa (WRITE_TRUNCATE) - solo para primera vez.
    """
    print(f"\n🚀 CARGA COMPLETA (primera vez)")
    print(f"   Origen: {gcs_uri}")
    print(f"   Destino: {table_id}")
    
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        write_disposition='WRITE_TRUNCATE',
        max_bad_records=100,
        encoding='UTF-8',
        autodetect=False,
        allow_quoted_newlines=True,
    )
    
    try:
        load_job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
        print(f"   ⏳ Esperando carga...")
        load_job.result()
        
        table = client.get_table(table_id)
        
        print(f"\n✅ CARGA COMPLETA FINALIZADA")
        print(f"   Filas cargadas: {table.num_rows:,}")
        print(f"   Tamaño: {table.num_bytes / (1024*1024):.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR en carga completa:")
        print(f"   {str(e)}")
        return False


def mostrar_resumen_datos(client, table_id):
    """
    Muestra resumen de datos cargados.
    """
    print(f"\n📊 RESUMEN DE DATOS:")
    
    query = f"""
    SELECT 
        MIN(fecha) as fecha_min,
        MAX(fecha) as fecha_max,
        COUNT(DISTINCT player_id) as jugadores_unicos,
        COUNT(DISTINCT game_id) as partidos_unicos,
        COUNT(*) as total_registros
    FROM `{table_id}`
    """
    
    result = list(client.query(query).result())[0]
    
    print(f"   • Período: {result.fecha_min} a {result.fecha_max}")
    print(f"   • Jugadores únicos: {result.jugadores_unicos:,}")
    print(f"   • Partidos únicos: {result.partidos_unicos:,}")
    print(f"   • Total registros: {result.total_registros:,}")
    
    # Top 5 goleadores
    print(f"\n🎯 Top 5 Goleadores (promedio por partido):")
    query_top = f"""
    SELECT 
        player_name,
        position,
        COUNT(*) as partidos,
        SUM(goals) as goles_total,
        ROUND(AVG(xG), 2) as xG_promedio
    FROM `{table_id}`
    WHERE minutes_played >= 45
    GROUP BY player_name, position
    HAVING partidos >= 10
    ORDER BY xG_promedio DESC
    LIMIT 5
    """
    
    for i, row in enumerate(client.query(query_top).result(), 1):
        print(f"   {i}. {row.player_name} ({row.position})")
        print(f"      {row.partidos} partidos | {row.goles_total} goles | xG: {row.xG_promedio}")


def main():
    print("="*70)
    print("  CARGA A BIGQUERY - FÚTBOL ARGENTINO 2021-2025")
    print("  Modo: CARGA INCREMENTAL INTELIGENTE")
    print("="*70)
    
    # Configuración
    blob_path = "data/futbol_argentino_2021_2025_COMPLETO_BQ.csv"
    table_id = f"{PROJECT_ID}.{RAW_DATASET}.jugadores_stats_raw"
    gcs_uri = f"gs://{BUCKET_NAME}/{blob_path}"
    
    print(f"\n📂 Archivo a cargar: {gcs_uri}")
    print(f"📊 Destino: {table_id}")
    
    # 1. Validar archivo en GCS (no bloqueante)
    validar_csv_en_gcs(BUCKET_NAME, blob_path)
    
    # 2. Inicializar cliente BigQuery con método robusto
    client = crear_cliente_bigquery()
    
    # 3. Determinar tipo de carga (incremental vs completa)
    ultima_fecha = obtener_ultima_fecha_cargada(client, table_id)
    
    print(f"\n{'='*70}")
    
    if ultima_fecha:
        # CARGA INCREMENTAL
        print(f"  Modo: INCREMENTAL (desde {ultima_fecha})")
        exito = cargar_incremental(client, gcs_uri, table_id, SCHEMA_COMPLETO, ultima_fecha)
    else:
        # CARGA COMPLETA (primera vez)
        print(f"  Modo: COMPLETA (primera carga)")
        exito = cargar_completo(client, gcs_uri, table_id, SCHEMA_COMPLETO)
    
    print(f"{'='*70}")
    
    # 4. Mostrar resumen si fue exitoso
    if exito:
        mostrar_resumen_datos(client, table_id)
        
        print(f"\n{'='*70}")
        print(f"  🎉 PROCESO COMPLETADO EXITOSAMENTE")
        print(f"{'='*70}")
        print(f"\n💡 Próximas ejecuciones serán INCREMENTALES")
        print(f"   Solo se procesarán datos nuevos desde {datetime.now().date()}")
    else:
        print(f"\n{'='*70}")
        print(f"  ⚠️ PROCESO FINALIZADO CON ERRORES")
        print(f"{'='*70}")
        sys.exit(1)


if __name__ == '__main__':
    main()