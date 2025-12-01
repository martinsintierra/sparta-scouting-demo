from google.cloud import bigquery

# --- CONFIGURACIÓN ---
PROJECT_ID = "proyecto-scouting-futbol"
RAW_DATASET = "raw_scouting"
DWH_DATASET = "dwh_scouting"

def create_dwh_table(client, sql, target_table_id):
    job_config = bigquery.QueryJobConfig(
        destination=target_table_id,
        write_disposition='WRITE_TRUNCATE',
        
        # 🔹 PARTICIONAMIENTO: Divide tabla por fecha
        time_partitioning=bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="fecha",
            expiration_ms=None
        ),
        
        # 🔹 CLUSTERING: Ordena datos dentro de cada partición
        clustering_fields=["posicion_agrupada", "team"]
    )
    
    try:
        query_job = client.query(sql, job_config=job_config)
        query_job.result()
        table = client.get_table(target_table_id)
        print(f"✓ Tabla DWH '{target_table_id}' creada.")
        print(f"  - Filas: {table.num_rows:,}")
        print(f"  - Particionada por: fecha")
        print(f"  - Clustering: posicion_agrupada, team")
    except Exception as e:
        print(f"❌ Error creando '{target_table_id}': {e}")

if __name__ == '__main__':
    client = bigquery.Client(project=PROJECT_ID)
    dwh_table_id = f"{PROJECT_ID}.{DWH_DATASET}.partidos_procesados_pro"

    sql_partidos_procesados = f"""
        SELECT
            -- 1. CONTEXTO
            liga,
            CAST(REGEXP_EXTRACT(temporada, r'[0-9]{{4}}') AS INT64) AS temporada_anio,
            temporada as temporada_original,
            game_id,
            fecha, 
            
            TRIM(REPLACE(team, 'Club Atlético', '')) AS team,
            player_name as player,
            player_id,

            -- 2. PERFIL JUGADOR
            CASE
                WHEN position = 'G' THEN 'Arquero'
                WHEN position = 'D' THEN 'Defensor'
                WHEN position = 'M' THEN 'Mediocampista'
                WHEN position = 'F' THEN 'Delantero'
                ELSE 'Desconocido'
            END AS posicion_agrupada,
            position as posicion_original,
            is_substitute,
            
            -- Datos Físicos y Económicos
            country AS nacionalidad,
            height_cm as altura,
            age_at_match as edad_al_partido,
            market_value_euro as valor_mercado,
            contrato_vence,
            pie_preferido,

            -- 3. MÉTRICAS DE RENDIMIENTO
            minutes_played,
            rating,
            
            -- Ataque
            COALESCE(goals, 0) AS goals,
            COALESCE(assists, 0) AS assists,
            COALESCE(xG, 0) AS xG,
            COALESCE(xA, 0) AS xA,
            COALESCE(shots_total, 0) AS shots_total,
            COALESCE(shots_on_target, 0) AS shots_on_target,
            COALESCE(big_chances_created, 0) AS big_chances_created,
            COALESCE(dribbles_completed, 0) AS dribbles_completed,
            
            -- Construcción
            COALESCE(passes_acc, 0) AS passes_acc,
            COALESCE(key_passes, 0) AS key_passes,
            COALESCE(long_balls_acc, 0) AS long_balls_acc,
            COALESCE(crosses_acc, 0) AS crosses_acc,
            COALESCE(opp_half_passes_acc, 0) AS pases_progresivos,
            
            -- Defensa
            COALESCE(tackles_won, 0) AS tackles_won,
            COALESCE(interceptions, 0) AS interceptions,
            COALESCE(ball_recoveries, 0) as recuperaciones,
            COALESCE(clearances_total, 0) as clearances,
            COALESCE(blocked_shots, 0) as blocked_shots,
            
            -- Duelos
            COALESCE(duels_won, 0) AS duels_won,
            COALESCE(duels_total, 0) AS duels_total,
            COALESCE(aerial_won, 0) AS aerial_won,
            COALESCE(aerial_total, 0) AS aerial_total,
            
            -- Negativas
            COALESCE(possession_lost, 0) as perdidas_balon,
            COALESCE(fouls_committed, 0) as faltas_cometidas,
            COALESCE(errors_leading_to_shot, 0) as errors_leading_to_shot,
            
            -- ARQUEROS (AGREGADO)
            COALESCE(gk_saves, 0) as gk_saves,
            COALESCE(gk_saves_inside_box, 0) as gk_saves_inside_box,
            COALESCE(gk_high_claims, 0) as gk_high_claims,
            COALESCE(gk_crosses_not_claimed, 0) as gk_crosses_not_claimed,
            COALESCE(gk_punches, 0) as gk_punches,
            COALESCE(gk_sweeper_accurate, 0) as gk_sweeper_accurate,
            COALESCE(gk_sweeper_total, 0) as gk_sweeper_total,
            COALESCE(gk_penalty_save, 0) as gk_penalty_save

        FROM `{PROJECT_ID}.{RAW_DATASET}.jugadores_stats_raw`
        WHERE minutes_played > 0
    """

    print(f"Iniciando transformación completa hacia: {dwh_table_id}")
    print(f"  • Incluye métricas de arqueros")
    print(f"  • Incluye stats negativas")
    create_dwh_table(client, sql_partidos_procesados, dwh_table_id)