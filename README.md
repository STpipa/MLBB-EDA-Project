# ⚔️ MLBB Meta-Game Analysis: Análisis Exploratorio de Datos (EDA) de Mobile Legends: Bang Bang

## 🌟 Visión General del Proyecto

Este proyecto aplica la **Ciencia de Datos** y el **Análisis Exploratorio de Datos (EDA)** para desentrañar las dinámicas del "meta-juego" de **Mobile Legends: Bang Bang (MLBB)**. Utilizando datos extraídos directamente de la API de estadísticas del juego, el objetivo es transformar la intuición anecdótica en conocimiento accionable, fundamentado en evidencia empírica.

El análisis se centra en identificar patrones de rendimiento, correlaciones entre estadísticas clave y tendencias que definen la efectividad actual de héroes, roles y estrategias en el campo de batalla.

## 🎯 Objetivos Principales del EDA

1.  **Rendimiento por Rol:** Determinar el *Win Rate* y *Ban Rate* promedio de cada rol (Tank, Mage, Fighter, etc.) para identificar la clase más dominante.
2.  **Influencia de la Línea (Lane):** Analizar qué líneas (EXP, Gold, Mid, Roam, Jungle) presentan la mayor o menor tasa de victoria.
3.  **Héroes de Alta Prioridad:** Identificar a los héroes con la mejor relación Win Rate/Ban Rate y aquellos que están siendo subestimados.
4.  **Correlaciones de Estadísticas:** Explorar la relación entre métricas (ej., Win Rate vs. Popularidad) para entender el balance del juego.

## 🛠️ Tecnologías y Librerías

| Categoría | Herramienta | Propósito |
| :--- | :--- | :--- |
| **Lenguaje** | `Python` | Lenguaje principal de desarrollo y análisis. |
| **Extracción** | `requests` | Realizar peticiones HTTP a la API de estadísticas. |
| **Manipulación** | `pandas` | Gestión, limpieza y transformación del DataFrame. |
| **Visualización** | `matplotlib`, `seaborn`, `Plotly Express` | Creación de gráficos estadísticos de alto impacto. |
| **Dashboarding** | `Streamlit` | Creación de la aplicación web interactiva. |


## ⚙️ Estructura del Repositorio

| Archivo/Directorio             | Descripción                                           |
|--------------------------------|-------------------------------------------------------|
| `eda_mobilelegends.py`         | Script de extracción y limpieza (Pipeline ETL).        |
| `eda_analysis.py`              | Script principal para visualización y EDA.             |
| `config.py`                    | Contiene la variable `API_BASE_URL`.                  |
| `mobile_legends_data.csv`      | Dataset limpio y listo para el análisis (output).      |
| `README.md`                    | Documentación del proyecto (este archivo).             |


## 🚀 Fase de Extracción de Datos (ETL)

La fase de extracción se completó con éxito, asegurando la recolección de 130 registros de héroes únicos.

**Pipeline de Extracción:**
1.  **Posiciones (`/hero-position/`):** Extrae nombres, roles y líneas de juego.
2.  **Ratings (`/hero-rate/<id>/`):** Extrae la Tasa de Victoria (Win Rate), Tasa de Ban (Ban Rate) y Tasa de Aparición (Appearance Rate) para cada héroe individualmente.
3.  **Limpieza:** Se realiza la desanidación de datos (`pd.json_normalize`) y la unificación de claves (`hero_id`) para asegurar un **Merge** limpio y completo.

## 📈 Próximos Pasos (En Curso: EDA)

Actualmente, estamos en la fase de **Análisis Exploratorio de Datos (EDA)**. Los primeros análisis incluyen:

- [x] Análisis del Win Rate promedio por Rol.
- [x] Análisis de la distribución de Win Rate por Línea (Lane).
- [x] Gráfico de dispersión (Scatter Plot) de Ban Rate vs. Win Rate.

---

## 📊  MLBB Meta Dashboard (Streamlit)

Este proyecto culmina con un **Dashboard Interactivo de Streamlit** que permite a los usuarios:

1.  **Explorar la Dominancia del Meta:** Visualización de la relación entre el Win Rate y el Ban Rate de los héroes más recientes.
2.  **Análisis por Roles y Líneas:** Desglose del rendimiento (Win Rate) por Roles (Tank, Mage, etc.) y Líneas de Juego (EXP, Gold, etc.).
3.  **Detalle del Héroe:** Búsqueda individual de héroes para visualizar su tendencia histórica de Win Rate y sus métricas clave.

## ⏭️ Próximos Pasos / Mejora Continua

Las áreas de mejora futuras para el proyecto incluyen:

* **Implementación de Predicción:** Aplicar modelos de Series de Tiempo (como ARIMA) para proyectar el Win Rate futuro de los héroes.
* **Análisis Multivariado:** Estudiar la correlación entre las estadísticas de items y talentos (Emblems) con el rendimiento final del héroe.
* **Automatización (CI/CD):** Configurar GitHub Actions para actualizar automáticamente los datos de la API y desplegar el dashboard de Streamlit.


## 🤝 Atribución y Licencia

Este proyecto se adhiere a los requisitos de la Licencia BSD 3-Clause, bajo la cual se distribuye la API utilizada.

* **Juego:** Desarrollado y publicado por **Moonton**.
* **Fuente de Datos:** API de estadísticas desarrollada por **ridwaanhall**.

Los resultados de este análisis no son oficiales y se basan en datos públicos proporcionados por la API.