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
            game_id,
            fecha,
            
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
            
            -- OFENSIVAS
            goals, assists, xG, xA,
            shots_on_target, key_passes, dribbles_completed,
            
            -- CONSTRUCCIÓN
            pases_progresivos, passes_acc, long_balls_acc, crosses_acc,
            
            -- DEFENSIVAS
            tackles_won, interceptions, recuperaciones, clearances,
            blocked_shots, duels_won, aerial_won,
            
            -- NEGATIVAS
            errors_leading_to_shot, perdidas_balon,
            
            -- ARQUEROS
            COALESCE(gk_saves, 0) as gk_saves,
            COALESCE(gk_saves_inside_box, 0) as gk_saves_inside_box,
            COALESCE(gk_high_claims, 0) as gk_high_claims,
            COALESCE(gk_crosses_not_claimed, 0) as gk_crosses_not_claimed,
            COALESCE(gk_punches, 0) as gk_punches,
            COALESCE(gk_sweeper_accurate, 0) as gk_sweeper_accurate,
            COALESCE(gk_sweeper_total, 0) as gk_sweeper_total,
            COALESCE(gk_penalty_save, 0) as gk_penalty_save,
            
            -- Para clean sheets
            CASE WHEN goals = 0 THEN 1 ELSE 0 END as clean_sheet,
            
            -- Contadores
            ROW_NUMBER() OVER (
                PARTITION BY player_id, temporada_anio, team 
                ORDER BY fecha DESC
            ) as rn_equipo
            
        FROM `{PROJECT_ID}.{DWH_DATASET}.partidos_procesados_pro`
    ),
    
    EquipoPrincipal AS (
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
            
            -- Dimensiones
            ANY_VALUE(s.posicion_agrupada) as posicion,
            ANY_VALUE(s.nacionalidad) as nacionalidad,
            ANY_VALUE(s.altura) as altura,
            ANY_VALUE(s.pie_preferido) as pie,
            
            MAX(ep.equipo_principal) as equipo_principal,
            MAX(s.valor_mercado) as valor_mercado,
            MAX(s.contrato_vence) as contrato_vence,
            AVG(s.edad_al_partido) as edad_promedio,
            
            -- Totales generales
            SUM(s.minutes_played) as total_minutos,
            COUNT(DISTINCT s.game_id) as partidos_jugados,
            AVG(s.rating) as rating_promedio,
            
            -- ARQUEROS - Totales
            SUM(s.gk_saves) as sum_gk_saves,
            SUM(s.gk_saves_inside_box) as sum_gk_saves_inside_box,
            SUM(s.gk_high_claims) as sum_gk_high_claims,
            SUM(s.gk_crosses_not_claimed) as sum_gk_crosses_not_claimed,
            SUM(s.gk_punches) as sum_gk_punches,
            SUM(s.gk_sweeper_accurate) as sum_gk_sweeper_accurate,
            SUM(s.gk_sweeper_total) as sum_gk_sweeper_total,
            SUM(s.gk_penalty_save) as sum_gk_penalty_save,
            SUM(s.clean_sheet) as sum_clean_sheets,
            SUM(s.passes_acc) as sum_passes,
            SUM(s.long_balls_acc) as sum_long_balls,
            
            -- OFENSIVAS - Totales
            SUM(s.goals) as sum_goals,
            SUM(s.assists) as sum_assists,
            SUM(s.xG) as sum_xG,
            SUM(s.xA) as sum_xA,
            SUM(s.shots_on_target) as sum_shots_target,
            SUM(s.key_passes) as sum_key_passes,
            SUM(s.dribbles_completed) as sum_dribbles,
            
            -- CONSTRUCCIÓN - Totales
            SUM(s.pases_progresivos) as sum_prog_passes,
            
            -- DEFENSIVAS - Totales
            SUM(s.tackles_won) as sum_tackles,
            SUM(s.interceptions) as sum_interceptions,
            SUM(s.recuperaciones) as sum_recoveries,
            SUM(s.duels_won) as sum_duels_won,
            SUM(s.aerial_won) as sum_aerial_won,
            SUM(s.clearances) as sum_clearances,
            SUM(s.blocked_shots) as sum_blocks,
            
            -- NEGATIVAS - Totales
            SUM(s.errors_leading_to_shot) as sum_errors,
            SUM(s.perdidas_balon) as sum_dispossessed
            
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
            
            -- ============================================
            -- MÉTRICAS PER 90 MINUTOS
            -- ============================================
            
            -- OFENSIVAS
            SAFE_DIVIDE(sum_goals * 90, total_minutos) as goals_p90,
            SAFE_DIVIDE(sum_assists * 90, total_minutos) as assists_p90,
            SAFE_DIVIDE(sum_xG * 90, total_minutos) as xG_p90,
            SAFE_DIVIDE(sum_xA * 90, total_minutos) as xA_p90,
            SAFE_DIVIDE(sum_key_passes * 90, total_minutos) as key_passes_p90,
            SAFE_DIVIDE(sum_dribbles * 90, total_minutos) as dribbles_p90,
            SAFE_DIVIDE(sum_shots_target * 90, total_minutos) as shots_target_p90,
            
            -- CONSTRUCCIÓN
            SAFE_DIVIDE(sum_prog_passes * 90, total_minutos) as prog_passes_p90,
            SAFE_DIVIDE(sum_passes * 90, total_minutos) as passes_p90,
            SAFE_DIVIDE(sum_long_balls * 90, total_minutos) as long_balls_p90,
            
            -- DEFENSIVAS
            SAFE_DIVIDE(sum_tackles * 90, total_minutos) as tackles_p90,
            SAFE_DIVIDE(sum_interceptions * 90, total_minutos) as interceptions_p90,
            SAFE_DIVIDE(sum_recoveries * 90, total_minutos) as recoveries_p90,
            SAFE_DIVIDE(sum_aerial_won * 90, total_minutos) as aerial_won_p90,
            SAFE_DIVIDE(sum_clearances * 90, total_minutos) as clearances_p90,
            SAFE_DIVIDE(sum_blocks * 90, total_minutos) as blocks_p90,
            
            -- NEGATIVAS
            SAFE_DIVIDE(sum_errors * 90, total_minutos) as errors_p90,
            SAFE_DIVIDE(sum_dispossessed * 90, total_minutos) as dispossessed_p90,
            
            -- ============================================
            -- ARQUEROS - Per 90 (NOMBRES COMPATIBLES ML)
            -- ============================================
            SAFE_DIVIDE(sum_gk_saves * 90, total_minutos) as saves_p90,
            SAFE_DIVIDE(sum_gk_high_claims * 90, total_minutos) as claims_p90,
            SAFE_DIVIDE(sum_gk_punches * 90, total_minutos) as punches_p90,
            SAFE_DIVIDE(sum_gk_sweeper_total * 90, total_minutos) as sweeper_p90,
            
            -- ============================================
            -- ARQUEROS - Porcentajes
            -- ============================================
            
            -- Save % (paradas / paradas + goles recibidos)
            SAFE_DIVIDE(
                sum_gk_saves, 
                NULLIF(sum_gk_saves + sum_goals, 0)
            ) * 100 as saves_pct,
            
            -- Clean Sheets %
            SAFE_DIVIDE(sum_clean_sheets, NULLIF(partidos_jugados, 0)) * 100 as clean_sheets_pct,
            
            -- Sweeper Accuracy %
            SAFE_DIVIDE(
                sum_gk_sweeper_accurate, 
                NULLIF(sum_gk_sweeper_total, 0)
            ) * 100 as sweeper_acc_pct,
            
            -- ============================================
            -- RATIOS ADICIONALES
            -- ============================================
            SAFE_DIVIDE(sum_shots_target, NULLIF(sum_goals, 0)) as shots_per_goal
            
        FROM StatsAgregadas
    )

    SELECT
        -- IDs y dimensiones
        player_id,
        player,
        temporada_anio,
        posicion,
        equipo_principal,
        nacionalidad,
        altura,
        pie,
        valor_mercado,
        contrato_vence,
        edad_promedio,
        
        -- Totales
        total_minutos,
        partidos_jugados,
        rating_promedio,
        
        -- Sumas
        sum_goals,
        sum_assists,
        sum_xG,
        sum_xA,
        sum_shots_target,
        sum_key_passes,
        sum_dribbles,
        sum_prog_passes,
        sum_tackles,
        sum_interceptions,
        sum_recoveries,
        sum_aerial_won,
        sum_clearances,
        sum_blocks,
        sum_errors,
        sum_dispossessed,
        
        -- Per 90
        goals_p90,
        assists_p90,
        xG_p90,
        xA_p90,
        key_passes_p90,
        dribbles_p90,
        shots_target_p90,
        prog_passes_p90,
        passes_p90,
        long_balls_p90,
        tackles_p90,
        interceptions_p90,
        recoveries_p90,
        aerial_won_p90,
        clearances_p90,
        blocks_p90,
        errors_p90,
        dispossessed_p90,
        
        -- Arqueros (nombres compatibles con ML)
        saves_p90,
        saves_pct,
        clean_sheets_pct,
        sweeper_p90,
        sweeper_acc_pct,
        claims_p90,
        punches_p90,
        
        -- Ratios
        shots_per_goal,
        
        -- ============================================
        -- PERCENTILES POR POSICIÓN
        -- ============================================
        PERCENT_RANK() OVER (
            PARTITION BY temporada_anio, posicion 
            ORDER BY rating_promedio
        ) as pct_rating,
        
        -- Ofensivos (excluir arqueros)
        CASE WHEN posicion != 'Arquero' 
            THEN PERCENT_RANK() OVER (
                PARTITION BY temporada_anio, posicion 
                ORDER BY xG_p90
            ) 
        END as pct_xG,
        
        PERCENT_RANK() OVER (
            PARTITION BY temporada_anio, posicion 
            ORDER BY xA_p90
        ) as pct_xA,
        
        PERCENT_RANK() OVER (
            PARTITION BY temporada_anio, posicion 
            ORDER BY prog_passes_p90
        ) as pct_prog_passes,
        
        PERCENT_RANK() OVER (
            PARTITION BY temporada_anio, posicion 
            ORDER BY dribbles_p90
        ) as pct_dribbles,
        
        -- Defensivos (todas las posiciones)
        PERCENT_RANK() OVER (
            PARTITION BY temporada_anio, posicion 
            ORDER BY recoveries_p90
        ) as pct_recoveries,
        
        PERCENT_RANK() OVER (
            PARTITION BY temporada_anio, posicion 
            ORDER BY aerial_won_p90
        ) as pct_aerial,
        
        -- Arqueros específicos
        CASE WHEN posicion = 'Arquero'
            THEN PERCENT_RANK() OVER (
                PARTITION BY temporada_anio, posicion 
                ORDER BY saves_p90
            )
        END as pct_saves,
        
        CASE WHEN posicion = 'Arquero'
            THEN PERCENT_RANK() OVER (
                PARTITION BY temporada_anio, posicion 
                ORDER BY saves_pct
            )
        END as pct_saves_pct,
        
        CASE WHEN posicion = 'Arquero'
            THEN PERCENT_RANK() OVER (
                PARTITION BY temporada_anio, posicion 
                ORDER BY clean_sheets_pct
            )
        END as pct_clean_sheets,
        
        CASE WHEN posicion = 'Arquero'
            THEN PERCENT_RANK() OVER (
                PARTITION BY temporada_anio, posicion 
                ORDER BY sweeper_p90
            )
        END as pct_sweeper

    FROM MetricsP90
    """

    print(f"Generando Datamart PRO con features para todas las posiciones...")
    create_datamart_table(client, sql_datamart, target_table)
    print(f"\n✅ Datamart compatible con modelo ML")
    print(f"   • Arqueros: saves_p90, saves_pct, clean_sheets_pct, sweeper_p90, claims_p90, punches_p90")
    print(f"   • Defensores: tackles_p90, clearances_p90, aerial_won_p90, blocks_p90")
    print(f"   • Mediocampistas: prog_passes_p90, key_passes_p90, recoveries_p90")
    print(f"   • Delanteros: xG_p90, xA_p90, goals_p90, dribbles_p90")