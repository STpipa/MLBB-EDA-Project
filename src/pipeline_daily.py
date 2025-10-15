import os
import subprocess
from datetime import datetime
from src.eda_mobilelegends import data_extraction_pipeline
from src.eda_analysis import run_eda_analysis
from src.reporting import generate_report
import sys

# Agregamos la ruta del directorio padre al path de Python 
# para que las importaciones de 'src.modulo' funcionen si es necesario.
# Aunque 'python -m src.pipeline_daily' ya lo maneja, es más seguro.
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Importamos las funciones principales de los scripts de recolección y analisis
"""try:
    from src.eda_mobilelegends import data_extraction_pipeline
    from src.eda_analysis import run_eda_analysis
    from src.reporting import generate_report
except ImportError as e:
    print(f" Error en la importación: Verifique las rutas de los archivos y nombres de funciones. {e}")
    exit(1) # Salir si no se puede importar"""


def run_daily_pipeline():
    """
    Función principal que orquesta la ejecución completa del pipeline de datos.
    """
    print(f"=====================================================")
    print(f"🚀 INICIANDO PIPELINE DIARIO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"=====================================================")

    # 1. ETAPA: EXTRACCIÓN Y LIMPIEZA (ETL)
    print(f"\n--- 1. Ejecutando Extracción(eda_mobilelegends) ---")
    df_new_data = data_extraction_pipeline()

    if df_new_data is None or df_new_data.empty:
        print("🔴 ERROR CRÍTICO: No se pudieron extraer datos. Deteniendo pipeline.")
        return
    
    print("--- 2. ETAPA: ANÁLISIS EXPLORATORIO DE DATOS (EDA)")
    run_eda_analysis() 
    
    # 2. ETAPA: GENERACIÓN DE GRÁFICOS (EDA analysis)
    print("\n--- 3. Ejecutando Análisis y Generación de Gráficos (eda_analysis) ---")
    generate_report()

    # 3. ETAPA: GENERACIÓN DE REPORTES (reporting)
    print("\n--- 3. Generando Reportes (reporting) ---")
    # Al ejecutar desde la raíz (D:\MLBB-EDA-Project), la ruta debe ser 'src/streamlit_dashboard.py'
    streamlit_command = "streamlit run src/streamlit_dashboard.py"

    try:
        # Usamos subprocess.Popen para que el dashboard corra en segundo plano
        subprocess.Popen(streamlit_command, shell=True) 
        print("✨ Dashboard de Streamlit iniciado en segundo plano. Abra su navegador (http://localhost:8501).")
    except FileNotFoundError:
        print("❌ Error: Asegúrate de que 'streamlit' esté instalado y en tu PATH.")
    except Exception as e:
        print(f"❌ Error al intentar iniciar Streamlit: {e}")

    print(f"=====================================================")
    print("✅ PIPELINE DIARIO COMPLETADO. Datos y reportes actualizados.")
    print("=====================================================")

if __name__ == "__main__":
    run_daily_pipeline()

    # 4. ETAPA: INICIAR EL DASHBOARD (Streamlit)
    # Usamos subprocess para lanzar el dasboard, pero el pipeline ya terminó
    print("\n--- 4. Iniciando Streamlit Dashboard")
    