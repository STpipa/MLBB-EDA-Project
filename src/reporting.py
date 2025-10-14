import pandas as pd
import numpy as np
import ast
from datetime import datetime
import os

# ----------------------------------------------------
# ------------- 1. CONFIGURACIÓN ---------------------
# ----------------------------------------------------

# Ruta relativa al archivo de datos, sube un nivel (..) y entra a 'data/'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE_PATH = os.path.join(BASE_DIR, "..", "data", "mobile_legends_data_historical.csv")
REPORT_OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reports'))

# Asegurarse de que la carpeta de reportes exista
os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)

# ----------------------------------------------------
# ------ 2. FUNCIONES AUXILIARES DE PARSEO -----------
# ----------------------------------------------------

def extract_roles(roles_str):
    if not isinstance(roles_str, str) or pd.isna(roles_str):
        return "Unknown"
    try:
        roles_list = ast.literal_eval(roles_str)
        roles = [item['data']['sort_title'] for item in roles_list if isinstance(item, dict) and 'data' in item and 'sort_title' in item['data']]
        return ', '.join(roles) if roles else "Unknown"
    except (ValueError, SyntaxError, TypeError):
        return "Unknown"

def extract_latest_win_rate(data_str):
    if not isinstance(data_str, str) or pd.isna(data_str):
        return np.nan
    try:
        data_dict = ast.literal_eval(data_str)
        if 'win_rate' in data_dict and data_dict['win_rate']:
            if data_dict['win_rate']: # Asegurarse de que la lista no esté vacía
                return data_dict['win_rate'][-1].get('win_rate')
        return np.nan
    except (ValueError, SyntaxError, TypeError):
        return np.nan

def extract_latest_ban_rate(data_str):
    if not isinstance(data_str, str) or pd.isna(data_str):
        return np.nan
    try:
        data_dict = ast.literal_eval(data_str)
        if 'win_rate' in data_dict and data_dict['win_rate']:
            if data_dict['win_rate']: # Asegurarse de que la lista no esté vacía
                return data_dict['win_rate'][-1].get('ban_rate') 
        return np.nan
    except (ValueError, SyntaxError, TypeError):
        return np.nan

# ----------------------------------------------------
# --- 3. FUNCIONES DE CARGA Y PREPROCESAMIENTO ---
# ----------------------------------------------------

def load_and_preprocess_data(file_path):
    print(f"\n🔍 Leyendo archivo desde: {os.path.abspath(file_path)}")
    try:
        df = pd.read_csv(file_path)
        print("📅 Fechas únicas detectadas:", df['extraction_date'].unique())
        
        # Aplicar las funciones de extracción
        df['win_rate'] = df['data'].apply(extract_latest_win_rate)
        df['ban_rate'] = df['data'].apply(extract_latest_ban_rate)
        
        df.rename(columns={'hero.data.name': 'hero_name',
                        'hero.data.sortid': 'raw_roles'}, inplace=True)
        
        df['role'] = df['raw_roles'].apply(extract_roles)
        df['primary_role'] = df['role'].apply(lambda x: x.split(',')[0].strip())
        
        df['win_rate_pct'] = df['win_rate'] * 100
        df['ban_rate_pct'] = df['ban_rate'] * 100
        
        df['extraction_date'] = pd.to_datetime(df['extraction_date'])
        
        # Eliminar filas con valores nulos en columnas críticas para el análisis
        df_clean = df.dropna(subset=['hero_name', 'win_rate_pct', 'ban_rate_pct', 'primary_role']).copy()
        
        return df_clean

    except FileNotFoundError:
        print(f"Error: El archivo '{file_path}' no fue encontrado.")
        return pd.DataFrame()
    except Exception as e:
        print(f"Ocurrió un error al cargar o preprocesar los datos: {e}")
        return pd.DataFrame()

# ----------------------------------------------------
# --- 4. FUNCIÓN PARA GENERAR EL REPORTE DE TEXTO ---
# ----------------------------------------------------

def generate_report():
    print("Generando reporte de tendencias del meta...")
    
    df_historical = load_and_preprocess_data(DATA_FILE_PATH)
    
    if df_historical.empty:
        return "ERROR: No se pudo cargar o preprocesar los datos para generar el reporte."

    latest_date = df_historical['extraction_date'].max()
    df_latest = df_historical[df_historical['extraction_date'] == latest_date].copy()
    
    if df_latest.empty:
        return "ERROR: No hay datos recientes para generar el reporte."

    report_content = []
    report_content.append(f"--- Reporte de Tendencia del Meta de MLBB ({latest_date.strftime('%Y-%m-%d')}) ---\n")
    report_content.append("Este reporte analiza los cambios más significativos en el meta del juego.\n")

    # Top 5 Héroes con mayor Win Rate
    top_win_rate = df_latest.nlargest(5, 'win_rate_pct')
    report_content.append("\n 👑 Top 5 Héroes por Tasa de Victoria:")
    for _, row in top_win_rate.iterrows():
        report_content.append(f"- {row['hero_name']}: {row['win_rate_pct']:.2f}% Win Rate ({row['primary_role']})")

    # Top 5 Héroes con mayor Ban Rate
    top_ban_rate = df_latest.nlargest(5, 'ban_rate_pct')
    report_content.append("\n 🚫 Top 5 Héroes por Tasa de Ban:")
    for _, row in top_ban_rate.iterrows():
        report_content.append(f"- {row['hero_name']}: {row['ban_rate_pct']:.2f}% Ban Rate ({row['primary_role']})")

    # Héroes con mayor cambio de Win Rate (requiere datos históricos de al menos 2 fechas)
    if len(df_historical['extraction_date'].unique()) >= 2:
        df_prev_date = df_historical.sort_values(by='extraction_date', ascending=False).drop_duplicates(subset=['hero_name'])
        
        # Obtener datos de la penúltima fecha
        second_latest_date = df_historical['extraction_date'].unique()[-2]
        df_previous = df_historical[df_historical['extraction_date'] == second_latest_date].copy()

        # Fusionar para calcular el cambio
        df_merged = pd.merge(df_latest[['hero_name', 'win_rate_pct']], 
                        df_previous[['hero_name', 'win_rate_pct']], 
                        on='hero_name', 
                        suffixes=('_latest', '_previous'))
        
        df_merged['win_rate_change'] = df_merged['win_rate_pct_latest'] - df_merged['win_rate_pct_previous']
        
        top_gainers = df_merged.nlargest(3, 'win_rate_change')
        top_losers = df_merged.nsmallest(3, 'win_rate_change')

        report_content.append("\n 🚀 Héroes con Mayor Ganancia de Win Rate (vs. última semana):")
        for _, row in top_gainers.iterrows():
            report_content.append(f"- {row['hero_name']}: +{row['win_rate_change']:.2f} pp")

        report_content.append("\ 📉 Héroes con Mayor Pérdida de Win Rate (vs. última semana):")
        for _, row in top_losers.iterrows():
            report_content.append(f"- {row['hero_name']}: {row['win_rate_change']:.2f} pp")
            
    else:
        report_content.append("\nNo hay suficientes datos históricos para calcular cambios de Win Rate.")


    report_text = "\n".join(report_content)
    
    # Guardar el reporte en la carpeta de reports
    file_name = os.path.join(REPORT_OUTPUT_DIR, f"reporte_tendencia_{latest_date.strftime('%Y%m%d')}.txt")
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"📝 Reporte de tendencias guardado en '{file_name}'")
    
    return report_text

# ----------------------------------------------------
# --- 5. EJECUCIÓN DEL SCRIPT ---
# ----------------------------------------------------
if __name__ == "__main__":
    generate_report()