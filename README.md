# 📊 AutorizacionesSRI_ETL

Pipeline ETL desarrollado para automatizar la carga, transformación y orquestación de datos del Servicio de Rentas Internas del Ecuador (SRI), específicamente sobre contribuyentes autorizados por oficio para emitir comprobantes electrónicos. Utiliza Apache Airflow en un entorno Docker local, Google Cloud Storage y BigQuery. Implementa un esquema de modelo dimensional tipo **copo de nieve (snowflake)** en el Data Warehouse.

---

## 🎯 Objetivo General

Automatizar el proceso de carga y transformación de datos abiertos del SRI, estructurándolos en un modelo de datos Snowflake dentro de BigQuery, para facilitar análisis OLAP, generación de reportes y consultas analíticas complejas sobre el comportamiento de las autorizaciones tributarias a nivel nacional.

---

## 🛠️ Herramientas y Tecnologías Utilizadas

| Herramienta | Descripción |
|------------|-------------|
| 🐳 Docker + Docker Compose | Entorno local para ejecutar Airflow sin depender de infraestructura externa |
| 🌬️ Apache Airflow | Orquestador ETL que organiza tareas dependientes por DAG |
| ☁️ Google Cloud Storage (GCS) | Almacenamiento de archivos CSV del SRI |
| 📘 Google BigQuery | Data Warehouse escalable para almacenamiento analítico |
| 🐍 Python 3 | Lenguaje de desarrollo principal |
| 📦 Pandas | Procesamiento y transformación de datos |
| 📦 google-cloud-bigquery | Cliente de Python para BigQuery |
| 📦 google-cloud-storage | Cliente de Python para Cloud Storage |
| 🔐 google-auth | Manejador de credenciales de acceso GCP |

---

## 🧱 Arquitectura del Proyecto

```plaintext
+------------------------+      +----------------------------+      +-------------------------------+
| 📁 Archivos CSV (SRI)  | ---> | ☁️ Cloud Storage (GCS)      | ---> | 🐳 Apache Airflow (DAG local)  |
| (Años 2022-2024)       |      | (3 archivos CSV)           |      | (Extracción y transformación) |
+------------------------+      +----------------------------+      +-------------------------------+
                                                                        |
                                                                        v
                                                               +-------------------------+
                                                               | 📊 BigQuery DW           |
                                                               | (Modelo Snowflake)       |
                                                               +-------------------------+
```

---

## 📚 Modelo Dimensional - Snowflake

### Tablas Dimensión

| Tabla               | Descripción                                     |
|--------------------|-------------------------------------------------|
| `dim_tiempo`        | Días individuales con atributos como mes y año |
| `dim_geografia`     | Provincias del Ecuador                         |
| `dim_tipo_ruc`      | Clasificación del RUC: Natural, Privado, Público |
| `dim_contribuyente` | Contribuyentes únicos, enlazados con tipo y geografía |

### Tabla de Hechos

| Tabla                  | Métricas |
|------------------------|----------|
| `hechos_autorizaciones` | Número de autorizaciones por fecha y contribuyente |

---

## 🗂️ DAG en Apache Airflow

**Nombre del DAG:** `etl_autorizaciones_sri_completo`

### Estructura del DAG

```plaintext
etl_autorizaciones_sri_completo
├── inicio
├── cargar_dim_tiempo
├── cargar_dim_geografia
├── cargar_dim_tipo_ruc
├── cargar_dim_contribuyente
├── cargar_hechos_autorizaciones
└── fin
```

### Flujo de Dependencias

