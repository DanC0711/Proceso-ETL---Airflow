# ====================
# Importaciones y configuración general
# ====================
from __future__ import annotations
import pendulum
import pandas as pd
from google.cloud import storage, bigquery
import calendar
from io import BytesIO

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

# Configuración de variables globales
BUCKET_NAME = "etl-autorizaciones-datos"
ARCHIVOS = [
    "SRI_CONTRI_AUTO_OFICIO_COMP_ELECT_2022.csv",
    "SRI_CONTRI_AUTO_OFICIO_COMP_ELECT_2023.csv",
    "SRI_CONTRI_AUTO_OFICIO_COMP_ELECT_2024.csv"
]
PROJECT_ID = "etl-autorizaciones-sri"
DATASET_ID = "dw_autorizaciones"

# ====================
# Funciones de carga de dimensiones y hechos
# ====================

def cargar_dim_tiempo():
    """Carga la dimensión de tiempo en BigQuery."""
    client = bigquery.Client(project=PROJECT_ID)
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    fechas = pd.date_range(start="2022-01-01", end="2024-12-31", freq='D')
    df = pd.DataFrame({'fecha': fechas, 'dia': fechas.day, 'mes': fechas.month, 'nombre_mes': [calendar.month_name[m] for m in fechas.month], 'anio': fechas.year, 'dia_semana': fechas.dayofweek})
    df['id_fecha'] = df.index + 1
    client.load_table_from_dataframe(df, f"{PROJECT_ID}.{DATASET_ID}.dim_tiempo", job_config=job_config).result()

def cargar_dim_geografia():
    """Carga la dimensión geográfica (provincias) en BigQuery."""
    client = bigquery.Client(project=PROJECT_ID)
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    data = {"codigo_provincia": [f"{i:02}" for i in range(1, 25)], "provincia": ['Azuay', 'Bolívar', 'Cañar', 'Carchi', 'Cotopaxi', 'Chimborazo', 'El Oro', 'Esmeraldas', 'Guayas', 'Imbabura', 'Loja', 'Los Ríos', 'Manabí', 'Morona Santiago', 'Napo', 'Pastaza', 'Pichincha', 'Tungurahua', 'Zamora Chinchipe', 'Galápagos', 'Sucumbíos', 'Orellana', 'Santo Domingo de los Tsáchilas', 'Santa Elena']}
    df = pd.DataFrame(data)
    df['id_geografia'] = df.index + 1
    client.load_table_from_dataframe(df, f"{PROJECT_ID}.{DATASET_ID}.dim_geografia", job_config=job_config).result()

def cargar_dim_tipo_ruc():
    """Carga la dimensión de tipo de RUC en BigQuery."""
    client = bigquery.Client(project=PROJECT_ID)
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    data = {"tipo_ruc": ["Natural", "Privada", "Pública"], "descripcion": ["Persona natural", "Sociedad privada", "Entidad pública"], "digito_verificador": ["", "9", "6"]}
    df = pd.DataFrame(data)
    df['id_tipo_ruc'] = df.index + 1
    client.load_table_from_dataframe(df, f"{PROJECT_ID}.{DATASET_ID}.dim_tipo_ruc", job_config=job_config).result()

def cargar_dim_contribuyente():
    """Carga la dimensión de contribuyentes, corrigiendo el tipo de dato de 'codigo_provincia'."""
    client_bq = bigquery.Client(project=PROJECT_ID)
    storage_client = storage.Client()
    dfs = []
    for archivo in ARCHIVOS:
        blob = storage_client.bucket(BUCKET_NAME).get_blob(archivo)
        df = pd.read_csv(BytesIO(blob.download_as_string()), encoding='latin-1', sep=';', dtype=str)
        df.rename(columns={'NUMERO_RUC': 'numero_ruc', 'RAZON_SOCIAL': 'razon_social', 'FECHA_AUTORIZACIÓN_OFICIO': 'fecha_autorizacion'}, inplace=True)
        df['fecha_autorizacion'] = pd.to_datetime(df['fecha_autorizacion'], errors='coerce', dayfirst=True)
        dfs.append(df)
    
    df_all = pd.concat(dfs, ignore_index=True)
    df_all["numero_ruc"] = df_all["numero_ruc"].astype(str).str.zfill(13)
    
    dim_geo = client_bq.query(f"SELECT codigo_provincia, id_geografia FROM `{PROJECT_ID}.{DATASET_ID}.dim_geografia`").to_dataframe()
    dim_ruc = client_bq.query(f"SELECT tipo_ruc, id_tipo_ruc FROM `{PROJECT_ID}.{DATASET_ID}.dim_tipo_ruc`").to_dataframe()

    def extraer_prov_tipo(ruc):
        prov, tipo_char = ruc[:2], ruc[2]
        tipo_ruc_texto = "Pública" if tipo_char == "6" else "Privada" if tipo_char == "9" else "Natural"
        # --- CAMBIO CLAVE Y FINAL: Devolvemos 'prov' como el texto que es, sin convertir a int ---
        return prov, tipo_ruc_texto
    
    df_all[["codigo_provincia", "tipo_ruc_texto"]] = df_all["numero_ruc"].apply(lambda x: pd.Series(extraer_prov_tipo(x)))
    df_con = df_all.drop_duplicates("numero_ruc").copy()
    
    # El merge ahora funcionará porque ambas columnas 'codigo_provincia' son de tipo texto.
    df_con = df_con.merge(dim_geo, on="codigo_provincia", how="left")
    df_con = df_con.merge(dim_ruc, left_on="tipo_ruc_texto", right_on="tipo_ruc", how="left")
    
    df_contribuyentes = df_con[["numero_ruc", "razon_social", "id_tipo_ruc", "id_geografia"]].copy()
    df_contribuyentes.insert(0, 'id_contribuyente', range(1, 1 + len(df_contribuyentes)))

    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    client_bq.load_table_from_dataframe(df_contribuyentes, f"{PROJECT_ID}.{DATASET_ID}.dim_contribuyente", job_config=job_config).result()

