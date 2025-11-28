"""
MODELO ML COMPLETO - SCOUTING INTELIGENTE
Unifica: Similitud KNN + Proyección Valor + Clustering Arquetipos
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

# Tablas de salida
DEST_SIMILITUD = f"{PROJECT_ID}.{DM_DATASET}.scouting_similitud_pro_v2"
DEST_ARQUETIPOS = f"{PROJECT_ID}.{DM_DATASET}.arquetipos_jugadores"
DEST_PROYECCIONES = f"{PROJECT_ID}.{DM_DATASET}.proyecciones_valor"

# ============================================================================
# PARTE 1: MODELO DE SIMILITUD (KNN) - Tu código original mejorado
# ============================================================================

FEATURE_WEIGHTS = {
    'Delantero': {
        'xG_p90': 3.0, 'xA_p90': 2.0, 'shots_on_target': 2.5,
        'dribbles_p90': 2.0, 'prog_passes_p90': 1.0, 'key_passes_p90': 1.5,
        'recoveries_p90': 0.5, 'interceptions_p90': 0.3, 'tackles_p90': 0.3,
        'aerial_won_p90': 1.2, 'rating_promedio': 1.5
    },
    'Mediocampista': {
        'xG_p90': 1.5, 'xA_p90': 2.5, 'shots_on_target': 1.0,
        'dribbles_p90': 2.0, 'prog_passes_p90': 3.0, 'key_passes_p90': 3.0,
        'recoveries_p90': 2.5, 'interceptions_p90': 2.0, 'tackles_p90': 2.0,
        'aerial_won_p90': 1.0, 'rating_promedio': 2.0
    },
    'Defensor': {
        'xG_p90': 0.3, 'xA_p90': 0.5, 'shots_on_target': 0.3,
        'dribbles_p90': 0.8, 'prog_passes_p90': 1.5, 'key_passes_p90': 0.8,
        'recoveries_p90': 3.0, 'interceptions_p90': 3.0, 'tackles_p90': 3.0,
        'aerial_won_p90': 2.5, 'rating_promedio': 2.0
    }
}

FEATURES_SIMILITUD = [
    'xG_p90', 'xA_p90', 'shots_on_target', 'prog_passes_p90', 'key_passes_p90',
    'dribbles_p90', 'recoveries_p90', 'interceptions_p90', 'tackles_p90',
    'aerial_won_p90', 'rating_promedio'
]

def calcular_similitudes(client: bigquery.Client) -> pd.DataFrame:
    """MODELO 1: Similitud entre jugadores (KNN)"""
    print("\n" + "="*70)
    print("🧠 MODELO 1: SIMILITUD ENTRE JUGADORES (KNN)")
    print("="*70)
    
    # Cargar datos
    query = f"""
        SELECT 
            player_id, player, temporada_anio, posicion,
            equipo_principal, nacionalidad, edad_promedio,
            valor_mercado, total_minutos, partidos_jugados,
            xG_p90, xA_p90, 
            sum_shots_target as shots_on_target,
            prog_passes_p90, key_passes_p90, dribbles_p90,
            recoveries_p90, interceptions_p90, tackles_p90, aerial_won_p90,
            rating_promedio
        FROM `{SOURCE_TABLE}`
        WHERE total_minutos > 400 
          AND posicion != 'Arquero'
          AND rating_promedio > 6.0
    """
    
    df = client.query(query).to_dataframe()
    print(f"✓ {len(df)} perfiles cargados")
    
    # Aplicar pesos por posición
    df_weighted = df.copy()
    for feature in FEATURES_SIMILITUD:
        df_weighted[feature] = df_weighted[feature].astype(float)
    
    for posicion, weights in FEATURE_WEIGHTS.items():
        mask = df_weighted['posicion'] == posicion
        for feature in FEATURES_SIMILITUD:
            if feature in weights:
                df_weighted.loc[mask, feature] *= weights[feature]
    
    # Calcular similitudes POR POSICIÓN
    all_results = []
    
    for posicion in df['posicion'].unique():
        df_pos = df_weighted[df_weighted['posicion'] == posicion].copy()
        
        if len(df_pos) < 10:
            continue
        
        print(f"  → {posicion}: {len(df_pos)} jugadores")
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_pos[FEATURES_SIMILITUD].fillna(0))
        
        n_neighbors = min(11, len(df_pos))
        knn = NearestNeighbors(n_neighbors=n_neighbors, algorithm='ball_tree')
        knn.fit(X_scaled)
        
        distances, indices = knn.kneighbors(X_scaled)
        
        df_pos['unique_id'] = df_pos['player_id'].astype(str) + "_" + df_pos['temporada_anio'].astype(str)
        
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
    
    df_similitudes = pd.DataFrame(all_results)
    print(f"✓ {len(df_similitudes)} relaciones de similitud generadas")
    
    return df_similitudes

# ============================================================================
# PARTE 2: PROYECCIÓN DE VALOR DE MERCADO
# ============================================================================

FEATURES_VALOR = [
    'edad_promedio', 'rating_promedio', 'xG_p90', 'xA_p90',
    'goals_p90', 'assists_p90', 'prog_passes_p90', 'key_passes_p90',
    'dribbles_p90', 'recoveries_p90', 'tackles_p90',
    'total_minutos', 'partidos_jugados',
    'pct_rating', 'pct_xG', 'pct_xA', 'pct_prog_passes'
]

def entrenar_modelo_valor(client: bigquery.Client) -> tuple:
    """MODELO 2: Proyección de Valor de Mercado"""
    print("\n" + "="*70)
    print("💰 MODELO 2: PROYECCIÓN DE VALOR DE MERCADO")
    print("="*70)
    
    # Cargar datos históricos (evolución temporal)
    query = f"""
        WITH ValoresPorTemporada AS (
            SELECT
                player_id, temporada_anio, player, posicion,
                edad_promedio, valor_mercado, rating_promedio,
                xG_p90, xA_p90, goals_p90, assists_p90,
                prog_passes_p90, key_passes_p90, dribbles_p90,
                recoveries_p90, tackles_p90, total_minutos, partidos_jugados,
                pct_rating, pct_xG, pct_xA, pct_prog_passes
            FROM `{SOURCE_TABLE}`
            WHERE valor_mercado IS NOT NULL
              AND valor_mercado > 0
              AND total_minutos >= 500
        )
        SELECT
            t1.player_id, t1.player, t1.posicion,
            t1.temporada_anio as temp_t1,
            t2.temporada_anio as temp_t2,
            
            -- Predictores (T1)
            t1.edad_promedio, t1.valor_mercado as valor_t1,
            t1.rating_promedio, t1.xG_p90, t1.xA_p90,
            t1.goals_p90, t1.assists_p90, t1.prog_passes_p90,
            t1.key_passes_p90, t1.dribbles_p90, t1.recoveries_p90,
            t1.tackles_p90, t1.total_minutos, t1.partidos_jugados,
            t1.pct_rating, t1.pct_xG, t1.pct_xA, t1.pct_prog_passes,
            
            -- Target (T2)
            t2.valor_mercado as valor_t2,
            ((t2.valor_mercado - t1.valor_mercado) / t1.valor_mercado) * 100 as delta_valor_pct
            
        FROM ValoresPorTemporada t1
        INNER JOIN ValoresPorTemporada t2
            ON t1.player_id = t2.player_id
            AND t2.temporada_anio = t1.temporada_anio + 1
        WHERE t1.edad_promedio <= 28
          AND t1.valor_mercado >= 1000000
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
    
    # Generar proyecciones para todos los jugadores actuales
    query_actual = f"""
        SELECT
            player_id, player, posicion, temporada_anio,
            equipo_principal, edad_promedio, valor_mercado,
            {', '.join(FEATURES_VALOR)}
        FROM `{SOURCE_TABLE}`
        WHERE temporada_anio = (SELECT MAX(temporada_anio) FROM `{SOURCE_TABLE}`)
          AND edad_promedio <= 28
          AND total_minutos >= 900
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
    
    print(f"✓ {len(df_proyecciones)} proyecciones generadas")
    
    return df_proyecciones, model, scaler

# ============================================================================
# PARTE 3: CLUSTERING DE ARQUETIPOS
# ============================================================================

FEATURES_CLUSTERING = [
    'xG_p90', 'xA_p90', 'goals_p90', 'assists_p90', 'shots_on_target',
    'key_passes_p90', 'dribbles_p90', 'prog_passes_p90',
    'recoveries_p90', 'tackles_p90', 'interceptions_p90',
    'aerial_won_p90', 'clearances_p90', 'rating_promedio'
]

def generar_arquetipos(client: bigquery.Client, n_clusters: int = 15) -> pd.DataFrame:
    """MODELO 3: Clustering de Arquetipos"""
    print("\n" + "="*70)
    print("🎨 MODELO 3: CLUSTERING DE ARQUETIPOS")
    print("="*70)
    
    # Cargar datos actuales
    query = f"""
        SELECT
            player_id, player, posicion, equipo_principal,
            edad_promedio, valor_mercado, nacionalidad,
            total_minutos, partidos_jugados, rating_promedio,
            goals_p90, assists_p90, xG_p90, xA_p90,
            sum_shots_target as shots_on_target,
            dribbles_p90, key_passes_p90, prog_passes_p90,
            recoveries_p90, tackles_p90, interceptions_p90,
            aerial_won_p90, clearances_p90
        FROM `{SOURCE_TABLE}`
        WHERE temporada_anio = (SELECT MAX(temporada_anio) FROM `{SOURCE_TABLE}`)
          AND posicion != 'Arquero'
          AND total_minutos >= 900
          AND rating_promedio >= 6.5
    """
    
    df = client.query(query).to_dataframe()
    print(f"✓ {len(df)} jugadores cargados para clustering")
    
    # Clustering
    X = df[FEATURES_CLUSTERING].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=20, max_iter=500)
    df['cluster'] = kmeans.fit_predict(X_scaled)
    
    # Interpretar arquetipos
    arquetipos_info = {}
    
    for cluster_id in sorted(df['cluster'].unique()):
        cluster_data = df[df['cluster'] == cluster_id]
        stats = cluster_data[FEATURES_CLUSTERING].mean()
        
        # Clasificar arquetipo
        score_ataque = stats[['xG_p90', 'xA_p90', 'goals_p90', 'assists_p90', 'shots_on_target', 'dribbles_p90']].mean()
        score_construccion = stats[['prog_passes_p90', 'key_passes_p90']].mean()
        score_defensa = stats[['recoveries_p90', 'tackles_p90', 'interceptions_p90', 'aerial_won_p90', 'clearances_p90']].mean()
        
        total = score_ataque + score_construccion + score_defensa
        pct_ataque = score_ataque / total if total > 0 else 0
        pct_defensa = score_defensa / total if total > 0 else 0
        
        # Asignar nombre
        if pct_ataque > 0.45:
            if stats['xG_p90'] > 0.5:
                nombre, emoji = "Goleador Letal", "🎯"
            elif stats['dribbles_p90'] > 2.0:
                nombre, emoji = "Extremo Desequilibrante", "⚡"
            else:
                nombre, emoji = "Delantero Completo", "🦅"
        elif 0.25 < pct_ataque < 0.45 and pct_defensa < 0.40:
            if stats['xA_p90'] > 0.25:
                nombre, emoji = "Mediapunta Creativo", "🎨"
            elif stats['prog_passes_p90'] > 5.0:
                nombre, emoji = "Organizador de Juego", "🧠"
            else:
                nombre, emoji = "Interior Box-to-Box", "🔄"
        elif pct_defensa > 0.40 and score_construccion > 2.0:
            nombre, emoji = "Pivote Conductor", "🎩"
        elif pct_defensa > 0.50:
            if stats['aerial_won_p90'] > 2.5:
                nombre, emoji = "Defensor Aéreo", "🗼"
            elif stats['tackles_p90'] > 2.5:
                nombre, emoji = "Marcador Agresivo", "🔒"
            else:
                nombre, emoji = "Defensor Seguro", "🧱"
        else:
            nombre, emoji = "Jugador Balanceado", "⚖️"
        
        df.loc[df['cluster'] == cluster_id, 'arquetipo_nombre'] = f"{emoji} {nombre}"
        
        arquetipos_info[cluster_id] = {
            'nombre': nombre,
            'emoji': emoji,
            'n_jugadores': len(cluster_data)
        }
    
    print(f"✓ {n_clusters} arquetipos identificados")
    for info in arquetipos_info.values():
        print(f"  {info['emoji']} {info['nombre']}: {info['n_jugadores']} jugadores")
    
    df_arquetipos = df[['player_id', 'player', 'posicion', 'equipo_principal',
                         'cluster', 'arquetipo_nombre', 'rating_promedio',
                         'xG_p90', 'xA_p90', 'valor_mercado']].copy()
    
    df_arquetipos['player_id'] = df_arquetipos['player_id'].astype(str)
    
    return df_arquetipos

# ============================================================================
# FUNCIÓN PRINCIPAL: EJECUTA TODO
# ============================================================================

def upload_to_bigquery(client: bigquery.Client, df: pd.DataFrame, dest_table: str, schema: list):
    """Sube DataFrame a BigQuery"""
    job_config = bigquery.LoadJobConfig(schema=schema, write_disposition="WRITE_TRUNCATE")
    job = client.load_table_from_dataframe(df, dest_table, job_config=job_config)
    job.result()
    print(f"✅ Tabla actualizada: {dest_table}")

def run_all_models():
    """Pipeline completo: Similitud + Proyección + Clustering"""
    
    print("\n" + "🚀"*35)
    print("      PIPELINE COMPLETO DE MODELOS ML - SCOUTING")
    print("🚀"*35)
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # ============ MODELO 1: SIMILITUD ============
    df_similitudes = calcular_similitudes(client)
    
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
    
    # ============ MODELO 2: PROYECCIÓN VALOR ============
    df_proyecciones, model_valor, scaler_valor = entrenar_modelo_valor(client)
    
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
    
    # ============ MODELO 3: ARQUETIPOS ============
    df_arquetipos = generar_arquetipos(client, n_clusters=15)
    
    schema_arquetipos = [
        bigquery.SchemaField("player_id", "STRING"),
        bigquery.SchemaField("player", "STRING"),
        bigquery.SchemaField("posicion", "STRING"),
        bigquery.SchemaField("equipo_principal", "STRING"),
        bigquery.SchemaField("cluster", "INTEGER"),
        bigquery.SchemaField("arquetipo_nombre", "STRING"),
        bigquery.SchemaField("rating_promedio", "FLOAT"),
        bigquery.SchemaField("xG_p90", "FLOAT"),
        bigquery.SchemaField("xA_p90", "FLOAT"),
        bigquery.SchemaField("valor_mercado", "FLOAT"),
    ]
    
    upload_to_bigquery(client, df_arquetipos, DEST_ARQUETIPOS, schema_arquetipos)
    
    # ============ RESUMEN FINAL ============
    print("\n" + "✅"*35)
    print("      PIPELINE COMPLETADO EXITOSAMENTE")
    print("✅"*35)
    print(f"\n📊 Resultados:")
    print(f"   • Similitudes:   {len(df_similitudes):,} relaciones → {DEST_SIMILITUD}")
    print(f"   • Proyecciones:  {len(df_proyecciones):,} jugadores → {DEST_PROYECCIONES}")
    print(f"   • Arquetipos:    {len(df_arquetipos):,} jugadores en {df_arquetipos['cluster'].nunique()} clusters → {DEST_ARQUETIPOS}")
    
    print(f"\n💡 Próximo paso: Ejecutar 04_crear_vista_dashboard.py para consolidar todo en una vista")

if __name__ == '__main__':
    run_all_models()