```plaintext
inicio
 └─► [dim_tiempo, dim_geografia, dim_tipo_ruc]
              └─► dim_contribuyente
                        └─► hechos_autorizaciones
                                  └─► fin
```
![image](https://github.com/user-attachments/assets/2264935b-01b7-4609-afaa-868dd40b3c3f)

---

## 📌 Consulta SQL General de Validación

```sql
SELECT 
  f.id_fecha,
  t.fecha,
  c.numero_ruc,
  c.razon_social,
  tr.tipo_ruc,
  g.provincia,
  COUNT(*) AS total_autorizaciones
FROM `etl-autorizaciones-sri.dw_autorizaciones.hechos_autorizaciones` f
JOIN `etl-autorizaciones-sri.dw_autorizaciones.dim_tiempo` t ON f.id_fecha = t.id_fecha
JOIN `etl-autorizaciones-sri.dw_autorizaciones.dim_contribuyente` c ON f.id_contribuyente = c.id_contribuyente
JOIN `etl-autorizaciones-sri.dw_autorizaciones.dim_geografia` g ON c.id_geografia = g.id_geografia
JOIN `etl-autorizaciones-sri.dw_autorizaciones.dim_tipo_ruc` tr ON c.id_tipo_ruc = tr.id_tipo_ruc
GROUP BY f.id_fecha, t.fecha, c.numero_ruc, c.razon_social, tr.tipo_ruc, g.provincia
ORDER BY t.fecha
LIMIT 100;
```
![image](https://github.com/user-attachments/assets/e2848084-b128-4139-9c15-17e13843ebe6)

## 📌 Consulta SQL Para Graficos
```sql
SELECT 
  f.id_fecha,
  t.fecha,
  c.numero_ruc,
  c.razon_social,
  tr.tipo_ruc,
  g.provincia,
  COUNT(*) AS total_autorizaciones
FROM `etl-autorizaciones-sri.dw_autorizaciones.hechos_autorizaciones` f
JOIN `etl-autorizaciones-sri.dw_autorizaciones.dim_tiempo` t ON f.id_fecha = t.id_fecha
JOIN `etl-autorizaciones-sri.dw_autorizaciones.dim_contribuyente` c ON f.id_contribuyente = c.id_contribuyente
JOIN `etl-autorizaciones-sri.dw_autorizaciones.dim_geografia` g ON c.id_geografia = g.id_geografia
JOIN `etl-autorizaciones-sri.dw_autorizaciones.dim_tipo_ruc` tr ON c.id_tipo_ruc = tr.id_tipo_ruc
GROUP BY f.id_fecha, t.fecha, c.numero_ruc, c.razon_social, tr.tipo_ruc, g.provincia
ORDER BY t.fecha
LIMIT 100;
```
![image](https://github.com/user-attachments/assets/ba717c9f-2126-4d6c-bca2-709b0393d774)


## ✅ Evidencia de Ejecución Exitosa

- ✔️ DAG `etl_autorizaciones_sri_completo` ejecutado exitosamente en Airflow local.
- ✔️ Todas las tareas marcaron estado `Success`.

  ![image](https://github.com/user-attachments/assets/9b61ea5a-e5c5-444d-b0b7-1819f36db2f5)
  
- ✔️ BigQuery poblado con:
  - `dim_tiempo`: ~1096 registros
  
   ![image](https://github.com/user-attachments/assets/3f483181-4c8f-4bcd-942f-56e87ce871a1)


  - `dim_geografia`: 24 registros
  - `dim_tipo_ruc`: 3 registros

   ![image](https://github.com/user-attachments/assets/fa117273-3c6e-495c-8306-cd9d3511ebf5)

  - `dim_contribuyente`: ~966,157 registros únicos
    
   ![image](https://github.com/user-attachments/assets/d841eb84-4f0f-4663-a2b5-91192c87ccf0)
  
  - `hechos_autorizaciones`: ~966,288 registros
    
   ![image](https://github.com/user-attachments/assets/339f5ee5-65c7-4df6-bc2b-fbef8a352a24)

---

## 🧩 Tabla de Incidencias y Soluciones

| Nº | Categoría | Problema | Causa Técnica | Solución |
|----|-----------|----------|----------------|----------|
| 1.1 | Docker | Error `.env` con `echo` en Windows | Incompatibilidad CMD/Powershell | Se omitió el archivo; Airflow toma UID por defecto |
| 1.2 | Docker | Daemon inaccesible | Docker Desktop no iniciado | Se verificó que Docker estuviera ejecutándose |
| 2.1 | Airflow | `airflow-apiserver` no saludable | Falta `jwt_secret` | Se definió en variable de entorno |
| 2.2 | Dependencias | `pandas` no instalado | No incluido en imagen oficial | Se usó `_PIP_ADDITIONAL_REQUIREMENTS` |
| 3.1 | GCP | Error de autenticación | Variable `GOOGLE_APPLICATION_CREDENTIALS` ausente | Se montó archivo JSON y se definió variable |
| 4.1 | pandas | Error de codificación | CSV en `latin-1` | Se añadió `encoding='latin-1'` |
| 4.2 | pandas | Error de delimitador | Usaba `;` en vez de `,` | Se añadió `sep=';'` |
| 4.3 | pandas | Columnas no encontradas | Diferencia en nombres con tildes | Se usó `rename()` |
| 4.4 | pandas | Merge con tipos distintos | `str` vs `int` en `codigo_provincia` | Se forzó a `str` |
| 4.5 | Memoria | DAG finalizado por OOM | Exceso de carga simultánea | Se aumentó RAM y se propuso procesamiento por lotes |

---

## 📚 Recursos Adicionales

- [Apache Airflow Docs](https://airflow.apache.org/docs/)
- [BigQuery Python Client](https://cloud.google.com/python/docs/reference/bigquery/latest)
- [Servicio de Rentas Internas del Ecuador (SRI)](https://www.sri.gob.ec](https://www.sri.gob.ec/datasets)

---

## 👨‍💻 Autor

**Danilo Guillermo Camacho León**  
Estudiante de Ingeniería de Software – Proyecto Académico  
Escuela Superior Politécnica de Chimborazo – ESPOCH  
2025
