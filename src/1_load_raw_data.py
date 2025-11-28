from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# --- CONFIGURACIÓN ---
# Asegúrate de que este sea el ID de tu proyecto
PROJECT_ID = "proyecto-scouting-futbol"
# El nombre del bucket que creaste
BUCKET_NAME = "bucket-scouting-futbol-raw-data" 
# El dataset de destino en BigQuery
RAW_DATASET = "raw_scouting"

# ESQUEMA CORREGIDO FINAL
MANUAL_SCHEMA = [
    bigquery.SchemaField("liga", "STRING"),
    bigquery.SchemaField("temporada", "STRING"),
    bigquery.SchemaField("game_id", "INTEGER"),
    bigquery.SchemaField("fecha", "DATE"),
    bigquery.SchemaField("team", "STRING"),
    bigquery.SchemaField("player", "STRING"),
    bigquery.SchemaField("player_id", "INTEGER"),
    bigquery.SchemaField("position", "STRING"),
    bigquery.SchemaField("rating", "FLOAT"),
    bigquery.SchemaField("minutes_played", "INTEGER"),
    bigquery.SchemaField("goals", "INTEGER"),
    bigquery.SchemaField("assists", "INTEGER"),
    bigquery.SchemaField("shots_total", "INTEGER"),
    bigquery.SchemaField("shots_on_target", "INTEGER"),
    bigquery.SchemaField("passes_total", "INTEGER"),
    bigquery.SchemaField("passes_accurate", "INTEGER"),
    bigquery.SchemaField("pass_accuracy_percent", "FLOAT"), # Correcto, es FLOAT
    bigquery.SchemaField("key_passes", "INTEGER"),
    bigquery.SchemaField("tackles", "INTEGER"),
    bigquery.SchemaField("interceptions", "INTEGER"),
    bigquery.SchemaField("clearances", "INTEGER"),
    bigquery.SchemaField("blocked_shots", "INTEGER"),
    bigquery.SchemaField("duels_won", "INTEGER"),
    bigquery.SchemaField("duels_total", "INTEGER"),
    bigquery.SchemaField("duel_success_percent", "FLOAT"), # Correcto, es FLOAT
    bigquery.SchemaField("aerial_duels_won", "INTEGER"),
    
    # --- POSIBLE PUNTO DE ERROR ---
    # La columna 'dribbles_successful' en tu glimpse tiene 0.
    # El log de error muestra valores como '0.0', '60.0', etc. que son decimales.
    # La renombramos y la cambiamos a FLOAT para estar seguros.
    bigquery.SchemaField("dribbles_successful", "FLOAT"),
    
    bigquery.SchemaField("fouls_committed", "INTEGER"),
    bigquery.SchemaField("was_fouled", "INTEGER"),
    bigquery.SchemaField("edad", "FLOAT"),
    bigquery.SchemaField("fecha_nacimiento", "STRING"), # Cambiado a STRING
    bigquery.SchemaField("nacionalidad", "STRING"),
    bigquery.SchemaField("altura_cm", "FLOAT"),
    bigquery.SchemaField("pie_preferido", "STRING"),
    bigquery.SchemaField("valor_mercado_eur", "FLOAT"), 
    bigquery.SchemaField("contrato_vence", "STRING"), # Fechas siempre STRING en capa RAW
    bigquery.SchemaField("posiciones_detalle", "STRING") 
]

def load_csv_from_gcs(client, gcs_uri, table_id, schema):
    job_config = bigquery.LoadJobConfig(
        # =============== INICIO DE LA SOLUCIÓN ===============
        # Usamos nuestro esquema manual en lugar de autodetect
        schema=schema,
        # =============== FIN DE LA SOLUCIÓN ===============
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        write_disposition='WRITE_TRUNCATE',
        # Permitimos algunos errores por si alguna fila del CSV tiene más columnas de las esperadas
        allow_jagged_rows=True,
    )

    try:
        print(f"Iniciando carga desde '{gcs_uri}' hacia '{table_id}'...")
        load_job = client.load_table_from_uri(
            gcs_uri,
            table_id,
            job_config=job_config
        )
        
        load_job.result()  # Espera a que el trabajo termine
        
        table = client.get_table(table_id)
        print(f"✓ Carga completada. Se cargaron {table.num_rows} filas en la tabla '{table_id}'.")

    except Exception as e:
        print(f"❌ Error al cargar la tabla '{table_id}': {e}")


if __name__ == '__main__':
    client = bigquery.Client(project=PROJECT_ID)

    # --- Carga de la Tabla de Liga Profesional ---
    liga_profesional_uri = f"gs://{BUCKET_NAME}/data/futbol_argentino_2021_2025_COMPLETO.csv"
    liga_profesional_table_id = f"{PROJECT_ID}.{RAW_DATASET}.liga_profesional_raw"
    load_csv_from_gcs(client, liga_profesional_uri, liga_profesional_table_id, MANUAL_SCHEMA)

    # =============== FIN DE LA SOLUCIÓN ===============

    print("\nProceso de carga a la capa RAW finalizado.")