import pandas as pd
import numpy as np
import ast
from datetime import datetime  
import os

# ---FUNCIÓN DE PARSEO: REUTILIZAMOS LA LÓGICA DE EDA---

# Las funciones auxiliares de limpieza deben ser ordenadas o re-definidas
# Aquí se re-definen para que 'reporting.py' sea independiente

def extract_roles(roles_str):
    if not isinstance(roles_str, str) or pd.isna(roles_str):
        return "Unknown"
    try:
        roles_list = ast.literal_eval(roles_str)
        roles = [item['data']['sort_title'] for item in roles_list if isinstance(item, dict) and 'data' in item]
        return ', '.join(roles) if roles else "Unknown"
    except Exception:
        return "Unknown"
    
def extract_latest_win_rate(data_str):
    if not isinstance(data_str, str) or pd.isna(data_str):
        return np.nan
    try:
        data_dict = ast.literal_eval(data_str)
        if 'win_rate' in data_dict and data_dict['win_rate']:
            # Tomamos el Win Rate más reciente de la serie de tiempo
            latest_record = data_dict['win_rate'][-1]
            return latest_record.get('win_rate')
        return np.nan
    except Exception:
        return np.nan
    
# ---FUNCIÓN PRINCIPAL DE REPORTING---

def generate_weekly_report():
    """
    Carga el historial, compara las dos ultimas fechas de extracción
    y genera un resumen de texto de las tendencias.
    """
    historical_file = 'D:/MLBB-EDA-Project/mobile_legends_data_historical.csv'
    if not os.path.exists(historical_file):
        print(f"Error: Archivo histórico '{historical_file}' no encontrado.")
        print("Asegúrate de ejecutar 'eda_mobilelegends.py' al menos dos veces para crear un historial.")
        return
    
    print("--- 🤖 GENERANDO REPORTE SEMANAL DE TENDENCIAS ---")

    df = pd.read_csv(historical_file)

    # 1. Limpieza y preparación de datos
    df['win_rate'] = df['data'].apply(extract_latest_win_rate)

    # 1.1 Renombrado y Creación de columna 'role'
    col_mapping = {'hero.data.sortid': 'raw_roles', 'hero.data.name': 'hero_name'}

    # Solo renombra si la columna existe para evitar errores
    df.rename(columns={k: v for k, v in col_mapping.items() if k in df.columns}, inplace=True)

    # La columna roles se crea ahora
    if 'raw_roles' in df.columns:
        df['role'] = df['raw_roles'].apply(extract_roles)
    else:
        # Esto sucede si 'hero.data.sortid' no se cargó o se renombró mal
        print("❌ Error: Columna fuente de roles ('hero.data.sortid' o 'raw_roles') no encontrada.")
        return

    df.dropna(subset=['win_rate', 'extraction_date'], inplace=True)

    # 2. Identificar las dos últimas fechas de extracción
    df['extraction_date'] = pd.to_datetime(df['extraction_date'])
    available_dates = sorted(df['extraction_date'].unique(), reverse=True)

    if len(available_dates) < 2:
        print("⚠️ Se necesita data de al menos 2 días/semanas para generar un reporte de tendencia.")
        return
    
    latest_date = available_dates[0]
    previous_date = available_dates[1]

    # Filtrar datos para las dos fechas
    df_latest = df[df['extraction_date'] == latest_date].copy()
    df_previous = df[df['extraction_date'] == previous_date].copy()

    print(f"Comparando datos del {previous_date.date()} con {latest_date.date()}...")

    # 3. Análisis de tendencia por rol
    df_latest['primary_role'] = df_latest['role'].apply(lambda x: x.split(',')[0].strip())
    df_previous['primary_role'] = df_previous['role'].apply(lambda x: x.split(',')[0].strip())

    # Calcular Win Rate promedio por rol en ambas fechas
    role_latest = df_latest.groupby('primary_role')['win_rate'].mean().rename('win_rate_latest')
    role_previous = df_previous.groupby('primary_role')['win_rate'].mean().rename('win_rate_previous')

    # Combinar y calcular la diferencia
    df_role_trend = pd.merge(role_latest, role_previous, left_index=True, right_index=True, how='inner')
    df_role_trend['change'] = (df_role_trend['win_rate_latest'] - df_role_trend['win_rate_previous']) * 100  # Cambio en puntos porcentuales

    # 4. Análisis de tendencia por héroe individuales
    # Nos centramos en el Win Rate individual para evitar sesgos de rol
    df_merged = pd.merge(
        df_latest[['hero_id', 'hero_name', 'win_rate', 'role']],
        df_previous[['hero_id', 'win_rate']],
        on='hero_id',
        suffixes=('_latest', '_previous')
    )
    df_merged['change'] = (df_merged['win_rate_latest'] - df_merged['win_rate_previous']) * 100  # Cambio en puntos porcentuales

    # 5. Generar un resumen de texto (Insights)
    report_text = f"--- 📊 REPORTE DE TENDENCIAS MLBB ({previous_date.date()} a {latest_date.date()}) ---\n\n"

    # Heróe que más subió
    top_gainer = df_merged.sort_values(by='change', ascending=False).iloc[0]
    report_text += f"🏆 Mayor ganador (Gainer): {top_gainer['hero_name']} ({top_gainer['role']})\n"
    report_text += f"   - Subió {top_gainer['change']:.2f} puntos porcentuales en Win Rate.\n\n"

    # Heróe que más cayó
    top_loser = df_merged.sort_values(by='change', ascending=True).iloc[0]
    report_text += f"💔 Mayor perdedor (Loser): {top_loser['hero_name']} ({top_loser['role']})\n"
    report_text += f"   - Cayó {abs(top_loser['change']):.2f} puntos porcentuales en Win Rate.\n\n"

    # Rol con mayor tendencia positiva
    best_role_trend = df_role_trend.sort_values(by='change', ascending=False).iloc[0]
    report_text += f"🚀 Rol en Ascenso: {best_role_trend.name}(cambio: {best_role_trend['change']:.2f}%)\n\n"

    # Rol con mayor tendencia negativa
    worst_role_trend = df_role_trend.sort_values(by='change', ascending=True).iloc[0]
    report_text += f"⚠️ Rol en Descenso: {worst_role_trend.name}(cambio: {worst_role_trend['change']:.2f}%)\n\n"
    
    # Guardar y mostrar el reporte
    report_filename = f"reports/reporte_tendencia_{latest_date.strftime('%Y%m%d')}.txt"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(report_text)
    print(f"Reporte guardado en: {report_filename}")


if __name__ == "__main__":
    generate_weekly_report()