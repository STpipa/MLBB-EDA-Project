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
| **Lenguaje** | Python | Lenguaje principal de desarrollo y análisis. |
| **Extracción** | `requests` | Realizar peticiones HTTP a la API de estadísticas. |
| **Manipulación** | `pandas` | Gestión, limpieza y transformación del DataFrame. |
| **Visualización** | `matplotlib`, `seaborn` | Creación de gráficos estadísticos de alto impacto. |

## ⚙️ Estructura del Repositorio