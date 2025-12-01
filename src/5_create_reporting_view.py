"""
VISTA UNIFICADA PARA DASHBOARD
Consolida: Stats Base + Similitudes + Proyecciones + Arquetipos
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
        
        -- Percentiles
        pct_rating,
        pct_xG,
        pct_xA,
        pct_prog_passes,
        pct_dribbles,
        pct_recoveries,
        pct_aerial,

        -- Arqueros - P90
        saves_p90,
        claims_p90,
        punches_p90,
        sweeper_p90,
        
        -- Arqueros - Porcentajes
        saves_pct,
        clean_sheets_pct,
        sweeper_acc_pct,
        
        -- Percentiles arqueros
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
    
    -- Stats P90
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
    
    -- Percentiles (para radar charts)
    bs.pct_rating,
    bs.pct_xG,
    bs.pct_xA,
    bs.pct_prog_passes,
    bs.pct_dribbles,
    bs.pct_recoveries,
    bs.pct_aerial,
    
    -- Arquetipo
    arq.arquetipo_id,
    arq.arquetipo_nombre,
    
    -- Proyección de valor
    proy.valor_proyectado_1y,
    proy.valor_proyectado_1y / 1000000 as valor_proyectado_millones,
    proy.delta_proyectado_pct,
    
    -- Similares (Array)
    sim.similares_top5,

    -- Arqueros
    bs.saves_p90,
    bs.saves_pct,
    bs.clean_sheets_pct,
    bs.sweeper_p90,
    bs.sweeper_acc_pct,
    bs.claims_p90,
    bs.punches_p90,
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
    print("🔨 Creando Vista Consolidada para Dashboard")
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
            COUNT(valor_proyectado_millones) as jugadores_con_proyeccion
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
        print(f"   • Total jugadores:        {stats.total_jugadores:,}")
        print(f"   • Arquetipos únicos:      {stats.arquetipos_unicos}")
        print(f"   • Posiciones:             {stats.posiciones}")
        print(f"   • Similares promedio:     {stats.avg_similares:.1f}")
        print(f"   • Con proyección valor:   {stats.jugadores_con_proyeccion:,}")
        
        # Queries de ejemplo
        print(f"\n" + "="*70)
        print("💡 QUERIES DE EJEMPLO PARA TU DASHBOARD")
        print("="*70)
        
        print(f"\n1️⃣  Búsqueda básica con todos los datos:")
        print(f"""
SELECT 
    nombre_jugador,
    posicion,
    equipo_principal,
    edad_promedio,
    valor_millones,
    rating_promedio,
    xG_p90,
    xA_p90,
    arquetipo_nombre,
    delta_proyectado_pct,
    similares_top5[OFFSET(0)].nombre as similar_1,
    similares_top5[OFFSET(0)].score_similitud as score_1
FROM `{PROJECT_ID}.{DM_DATASET}.v_dashboard_scouting_completo`
WHERE nombre_jugador LIKE '%Álvarez%'
  AND temporada_anio = 2024;
        """)
        
        print(f"\n2️⃣  Búsqueda multi-criterio (jóvenes con potencial):")
        print(f"""
SELECT 
    nombre_jugador,
    equipo_principal,
    edad_promedio,
    valor_millones,
    valor_proyectado_millones,
    delta_proyectado_pct,
    rating_promedio,
    arquetipo_nombre
FROM `{PROJECT_ID}.{DM_DATASET}.v_dashboard_scouting_completo`
WHERE temporada_anio = 2024
  AND posicion = 'Delantero'
  AND edad_promedio <= 25
  AND valor_millones <= 20
  AND delta_proyectado_pct > 10  -- Proyección de +10% revalorización
  AND pct_xG >= 0.70              -- Top 30% en goles esperados
ORDER BY delta_proyectado_pct DESC
LIMIT 20;
        """)
        
        print(f"\n3️⃣  Explorar arquetipos específicos:")
        print(f"""
SELECT 
    nombre_jugador,
    equipo_principal,
    edad_promedio,
    valor_millones,
    rating_promedio,
    xG_p90,
    xA_p90
FROM `{PROJECT_ID}.{DM_DATASET}.v_dashboard_scouting_completo`
WHERE temporada_anio = 2024
  AND arquetipo_nombre LIKE '%Goleador%'
  AND valor_millones <= 30
ORDER BY rating_promedio DESC
LIMIT 20;
        """)
        
        print(f"\n4️⃣  Expandir similares (ver detalle de los 5 similares):")
        print(f"""
SELECT 
    nombre_jugador,
    similar.nombre as jugador_similar,
    similar.equipo as equipo_similar,
    similar.score_similitud,
    similar.valor_millones as valor_similar,
    similar.edad as edad_similar,
    similar.rank_similitud
FROM `{PROJECT_ID}.{DM_DATASET}.v_dashboard_scouting_completo`,
UNNEST(similares_top5) as similar
WHERE nombre_jugador LIKE '%Álvarez%'
  AND temporada_anio = 2024
ORDER BY similar.rank_similitud;
        """)
        
        print(f"\n5️⃣  Top oportunidades por arquetipo y rango de precio:")
        print(f"""
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
        valor_millones,
        rating_promedio,
        ROW_NUMBER() OVER (
            PARTITION BY arquetipo_nombre,
            CASE 
                WHEN valor_millones < 10 THEN 'Económico (<€10M)'
                WHEN valor_millones < 30 THEN 'Medio (€10-30M)'
                ELSE 'Premium (>€30M)'
            END
            ORDER BY rating_promedio DESC
        ) as rank
    FROM `{PROJECT_ID}.{DM_DATASET}.v_dashboard_scouting_completo`
    WHERE temporada_anio = 2024
)
SELECT * FROM Rangos
WHERE rank = 1
ORDER BY arquetipo_nombre, rango_precio;
        """)
        
        print(f"\n" + "="*70)
        print("✨ Vista lista para conectar con Streamlit/Looker/Tableau")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    crear_vista()