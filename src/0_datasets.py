from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# --- CONFIGURACIÓN ---
PROJECT_ID = "proyecto-scouting-futbol"
# Elige la ubicación. Debe ser la misma que tu bucket.
LOCATION = "southamerica-west1" 
# Lista de todos los datasets que vamos a necesitar
DATASETS_TO_CREATE = ['raw_scouting', 'dwh_scouting', 'dm_scouting']

def create_bigquery_dataset(client, project_id, dataset_name, location):
    """
    Crea un dataset en BigQuery si no existe.
    """
    dataset_id = f"{project_id}.{dataset_name}"

    try:
        # Intenta obtener el dataset. Si no existe, lanzará una excepción NotFound.
        client.get_dataset(dataset_id)
        print(f"El dataset '{dataset_id}' ya existe.")
    except NotFound:
        print(f"El dataset '{dataset_id}' no existe. Creándolo...")
        # Si no existe, lo creamos.
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = location
        dataset = client.create_dataset(dataset, timeout=30)
        print(f"✓ Dataset '{dataset_id}' creado exitosamente en la ubicación '{location}'.")
    except Exception as e:
        print(f"❌ Error al intentar crear/verificar el dataset '{dataset_id}': {e}")


if __name__ == '__main__':
    # Inicializamos el cliente de BigQuery
    client = bigquery.Client(project=PROJECT_ID)

    print(f"Iniciando la configuración de datasets para el proyecto '{PROJECT_ID}'...")
    
    # Iteramos sobre la lista y llamamos a la función para cada dataset
    for name in DATASETS_TO_CREATE:
        create_bigquery_dataset(client, PROJECT_ID, name, LOCATION)
        
    print("\nConfiguración de datasets finalizada.")