"""
MODELO ML COMPLETO - SCOUTING INTELIGENTE CON ARQUEROS
Unifica: Similitud KNN + Proyección Valor + Clustering Arquetipos
ACTUALIZACIÓN: Incluye features específicas para cada posición
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from typing import Dict, List

# --- CONFIGURACIÓN ---
PROJECT_ID = "proyecto-scouting-futbol"
DM_DATASET = "dm_scouting"
SOURCE_TABLE = f"{PROJECT_ID}.{DM_DATASET}.stats_jugador_temporada_pro"

DEST_SIMILITUD = f"{PROJECT_ID}.{DM_DATASET}.scouting_similitud_pro_v2"
DEST_ARQUETIPOS = f"{PROJECT_ID}.{DM_DATASET}.arquetipos_jugadores"
DEST_PROYECCIONES = f"{PROJECT_ID}.{DM_DATASET}.proyecciones_valor"

# ============================================================================
# CONFIGURACIÓN FEATURES POR POSICIÓN (INCLUYENDO ARQUEROS)
# ============================================================================

FEATURE_SETS = {
    'Arquero': {
        'primary': [
            'saves_p90', 'saves_pct', 'clean_sheets_pct',
            'sweeper_p90', 'claims_p90', 'punches_p90',
            'passes_p90', 'long_balls_p90', 'rating_promedio'
        ],
        'weights': {
            'saves_p90': 3.0,
            'saves_pct': 3.0,
            'clean_sheets_pct': 2.5,
            'sweeper_p90': 2.0,
            'claims_p90': 2.0,
            'punches_p90': 1.5,
            'passes_p90': 1.0,
            'long_balls_p90': 1.0,
            'rating_promedio': 2.0
        }
    },
    'Defensor': {
        'primary': [
            'tackles_p90', 'interceptions_p90', 'clearances_p90',
            'aerial_won_p90', 'blocks_p90', 'recoveries_p90',
            'prog_passes_p90', 'rating_promedio'
        ],
        'weights': {
            'tackles_p90': 3.0,
            'interceptions_p90': 3.0,
            'clearances_p90': 2.5,
            'aerial_won_p90': 2.5,
            'blocks_p90': 2.0,
            'recoveries_p90': 2.5,
            'prog_passes_p90': 1.5,
            'rating_promedio': 2.0
        }
    },
    'Mediocampista': {
        'primary': [
            'xG_p90', 'xA_p90', 'key_passes_p90', 'prog_passes_p90',
            'dribbles_p90', 'recoveries_p90', 'tackles_p90',
            'interceptions_p90', 'rating_promedio'
        ],
        'weights': {
            'xG_p90': 1.5,
            'xA_p90': 2.5,
            'key_passes_p90': 3.0,
            'prog_passes_p90': 3.0,
            'dribbles_p90': 2.0,
            'recoveries_p90': 2.5,
            'tackles_p90': 2.0,
            'interceptions_p90': 2.0,
            'rating_promedio': 2.0
        }
    },
    'Delantero': {
        'primary': [
            'xG_p90', 'xA_p90', 'goals_p90', 'shots_on_target',
            'dribbles_p90', 'key_passes_p90', 'aerial_won_p90',
            'rating_promedio'
        ],
        'weights': {
            'xG_p90': 3.0,
            'xA_p90': 2.0,
            'goals_p90': 3.0,
            'shots_on_target': 2.5,
            'dribbles_p90': 2.0,
            'key_passes_p90': 1.5,
            'aerial_won_p90': 1.2,
            'rating_promedio': 1.5
        }
    }
}

# ============================================================================
# MODELO 1: SIMILITUD CON ARQUEROS
# ============================================================================

def calcular_similitudes_por_posicion(client: bigquery.Client) -> pd.DataFrame:
    """MODELO 1 MEJORADO: Similitud POR POSICIÓN con features específicas"""
    print("\n" + "="*70)
    print("🧠 MODELO 1: SIMILITUD POR POSICIÓN (KNN ADAPTATIVO + ARQUEROS)")
    print("="*70)
    
    all_results = []
    
    # ITERAR POR CADA POSICIÓN (incluyendo arqueros)
    for posicion, config in FEATURE_SETS.items():
        print(f"\n📍 Procesando: {posicion}")
        
        # Query específica por posición
        features_str = ", ".join(config['primary'])
        
        # WHERE dinámico para features no nulos
        where_conditions = [f"{feat} IS NOT NULL" for feat in config['primary']]
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
            SELECT 
                player_id, player, temporada_anio, posicion,
                equipo_principal, nacionalidad, edad_promedio, 
                valor_mercado, total_minutos, partidos_jugados,
                {features_str}
            FROM `{SOURCE_TABLE}`
            WHERE posicion = '{posicion}'
              AND total_minutos > 400
              AND rating_promedio > 6.0
              AND {where_clause}
        """
        
        df_pos = client.query(query).to_dataframe()
        
        if len(df_pos) < 10:
            print(f"   ⚠️ Pocos datos ({len(df_pos)}), saltando...")
            continue
        
        print(f"   ✓ {len(df_pos)} jugadores cargados")
        
        # Aplicar pesos específicos
        df_weighted = df_pos.copy()
        for feature in config['primary']:
            weight = config['weights'].get(feature, 1.0)
            df_weighted[feature] = df_weighted[feature].astype(float) * weight
        
        # Normalizar
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_weighted[config['primary']].fillna(0))
        
        # KNN
        n_neighbors = min(11, len(df_pos))
        knn = NearestNeighbors(n_neighbors=n_neighbors, algorithm='ball_tree')
        knn.fit(X_scaled)
        
        distances, indices = knn.kneighbors(X_scaled)
        
        # Generar relaciones
        for i in range(len(df_pos)):
            source_row = df_pos.iloc[i]
            
            for j in range(1, min(6, n_neighbors)):
                neighbor_idx = indices[i][j]
                neighbor_row = df_pos.iloc[neighbor_idx]
                
                dist = distances[i][j]
                tiempo_diff = abs(source_row['temporada_anio'] - neighbor_row['temporada_anio'])
                decay_factor = 0.95 ** tiempo_diff
                similarity_adjusted = (1 / (1 + dist)) * 100 * decay_factor
                
                all_results.append({
                    'jugador_origen': source_row['player'],
                    'jugador_origen_id': str(source_row['player_id']),
                    'temporada_origen': int(source_row['temporada_anio']),
                    'jugador_similar': neighbor_row['player'],
                    'jugador_similar_id': str(neighbor_row['player_id']),
                    'temporada_similar': int(neighbor_row['temporada_anio']),
                    'posicion': posicion,
                    'rank_similitud': j,
                    'score_similitud': round(similarity_adjusted, 2),
                    'distancia_euclidiana': round(dist, 4),
                    'decay_temporal': round(decay_factor, 3),
                    'valor_mercado_similar': neighbor_row['valor_mercado'],
                    'edad_similar': neighbor_row['edad_promedio'],
                    'equipo_similar': neighbor_row['equipo_principal']
                })
        
        print(f"   ✓ {len([r for r in all_results if r['posicion'] == posicion])} relaciones generadas")
    
    df_similitudes = pd.DataFrame(all_results)
    
    print(f"\n✅ TOTAL: {len(df_similitudes):,} relaciones de similitud")
    for posicion in FEATURE_SETS.keys():
        count = len(df_similitudes[df_similitudes['posicion'] == posicion])
        print(f"   {posicion}: {count:,}")
    
    return df_similitudes

