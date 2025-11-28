from google.cloud import bigquery

PROJECT_ID = "proyecto-scouting-futbol"
DWH_DATASET = "dwh_scouting"
DM_DATASET = "dm_scouting"

def create_datamart_table(client, sql, target_table_id):
    job_config = bigquery.QueryJobConfig(
        destination=target_table_id,
        write_disposition='WRITE_TRUNCATE'
    )
    try:
        query_job = client.query(sql, job_config=job_config)
        query_job.result()
        table = client.get_table(target_table_id)
        print(f"✓ Datamart PRO Generado. Filas: {table.num_rows}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    client = bigquery.Client(project=PROJECT_ID)
    target_table = f"{PROJECT_ID}.{DM_DATASET}.stats_jugador_temporada_pro"

    sql_datamart = f"""
    WITH StatsBase AS (
        SELECT
            player_id,
            player,
            temporada_anio,
            game_id,  -- AÑADIDO: Necesario para COUNT DISTINCT
            fecha,    -- AÑADIDO: Necesario para ROW_NUMBER
            
            -- Dimensiones
            posicion_agrupada,
            team,
            nacionalidad,
            altura,
            pie_preferido,
            valor_mercado,
            contrato_vence,
            edad_al_partido,
            
            -- Métricas por partido
            minutes_played,
            rating,
            goals,
            assists,
            xG,
            xA,
            shots_on_target,
            key_passes,
            dribbles_completed,
            pases_progresivos,
            tackles_won,
            interceptions,
            recuperaciones,
            duels_won,
            aerial_won,
            clearances,
            
            -- Contadores para frecuencia
            ROW_NUMBER() OVER (
                PARTITION BY player_id, temporada_anio, team 
                ORDER BY fecha DESC
            ) as rn_equipo
            
        FROM `{PROJECT_ID}.{DWH_DATASET}.partidos_procesados_pro`
    ),
    
    EquipoPrincipal AS (
        -- Extraer el equipo más reciente (último partido jugado)
        SELECT
            player_id,
            temporada_anio,
            team as equipo_principal
        FROM StatsBase
        WHERE rn_equipo = 1
    ),
    
    StatsAgregadas AS (
        SELECT
            s.player_id,
            s.player,
            s.temporada_anio,
            
            -- Dimensiones (tomar ANY_VALUE es seguro para altura, país, pie)
            ANY_VALUE(s.posicion_agrupada) as posicion,
            ANY_VALUE(s.nacionalidad) as nacionalidad,
            ANY_VALUE(s.altura) as altura,
            ANY_VALUE(s.pie_preferido) as pie,
            
            -- Equipo principal (último partido)
            MAX(ep.equipo_principal) as equipo_principal,
            
            -- Valor máximo de mercado en la temporada
            MAX(s.valor_mercado) as valor_mercado,
            MAX(s.contrato_vence) as contrato_vence,
            AVG(s.edad_al_partido) as edad_promedio,
            
            -- Totales
            SUM(s.minutes_played) as total_minutos,
            COUNT(DISTINCT s.game_id) as partidos_jugados,
            AVG(s.rating) as rating_promedio,
            
            -- Sumas
            SUM(s.goals) as sum_goals,
            SUM(s.assists) as sum_assists,
            SUM(s.xG) as sum_xG,
            SUM(s.xA) as sum_xA,
            SUM(s.shots_on_target) as sum_shots_target,
            SUM(s.key_passes) as sum_key_passes,
            SUM(s.dribbles_completed) as sum_dribbles,
            SUM(s.pases_progresivos) as sum_prog_passes,
            SUM(s.tackles_won) as sum_tackles,
            SUM(s.interceptions) as sum_interceptions,
            SUM(s.recuperaciones) as sum_recoveries,
            SUM(s.duels_won) as sum_duels_won,
            SUM(s.aerial_won) as sum_aerial_won,
            SUM(s.clearances) as sum_clearances
            
        FROM StatsBase s
        LEFT JOIN EquipoPrincipal ep 
            ON s.player_id = ep.player_id 
            AND s.temporada_anio = ep.temporada_anio
        GROUP BY s.player_id, s.player, s.temporada_anio
        HAVING total_minutos > 300
    ),

    MetricsP90 AS (
        SELECT
            *,
            -- Per 90 minutos
            SAFE_DIVIDE(sum_goals * 90, total_minutos) as goals_p90,
            SAFE_DIVIDE(sum_assists * 90, total_minutos) as assists_p90,
            SAFE_DIVIDE(sum_xG * 90, total_minutos) as xG_p90,
            SAFE_DIVIDE(sum_xA * 90, total_minutos) as xA_p90,
            SAFE_DIVIDE(sum_key_passes * 90, total_minutos) as key_passes_p90,
            SAFE_DIVIDE(sum_dribbles * 90, total_minutos) as dribbles_p90,
            SAFE_DIVIDE(sum_prog_passes * 90, total_minutos) as prog_passes_p90,
            SAFE_DIVIDE(sum_tackles * 90, total_minutos) as tackles_p90,
            SAFE_DIVIDE(sum_interceptions * 90, total_minutos) as interceptions_p90,
            SAFE_DIVIDE(sum_recoveries * 90, total_minutos) as recoveries_p90,
            SAFE_DIVIDE(sum_aerial_won * 90, total_minutos) as aerial_won_p90,
            SAFE_DIVIDE(sum_clearances * 90, total_minutos) as clearances_p90,
            
            -- Ratios de eficiencia
            SAFE_DIVIDE(sum_shots_target, NULLIF(sum_goals, 0)) as shots_per_goal
        FROM StatsAgregadas
    )

    SELECT
        *,
        -- Percentiles por posición y temporada
        PERCENT_RANK() OVER (PARTITION BY temporada_anio, posicion ORDER BY rating_promedio) as pct_rating,
        PERCENT_RANK() OVER (PARTITION BY temporada_anio, posicion ORDER BY xG_p90) as pct_xG,
        PERCENT_RANK() OVER (PARTITION BY temporada_anio, posicion ORDER BY xA_p90) as pct_xA,
        PERCENT_RANK() OVER (PARTITION BY temporada_anio, posicion ORDER BY prog_passes_p90) as pct_prog_passes,
        PERCENT_RANK() OVER (PARTITION BY temporada_anio, posicion ORDER BY dribbles_p90) as pct_dribbles,
        PERCENT_RANK() OVER (PARTITION BY temporada_anio, posicion ORDER BY recoveries_p90) as pct_recoveries,
        PERCENT_RANK() OVER (PARTITION BY temporada_anio, posicion ORDER BY aerial_won_p90) as pct_aerial
    FROM MetricsP90
    """

    print(f"Generando Datamart PRO (xG, xA, Valor, Contrato)...")
    create_datamart_table(client, sql_datamart, target_table)