"""
VISTA UNIFICADA PARA DASHBOARD - VERSION COMPLETA
Consolida: Stats Base + Similitudes + Proyecciones + Arquetipos
CORREGIDO: Incluye TODOS los percentiles disponibles
"""

from google.cloud import bigquery

PROJECT_ID = "proyecto-scouting-futbol"
DM_DATASET = "dm_scouting"
CLIENT = bigquery.Client(project=PROJECT_ID)

sql_view = f"""
CREATE OR REPLACE VIEW `{PROJECT_ID}.{DM_DATASET}.v_dashboard_scouting_completo` AS

WITH BaseStats AS (
    -- Stats principales de cada jugador
    SELECT
        player_id,
        player,
        temporada_anio,
        posicion,
        equipo_principal,
        nacionalidad,
        edad_promedio,
        valor_mercado,
        altura,
        pie,
        contrato_vence,
        total_minutos,
        partidos_jugados,
        
        -- Stats P90
        rating_promedio,
        goals_p90,
        assists_p90,
        xG_p90,
        xA_p90,
        prog_passes_p90,
        key_passes_p90,
        dribbles_p90,
        recoveries_p90,
        tackles_p90,
        interceptions_p90,
        aerial_won_p90,
        clearances_p90,
        blocks_p90,
        errors_p90,
        dispossessed_p90,
        
        -- Percentiles GENERALES (todas las posiciones)
        pct_rating,
        pct_xA,
        pct_prog_passes,
        pct_dribbles,
        pct_recoveries,
        pct_aerial,
        
        -- Percentiles OFENSIVOS (excluye arqueros - puede ser NULL)
        pct_xG,
        
        -- Percentiles DEFENSIVOS (todas las posiciones)
        -- ✅ AGREGADOS EN DATAMART v2:
        pct_tackles,
        pct_interceptions,
        pct_clearances,
        pct_blocks,
        
        -- Arqueros - P90
        saves_p90,
        claims_p90,
        punches_p90,
        sweeper_p90,
        
        -- Arqueros - Porcentajes
        saves_pct,
        clean_sheets_pct,
        sweeper_acc_pct,
        
        -- Percentiles ARQUEROS (solo para posicion = 'Arquero')
        pct_saves,
        pct_saves_pct,
        pct_clean_sheets,
        pct_sweeper
        
    FROM `{PROJECT_ID}.{DM_DATASET}.stats_jugador_temporada_pro`
),

Similitudes AS (
    -- Top 5 similares por jugador
    SELECT
        jugador_origen_id,
        temporada_origen,
        
        ARRAY_AGG(
            STRUCT(
                jugador_similar_id,
                jugador_similar as nombre,
                equipo_similar as equipo,
                score_similitud,
                valor_mercado_similar / 1000000 as valor_millones,
                edad_similar as edad,
                rank_similitud
            )
            ORDER BY rank_similitud
            LIMIT 5
        ) as similares_top5
        
    FROM `{PROJECT_ID}.{DM_DATASET}.scouting_similitud_pro_v2`
    GROUP BY jugador_origen_id, temporada_origen
),

Proyecciones AS (
    -- Proyecciones de valor futuro
    SELECT
        player_id,
        valor_proyectado_1y,
        delta_proyectado_pct
    FROM `{PROJECT_ID}.{DM_DATASET}.proyecciones_valor`
),

Arquetipos AS (
    -- Cluster y arquetipo
    SELECT
        player_id,
        cluster as arquetipo_id,
        arquetipo_nombre
    FROM `{PROJECT_ID}.{DM_DATASET}.arquetipos_jugadores`
)

-- QUERY PRINCIPAL
SELECT
    -- Identificación
    bs.player_id,
    bs.player as nombre_jugador,
    bs.temporada_anio,
    
    -- Perfil
    bs.posicion,
    bs.equipo_principal,
    bs.nacionalidad,
    bs.edad_promedio,
    bs.altura,
    bs.pie,
    bs.contrato_vence,
    
    -- Valor y Actividad
    bs.valor_mercado,
    bs.valor_mercado / 1000000 as valor_millones,
    bs.total_minutos,
    bs.partidos_jugados,
    
    -- =========================================
    -- STATS P90 (VALORES ABSOLUTOS)
    -- =========================================
    bs.rating_promedio,
    bs.goals_p90,
    bs.assists_p90,
    bs.xG_p90,
    bs.xA_p90,
    bs.prog_passes_p90,
    bs.key_passes_p90,
    bs.dribbles_p90,
    bs.recoveries_p90,
    bs.tackles_p90,
    bs.interceptions_p90,
    bs.aerial_won_p90,
    bs.clearances_p90,
    bs.blocks_p90,
    bs.errors_p90,
    bs.dispossessed_p90,
    
    -- =========================================
    -- PERCENTILES GENERALES (para radar charts)
    -- =========================================
    bs.pct_rating,
    bs.pct_xG,          -- NULL para arqueros
    bs.pct_xA,
    bs.pct_prog_passes,
    bs.pct_dribbles,
    bs.pct_recoveries,
    bs.pct_aerial,
    
    -- ⚠️ PERCENTILES DEFENSIVOS (AGREGADOS):
    bs.pct_tackles,
    bs.pct_interceptions,
    bs.pct_clearances,
    bs.pct_blocks,
    
    -- =========================================
    -- ARQUETIPO
    -- =========================================
    arq.arquetipo_id,
    arq.arquetipo_nombre,
    
    -- =========================================
    -- PROYECCIÓN DE VALOR
    -- =========================================
    proy.valor_proyectado_1y,
    proy.valor_proyectado_1y / 1000000 as valor_proyectado_millones,
    proy.delta_proyectado_pct,
    
    -- =========================================
    -- SIMILARES (Array)
    -- =========================================
    sim.similares_top5,

    -- =========================================
    -- ARQUEROS - STATS P90
    -- =========================================
    bs.saves_p90,
    bs.claims_p90,
    bs.punches_p90,
    bs.sweeper_p90,
    
    -- ARQUEROS - PORCENTAJES
    bs.saves_pct,
    bs.clean_sheets_pct,
    bs.sweeper_acc_pct,
    
    -- ARQUEROS - PERCENTILES
    bs.pct_saves,
    bs.pct_saves_pct,
    bs.pct_clean_sheets,
    bs.pct_sweeper

FROM BaseStats bs
LEFT JOIN Arquetipos arq 
    ON CAST(bs.player_id AS STRING) = arq.player_id
LEFT JOIN Proyecciones proy
    ON CAST(bs.player_id AS STRING) = proy.player_id
LEFT JOIN Similitudes sim
    ON CAST(bs.player_id AS STRING) = sim.jugador_origen_id
    AND bs.temporada_anio = sim.temporada_origen
"""