# ============================================================================
# MODELO 2: PROYECCIÓN DE VALOR (SIN CAMBIOS MAYORES)
# ============================================================================

FEATURES_VALOR = [
    'edad_promedio', 'rating_promedio', 'total_minutos', 'partidos_jugados',
    'pct_rating'
]

def entrenar_modelo_valor(client: bigquery.Client) -> tuple:
    """MODELO 2: Proyección de Valor de Mercado"""
    print("\n" + "="*70)
    print("💰 MODELO 2: PROYECCIÓN DE VALOR DE MERCADO")
    print("="*70)
    
    # Query optimizada (features comunes a todas las posiciones)
    query = f"""
        WITH ValoresPorTemporada AS (
            SELECT
                player_id, temporada_anio, player, posicion,
                edad_promedio, valor_mercado, rating_promedio,
                total_minutos, partidos_jugados, pct_rating
            FROM `{SOURCE_TABLE}`
            WHERE valor_mercado IS NOT NULL
              AND valor_mercado > 0
              AND total_minutos >= 500
        )
        SELECT
            t1.player_id, t1.player, t1.posicion,
            t1.temporada_anio as temp_t1,
            t2.temporada_anio as temp_t2,
            t1.edad_promedio, t1.valor_mercado as valor_t1,
            t1.rating_promedio, t1.total_minutos, t1.partidos_jugados,
            t1.pct_rating,
            t2.valor_mercado as valor_t2,
            ((t2.valor_mercado - t1.valor_mercado) / t1.valor_mercado) * 100 as delta_valor_pct
        FROM ValoresPorTemporada t1
        INNER JOIN ValoresPorTemporada t2
            ON t1.player_id = t2.player_id
            AND t2.temporada_anio = t1.temporada_anio + 1
        WHERE t1.edad_promedio <= 30
          AND t1.valor_mercado >= 500000
    """
    
    df = client.query(query).to_dataframe()
    print(f"✓ {len(df)} casos de evolución encontrados")
    
    # Entrenar modelo
    X = df[FEATURES_VALOR].fillna(0)
    y = df['delta_valor_pct']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, max_depth=5, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    train_score = model.score(X_train_scaled, y_train)
    test_score = model.score(X_test_scaled, y_test)
    
    print(f"✓ Modelo entrenado | R² Train: {train_score:.3f} | R² Test: {test_score:.3f}")
    
    # Proyecciones actuales
    query_actual = f"""
        SELECT
            player_id, player, posicion, temporada_anio,
            equipo_principal, edad_promedio, valor_mercado,
            rating_promedio, total_minutos, partidos_jugados, pct_rating
        FROM `{SOURCE_TABLE}`
        WHERE temporada_anio = (SELECT MAX(temporada_anio) FROM `{SOURCE_TABLE}`)
          AND edad_promedio <= 30
          AND total_minutos >= 900
          AND valor_mercado IS NOT NULL
    """
    
    df_actual = client.query(query_actual).to_dataframe()
    
    X_actual = df_actual[FEATURES_VALOR].fillna(0)
    X_actual_scaled = scaler.transform(X_actual)
    
    df_actual['delta_proyectado_pct'] = model.predict(X_actual_scaled)
    df_actual['valor_proyectado_1y'] = df_actual['valor_mercado'] * (1 + df_actual['delta_proyectado_pct'] / 100)
    
    df_proyecciones = df_actual[[
        'player_id', 'player', 'posicion', 'temporada_anio',
        'equipo_principal', 'edad_promedio',
        'valor_mercado', 'valor_proyectado_1y', 'delta_proyectado_pct'
    ]].copy()
    
    df_proyecciones['player_id'] = df_proyecciones['player_id'].astype(str)
    
    print(f"✓ {len(df_proyecciones)} proyecciones generadas (incluyendo arqueros)")
    
    return df_proyecciones, model, scaler