def cargar_hechos_autorizaciones():
    """Carga la tabla de hechos de autorizaciones."""
    client = bigquery.Client(project=PROJECT_ID)
    storage_client = storage.Client()
    dfs = []
    for archivo in ARCHIVOS:
        blob = storage_client.bucket(BUCKET_NAME).get_blob(archivo)
        df = pd.read_csv(BytesIO(blob.download_as_string()), encoding='latin-1', sep=';', dtype=str)
        df.rename(columns={'NUMERO_RUC': 'numero_ruc', 'RAZON_SOCIAL': 'razon_social', 'FECHA_AUTORIZACIÓN_OFICIO': 'fecha_autorizacion'}, inplace=True)
        df['fecha_autorizacion'] = pd.to_datetime(df['fecha_autorizacion'], errors='coerce', dayfirst=True)
        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)
    df["numero_ruc"] = df["numero_ruc"].astype(str).str.zfill(13)
    df["fecha"] = df['fecha_autorizacion'].dt.date
    
    dim_contribuyente = client.query(f"SELECT id_contribuyente, numero_ruc FROM `{PROJECT_ID}.{DATASET_ID}.dim_contribuyente`").to_dataframe()
    dim_tiempo = client.query(f"SELECT id_fecha, fecha FROM `{PROJECT_ID}.{DATASET_ID}.dim_tiempo`").to_dataframe()
    dim_tiempo['fecha'] = pd.to_datetime(dim_tiempo['fecha']).dt.date
    
    df_merge = df.merge(dim_contribuyente, on="numero_ruc", how="left")
    df_merge = df_merge.merge(dim_tiempo, on="fecha", how="left")
    df_merge["cantidad_autorizaciones"] = 1
    df_final = df_merge[["id_fecha", "id_contribuyente", "cantidad_autorizaciones"]].dropna()
    df_final = df_final.astype({"id_fecha": "int64", "id_contribuyente": "int64"})

    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    client.load_table_from_dataframe(df_final, f"{PROJECT_ID}.{DATASET_ID}.hechos_autorizaciones", job_config=job_config).result()

with DAG(
    dag_id="etl_autorizaciones_sri_completo",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule=None,
    catchup=False,
    description="ETL DAG completo para autorizaciones SRI",
    tags=['etl', 'sri', 'gcp'],
) as dag:
    inicio = EmptyOperator(task_id='inicio')
    fin = EmptyOperator(task_id='fin')
    t_dim_tiempo = PythonOperator(task_id='cargar_dim_tiempo', python_callable=cargar_dim_tiempo)
    t_dim_geo = PythonOperator(task_id='cargar_dim_geografia', python_callable=cargar_dim_geografia)
    t_dim_ruc = PythonOperator(task_id='cargar_dim_tipo_ruc', python_callable=cargar_dim_tipo_ruc)
    t_dim_contribuyente = PythonOperator(task_id='cargar_dim_contribuyente', python_callable=cargar_dim_contribuyente)
    t_hechos = PythonOperator(task_id='cargar_hechos_autorizaciones', python_callable=cargar_hechos_autorizaciones)

    # Definición del flujo de dependencias entre tareas
    inicio >> [t_dim_tiempo, t_dim_geo, t_dim_ruc]
    [t_dim_geo, t_dim_ruc] >> t_dim_contribuyente
    [t_dim_tiempo, t_dim_contribuyente] >> t_hechos
    t_hechos >> fin