def crear_vista():
    """Crea vista consolidada para el dashboard"""
    print("🔨 Creando Vista Consolidada para Dashboard (VERSION COMPLETA)")
    print("=" * 70)
    
    try:
        job = CLIENT.query(sql_view)
        job.result()
        
        # Verificar resultados
        test_query = f"""
        SELECT 
            COUNT(*) as total_jugadores,
            COUNT(DISTINCT arquetipo_nombre) as arquetipos_unicos,
            COUNT(DISTINCT posicion) as posiciones,
            AVG(ARRAY_LENGTH(similares_top5)) as avg_similares,
            COUNT(valor_proyectado_millones) as jugadores_con_proyeccion,
            
            -- Verificar percentiles defensivos
            COUNT(pct_tackles) as jugadores_con_pct_tackles,
            COUNT(pct_interceptions) as jugadores_con_pct_interceptions,
            COUNT(pct_clearances) as jugadores_con_pct_clearances,
            COUNT(pct_blocks) as jugadores_con_pct_blocks
            
        FROM `{PROJECT_ID}.{DM_DATASET}.v_dashboard_scouting_completo`
        WHERE temporada_anio = (
            SELECT MAX(temporada_anio) 
            FROM `{PROJECT_ID}.{DM_DATASET}.stats_jugador_temporada_pro`
        )
        """
        
        result = CLIENT.query(test_query).result()
        stats = list(result)[0]
        
        print("✅ Vista creada exitosamente\n")
        print(f"📊 Estadísticas (última temporada):")
        print(f"   • Total jugadores:         {stats.total_jugadores:,}")
        print(f"   • Arquetipos únicos:       {stats.arquetipos_unicos}")
        print(f"   • Posiciones:              {stats.posiciones}")
        print(f"   • Similares promedio:      {stats.avg_similares:.1f}")
        print(f"   • Con proyección valor:    {stats.jugadores_con_proyeccion:,}")
        
        print(f"\n✅ Percentiles Defensivos Verificados:")
        print(f"   • pct_tackles:             {stats.jugadores_con_pct_tackles:,}")
        print(f"   • pct_interceptions:       {stats.jugadores_con_pct_interceptions:,}")
        print(f"   • pct_clearances:          {stats.jugadores_con_pct_clearances:,}")
        print(f"   • pct_blocks:              {stats.jugadores_con_pct_blocks:,}")
        
        # Query de ejemplo con percentiles defensivos
        print(f"\n" + "="*70)
        print("💡 EJEMPLO: DEFENSORES TOP CON PERCENTILES COMPLETOS")
        print("="*70)
        
        print(f"""
SELECT 
    nombre_jugador,
    equipo_principal,
    edad_promedio,
    valor_millones,
    rating_promedio,
    
    -- Stats P90
    tackles_p90,
    interceptions_p90,
    clearances_p90,
    blocks_p90,
    aerial_won_p90,
    
    -- Percentiles (0-1, multiplicar x100 para %)
    ROUND(pct_tackles * 100, 1) as tackles_percentil,
    ROUND(pct_interceptions * 100, 1) as interceptions_percentil,
    ROUND(pct_clearances * 100, 1) as clearances_percentil,
    ROUND(pct_blocks * 100, 1) as blocks_percentil,
    ROUND(pct_aerial * 100, 1) as aerial_percentil,
    
    arquetipo_nombre
    
FROM `{PROJECT_ID}.{DM_DATASET}.v_dashboard_scouting_completo`
WHERE temporada_anio = 2024
  AND posicion = 'Defensor'
  AND total_minutos >= 1000
  AND pct_tackles >= 0.75  -- Top 25% en tackles
  AND pct_aerial >= 0.70   -- Top 30% en duelos aéreos
ORDER BY rating_promedio DESC
LIMIT 20;
        """)
        
        print(f"\n" + "="*70)
        print("📋 RESUMEN DE PERCENTILES DISPONIBLES:")
        print("="*70)
        print("""
GENERALES (todas las posiciones):
  • pct_rating
  • pct_xA
  • pct_prog_passes
  • pct_dribbles
  • pct_recoveries
  • pct_aerial

OFENSIVOS (excluye arqueros):
  • pct_xG

DEFENSIVOS (todas las posiciones):
  • pct_tackles           ← ✅ AGREGADO
  • pct_interceptions     ← ✅ AGREGADO
  • pct_clearances        ← ✅ AGREGADO
  • pct_blocks            ← ✅ AGREGADO

ARQUEROS (solo posicion = 'Arquero'):
  • pct_saves
  • pct_saves_pct
  • pct_clean_sheets
  • pct_sweeper
        """)
        
        print(f"\n" + "="*70)
        print("✨ Vista lista para conectar con Streamlit/Looker/Tableau")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    crear_vista()