# ============================================================================
# MODELO 3: CLUSTERING POR POSICIÓN
# ============================================================================

def generar_arquetipos_por_posicion(client: bigquery.Client) -> pd.DataFrame:
    """MODELO 3: Clustering de Arquetipos POR POSICIÓN"""
    print("\n" + "="*70)
    print("🎨 MODELO 3: CLUSTERING DE ARQUETIPOS POR POSICIÓN")
    print("="*70)
    
    all_arquetipos = []
    cluster_global_id = 0
    
    for posicion, config in FEATURE_SETS.items():
        print(f"\n📍 Clustering para: {posicion}")
        
        features_str = ", ".join(config['primary'])
        where_conditions = [f"{feat} IS NOT NULL" for feat in config['primary']]
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
            SELECT
                player_id, player, posicion, equipo_principal,
                edad_promedio, valor_mercado, nacionalidad,
                total_minutos, partidos_jugados, rating_promedio,
                {features_str}
            FROM `{SOURCE_TABLE}`
            WHERE temporada_anio = (SELECT MAX(temporada_anio) FROM `{SOURCE_TABLE}`)
              AND posicion = '{posicion}'
              AND total_minutos >= 900
              AND rating_promedio >= 6.5
              AND {where_clause}
        """
        
        df_pos = client.query(query).to_dataframe()
        
        if len(df_pos) < 15:
            print(f"   ⚠️ Datos insuficientes ({len(df_pos)})")
            continue
        
        print(f"   ✓ {len(df_pos)} jugadores")
        
        # Determinar número de clusters
        n_clusters = min(5, max(3, len(df_pos) // 30))
        
        # Clustering
        X = df_pos[config['primary']].fillna(0)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
        df_pos['cluster_local'] = kmeans.fit_predict(X_scaled)
        df_pos['cluster_global'] = df_pos['cluster_local'] + cluster_global_id
        
        # Nombrar arquetipos según posición
        for cluster_id in sorted(df_pos['cluster_local'].unique()):
            mask = df_pos['cluster_local'] == cluster_id
            stats = df_pos.loc[mask, config['primary']].mean()
            
            # Lógica de nombres por posición
            if posicion == 'Arquero':
                if stats['saves_pct'] > 70:
                    nombre = "🧤 Muro Infranqueable"
                elif stats['sweeper_p90'] > 1.5:
                    nombre = "🏃 Arquero Líbero"
                else:
                    nombre = "✋ Guardameta Sólido"
            
            elif posicion == 'Defensor':
                if stats['aerial_won_p90'] > 3.0:
                    nombre = "🗼 Coloso Aéreo"
                elif stats['tackles_p90'] > 3.0:
                    nombre = "🔒 Marcador Férreo"
                else:
                    nombre = "🧱 Defensor Completo"
            
            elif posicion == 'Mediocampista':
                if stats['key_passes_p90'] > 2.0:
                    nombre = "🎨 Creador Puro"
                elif stats['recoveries_p90'] > 7.0:
                    nombre = "🎩 Pivote Recuperador"
                else:
                    nombre = "🔄 Box-to-Box"
            
            else:  # Delantero
                if stats['xG_p90'] > 0.6:
                    nombre = "🎯 Goleador Nato"
                elif stats['dribbles_p90'] > 3.0:
                    nombre = "⚡ Extremo Eléctrico"
                else:
                    nombre = "🦅 Ariete Completo"
            
            df_pos.loc[mask, 'arquetipo_nombre'] = nombre
        
        all_arquetipos.append(df_pos)
        cluster_global_id += n_clusters
        print(f"   ✓ {n_clusters} arquetipos creados")
    
    df_arquetipos = pd.concat(all_arquetipos, ignore_index=True)
    
    df_resultado = df_arquetipos[[
        'player_id', 'player', 'posicion', 'equipo_principal',
        'cluster_global', 'arquetipo_nombre', 'rating_promedio', 'valor_mercado'
    ]].copy()
    
    df_resultado['player_id'] = df_resultado['player_id'].astype(str)
    df_resultado.rename(columns={'cluster_global': 'cluster'}, inplace=True)
    
    print(f"\n✅ {len(df_resultado)} jugadores clasificados en arquetipos")
    
    return df_resultado

# ============================================================================
# PIPELINE COMPLETO
# ============================================================================

def upload_to_bigquery(client: bigquery.Client, df: pd.DataFrame, dest_table: str, schema: list):
    """Sube DataFrame a BigQuery"""
    job_config = bigquery.LoadJobConfig(schema=schema, write_disposition="WRITE_TRUNCATE")
    job = client.load_table_from_dataframe(df, dest_table, job_config=job_config)
    job.result()
    print(f"✅ Tabla actualizada: {dest_table}")

def run_all_models():
    """Pipeline completo incluyendo arqueros"""
    
    print("\n" + "🚀"*35)
    print("   PIPELINE ML COMPLETO - TODAS LAS POSICIONES")
    print("🚀"*35)
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # MODELO 1: SIMILITUD
    df_similitudes = calcular_similitudes_por_posicion(client)
    
    schema_similitud = [
        bigquery.SchemaField("jugador_origen", "STRING"),
        bigquery.SchemaField("jugador_origen_id", "STRING"),
        bigquery.SchemaField("temporada_origen", "INTEGER"),
        bigquery.SchemaField("jugador_similar", "STRING"),
        bigquery.SchemaField("jugador_similar_id", "STRING"),
        bigquery.SchemaField("temporada_similar", "INTEGER"),
        bigquery.SchemaField("posicion", "STRING"),
        bigquery.SchemaField("rank_similitud", "INTEGER"),
        bigquery.SchemaField("score_similitud", "FLOAT"),
        bigquery.SchemaField("distancia_euclidiana", "FLOAT"),
        bigquery.SchemaField("decay_temporal", "FLOAT"),
        bigquery.SchemaField("valor_mercado_similar", "FLOAT"),
        bigquery.SchemaField("edad_similar", "FLOAT"),
        bigquery.SchemaField("equipo_similar", "STRING"),
    ]
    
    upload_to_bigquery(client, df_similitudes, DEST_SIMILITUD, schema_similitud)
    
    # MODELO 2: PROYECCIÓN
    df_proyecciones, _, _ = entrenar_modelo_valor(client)
    
    schema_proyecciones = [
        bigquery.SchemaField("player_id", "STRING"),
        bigquery.SchemaField("player", "STRING"),
        bigquery.SchemaField("posicion", "STRING"),
        bigquery.SchemaField("temporada_anio", "INTEGER"),
        bigquery.SchemaField("equipo_principal", "STRING"),
        bigquery.SchemaField("edad_promedio", "FLOAT"),
        bigquery.SchemaField("valor_mercado", "FLOAT"),
        bigquery.SchemaField("valor_proyectado_1y", "FLOAT"),
        bigquery.SchemaField("delta_proyectado_pct", "FLOAT"),
    ]
    
    upload_to_bigquery(client, df_proyecciones, DEST_PROYECCIONES, schema_proyecciones)
    
    # MODELO 3: ARQUETIPOS
    df_arquetipos = generar_arquetipos_por_posicion(client)
    
    schema_arquetipos = [
        bigquery.SchemaField("player_id", "STRING"),
        bigquery.SchemaField("player", "STRING"),
        bigquery.SchemaField("posicion", "STRING"),
        bigquery.SchemaField("equipo_principal", "STRING"),
        bigquery.SchemaField("cluster", "INTEGER"),
        bigquery.SchemaField("arquetipo_nombre", "STRING"),
        bigquery.SchemaField("rating_promedio", "FLOAT"),
        bigquery.SchemaField("valor_mercado", "FLOAT"),
    ]
    
    upload_to_bigquery(client, df_arquetipos, DEST_ARQUETIPOS, schema_arquetipos)
    
    # RESUMEN
    print("\n" + "✅"*35)
    print("      PIPELINE COMPLETADO")
    print("✅"*35)
    print(f"\n📊 Resultados:")
    print(f"   • Similitudes:   {len(df_similitudes):,} relaciones")
    print(f"   • Proyecciones:  {len(df_proyecciones):,} jugadores")
    print(f"   • Arquetipos:    {len(df_arquetipos):,} jugadores")
    
    # Desglose por posición
    print(f"\n📍 Desglose Similitudes:")
    for pos in FEATURE_SETS.keys():
        count = len(df_similitudes[df_similitudes['posicion'] == pos])
        print(f"   {pos}: {count:,}")

if __name__ == '__main__':
    run_all_models()