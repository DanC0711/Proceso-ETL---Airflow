
# ❄️ ETL Autorizaciones SRI

Pipeline ETL diseñado para automatizar la extracción, transformación y carga de datos de autorizaciones emitidas por el Servicio de Rentas Internas (SRI) del Ecuador. El sistema está implementado en **Google Cloud Platform (GCP)** utilizando **Apache Airflow (local en Docker)**, **BigQuery** y **Cloud Storage**, permitiendo una integración reproducible, trazable y escalable para el análisis de datos tributarios mediante un modelo **copo de nieve**.

---

## 🎯 Objetivo General

Automatizar la ingesta y transformación de los registros de autorizaciones emitidas por el SRI a contribuyentes, organizados bajo un **modelo dimensional copo de nieve**, que permita consultas analíticas eficientes y generación de reportes OLAP.

---

## 🧰 Herramientas y Tecnologías Utilizadas

| Tecnología | Descripción |
|-----------|-------------|
| **Google Cloud Platform (GCP)** | Infraestructura en la nube |
| **Google Cloud Storage (GCS)** | Almacenamiento de archivos fuente `.csv` |
| **Google BigQuery** | Almacén de datos (Data Warehouse) |
| **Apache Airflow (Docker)** | Orquestador ETL desplegado de forma local |
| **Python 3** | Lenguaje principal del pipeline |
| **Pandas** | Transformación y limpieza de datos |
| **google-cloud-storage** | Cliente Python para GCS |
| **google-cloud-bigquery** | Cliente Python para BigQuery |
| **PyArrow** | Backend de exportación para pandas |
| **Docker** | Contenedor de ejecución para Airflow |

---

## 🧱 Arquitectura del Proyecto

```
+--------------------------+       +---------------------------+       +---------------------------+
| 📥 Archivos CSV (SRI)    | --->  | ☁️ Google Cloud Storage    | --->  | 🐳 Apache Airflow (Docker) |
| (2022, 2023, 2024)       |       | (3 archivos cargados)     |       | (Transformación ETL)      |
+--------------------------+       +---------------------------+       +---------------------------+
                                                                              |
                                                                              v
                                                                    +-------------------------+
                                                                    | 📊 BigQuery DW           |
                                                                    | Modelo Copo de Nieve     |
                                                                    +-------------------------+
```

---

## 📦 Componentes Principales

| Componente | Descripción |
|------------|-------------|
| **Cloud Storage** | Contiene los archivos fuente `.csv` |
| **Airflow (Docker)** | Ejecuta el DAG localmente con tareas programadas |
| **BigQuery** | Almacena las tablas del modelo copo de nieve |
| **Python (pandas)** | Realiza la transformación, joins y validación |

---

## ❄️ Modelo Dimensional - Esquema Copo de Nieve

| Tabla | Descripción |
|-------|-------------|
| **hechos_autorizaciones** | Tabla de hechos principal con autorizaciones emitidas |
| **dim_contribuyente** | Información única por RUC (nombre, tipo y ubicación) |
| **dim_tiempo** | Dimensión temporal por día |
| **dim_geografia** | Subdimensión: Provincias del Ecuador |
| **dim_tipo_ruc** | Subdimensión: Tipos de contribuyentes (Natural, Privada, Pública) |

---

## 🛠️ Requisitos del Entorno

### 1. Infraestructura

- Bucket GCS creado: `etl-autorizaciones-datos`
- Dataset BigQuery: `dw_autorizaciones`
- Airflow ejecutándose localmente en Docker

### 2. Permisos y Credenciales

Cuenta de servicio con los siguientes roles:

- `roles/bigquery.dataEditor`
- `roles/bigquery.jobUser`
- `roles/storage.objectViewer`
- `roles/storage.admin`

> Guardar las credenciales `.json` en la carpeta `/include` de Airflow local o montarlas como volumen.

### 3. Librerías Python necesarias

```bash
pip install pandas pyarrow
pip install google-cloud-bigquery google-cloud-storage google-auth
```

---

## 🧬 Estructura del DAG en Airflow

```
etl_autorizaciones_sri_completo
├── inicio
├── cargar_dim_tiempo
├── cargar_dim_geografia
├── cargar_dim_tipo_ruc
├── cargar_dim_contribuyente
├── cargar_hechos_autorizaciones
└── fin
```

### Función de cada tarea

| Tarea | Descripción |
|-------|-------------|
| `inicio` | Inicio del flujo ETL |
| `cargar_dim_tiempo` | Genera fechas del 2022 al 2024 |
| `cargar_dim_geografia` | Carga provincias de Ecuador |
| `cargar_dim_tipo_ruc` | Crea tipos de contribuyentes |
| `cargar_dim_contribuyente` | Une RUC con provincia y tipo |
| `cargar_hechos_autorizaciones` | Realiza join y carga de hechos |
| `fin` | Finaliza el flujo |

---

## 📂 Ubicación del DAG y Credenciales

- DAG `.py` debe ser montado en el contenedor: `./dags/etl_autorizaciones_sri_completo.py`
- Credenciales GCP: `./include/key-etl-sri.json`

---

## ✅ Resultados Esperados

- Tablas `dim_*` y `hechos_autorizaciones` en BigQuery pobladas correctamente.
- Claves foráneas resueltas entre contribuyentes, tipos de RUC, geografía y tiempo.
- Airflow muestra DAG en estado exitoso (✅ verde).
- Posibilidad de consultas OLAP inmediatas en BigQuery.

---

## 📷 Evidencias

- Ejecución exitosa del DAG en Airflow.
- Conteo de registros en BigQuery:
```sql
SELECT COUNT(*) FROM `dw_autorizaciones.hechos_autorizaciones`;
```
- Validación de claves foráneas con joins:
```sql
SELECT COUNT(*) 
FROM `dw_autorizaciones.hechos_autorizaciones` h
JOIN `dw_autorizaciones.dim_contribuyente` c ON h.id_contribuyente = c.id_contribuyente;
```

---

## 📚 Recursos Adicionales

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Google BigQuery Python Client](https://cloud.google.com/bigquery/docs/reference/libraries)
- [SRI Ecuador](https://www.sri.gob.ec/)

---

## 👨‍💻 Autor

**Danilo Guillermo Camacho León**  
Estudiante de Ingeniería de Software  
Escuela Superior Politécnica de Chimborazo (ESPOCH)  
Proyecto académico: ETL Autorizaciones SRI

