import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import ast # Para parsear strings de listas/diccionarios
from datetime import datetime
import os
from pandas import DataFrame

# ----------------------------------------------------
# ------------- 1. CONFIGURACIÓN ---------------------
# ----------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE_PATH = os.path.join(BASE_DIR,"..","data","mobile_legends_data_historical.csv")
REPORT_DIR = os.path.abspath(os.path.join(BASE_DIR,"..","reports")) # Carpeta para guardar los reportes/gráficos

# Asegurarse de que la carpeta de reportes exista
os.makedirs(REPORT_DIR, exist_ok=True)

# ----------------------------------------------------
# ----------- 2. FUNCIONES AUXILIARES ----------------
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
            # Verifica si la lista no está vacía antes de acceder a [-1]
            if data_dict['win_rate']:
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
            # Verifica si la lista no está vacía antes de acceder a [-1]
            if data_dict['win_rate']:
                return data_dict['win_rate'][-1].get('ban_rate')
        return np.nan
    except (ValueError, SyntaxError, TypeError):
        return np.nan

# ----------------------------------------------------
# --- 3. FUNCIONES DE ANÁLISIS Y VISUALIZACIÓN ---
# ----------------------------------------------------

def load_and_preprocess_data(file_path: str) -> DataFrame:
    try:
        df = pd.read_csv(file_path)
        # Aplicar las funciones de extracción para limpiar las columnas 'data' y 'hero.data.sortid'
        df['win_rate'] = df['data'].apply(extract_latest_win_rate)
        df['ban_rate'] = df['data'].apply(extract_latest_ban_rate)
        
        df.rename(columns={'hero.data.name': 'hero_name',
                        'hero.data.sortid': 'raw_roles'}, inplace=True)
        
        df['role'] = df['raw_roles'].apply(extract_roles)
        df['primary_role'] = df['role'].apply(lambda x: x.split(',')[0].strip()) # Para agrupar por rol principal
        
        df['win_rate_pct'] = df['win_rate'] * 100
        df['ban_rate_pct'] = df['ban_rate'] * 100
        
        df['extraction_date'] = pd.to_datetime(df['extraction_date'])

        # 🧩 Crear la columna 'lane_clean' si existe alguna con ese dato
        if 'lane' in df.columns:
            df['lane_clean'] = df['lane'].str.strip().fillna('Desconocido')
        elif 'data.lane' in df.columns:
            df['lane_clean'] = df['data.lane'].str.strip().fillna('Desconocido')
        else:
            df['lane_clean'] = 'Desconocido'
        
        # Eliminar filas con valores nulos en columnas críticas para el análisis
        df_clean = df.dropna(subset=['hero_name', 'win_rate_pct', 'ban_rate_pct', 'primary_role']).copy()
        
        return df_clean

    except FileNotFoundError:
        print(f"Error: El archivo '{file_path}' no fue encontrado.")
        return pd.DataFrame()
    except Exception as e:
        print(f"Ocurrió un error al cargar o preprocesar los datos: {e}")
        return pd.DataFrame()

def plot_win_rate_vs_ban_rate(df: DataFrame, current_date: str):
    """Genera un scatter plot de Win Rate vs Ban Rate y lo guarda."""
    
    if 'lane_clean' not in df.columns:
        print("⚠️ Columna 'lane_clean' no encontrada. No se puede generar el gráfico por Línea.")
        return
    
    df_grouped = df.groupby('lane_clean')['win_rate_pct'].mean().reset_index()

    plt.figure(figsize=(10, 6))
    sns.barplot(x='lane_clean', y='win_rate_pct', data=df_grouped, hue='lane_clean', palette="rocket", legend=False)

    plt.figure(figsize=(12, 8))
    sns.scatterplot(
        data=df,
        x='ban_rate_pct',
        y='win_rate_pct',
        hue='primary_role', # Colorear por rol principal
        size='win_rate_pct', # Tamaño de los puntos basado en Win Rate
        sizes=(50, 800), # Rango de tamaño de los puntos
        alpha=0.7,
        palette='viridis'
    )
    # Anotar los héroes más relevantes (ej. top 5 en Win Rate y Ban Rate)
    top_heroes = df.nlargest(5, 'win_rate_pct')
    for i, row in top_heroes.iterrows():
        plt.text(row['ban_rate_pct'] + 0.5, row['win_rate_pct'], row['hero_name'], 
                fontsize=9, weight='bold')

    plt.title(f'Win Rate vs Ban Rate de Héroes (Al {current_date})', fontsize=16)
    plt.xlabel('Tasa de Ban (%)', fontsize=12)
    plt.ylabel('Tasa de Victoria (%)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(title='Rol Principal', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORT_DIR, f"{current_date}_ban_vs_win_rate.png"))
    plt.close()
    print(f"📈 Gráfico de Win Rate vs Ban Rate guardado en {os.path.join(REPORT_DIR, f'{current_date}_ban_vs_win_rate.png')}")

def plot_win_rate_by_role(df, current_date):
    """Genera un box plot del Win Rate por rol principal y lo guarda."""
    plt.figure(figsize=(12, 8))
    sns.boxplot(data=df, x='primary_role', y='win_rate_pct', hue='primary_role', palette='coolwarm', legend=False)
    plt.title(f'Distribución de Win Rate por Rol Principal (Al {current_date})', fontsize=16)
    plt.xlabel('Rol Principal', fontsize=12)
    plt.ylabel('Tasa de Victoria (%)', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(REPORT_DIR, f"{current_date}_win_rate_by_role.png"))
    plt.close()
    print(f"📊 Gráfico de Win Rate por Rol guardado en {os.path.join(REPORT_DIR, f'{current_date}_win_rate_by_role.png')}")

def plot_win_rate_by_lane(df: DataFrame, current_date: str):
    """
    Calcula y grafica el Win Rate promedio por Línea (Lane).
    """
    # 1. Agrupar por la columna de Línea
    # NOTA: Asegúrate que la columna 'lane_clean' o similar exista en tu DataFrame limpio.
    if 'lane_clean' not in df.columns:
        print("⚠️ Columna 'lane_clean' no encontrada. No se puede generar el gráfico por Línea.")
        return

    df_grouped = df.groupby('lane_clean')['win_rate_pct'].mean().reset_index()

    plt.figure(figsize=(10, 6))
    sns.barplot(x='lane_clean', y='win_rate_pct', data=df_grouped, hue='lane_clean', palette="rocket", legend=False)
    
    # Añadir etiquetas de valor
    for index, row in df_grouped.iterrows():
        plt.text(index, row['win_rate_pct'] + 0.1, 
                f"{row['win_rate_pct']:.2f}%", 
                color='black', ha="center")

    plt.title('Win Rate Promedio por Línea (Lane)')
    plt.xlabel('Línea (Lane)')
    plt.ylabel('Win Rate Promedio (%)')
    plt.ylim(df_grouped['win_rate_pct'].min() * 0.9, df_grouped['win_rate_pct'].max() * 1.1)
    plt.tight_layout()

    # Guardar con el nombre solicitado: win_rate_by_lane.png
    file_name = os.path.join(REPORT_DIR, f"{current_date}_win_rate_by_lane.png")
    plt.savefig(file_name)
    plt.close()
    print(f"📊 Gráfico de Win Rate por Línea guardado en {file_name}")

# ----------------------------------------------------
# --- 4. FUNCIÓN PRINCIPAL DE EJECUCIÓN DEL ANÁLISIS ---
# ----------------------------------------------------

def run_eda_analysis():
    print("Iniciando Análisis Exploratorio de Datos (EDA)...")
    
    df_historical = load_and_preprocess_data(DATA_FILE_PATH)
    
    if df_historical.empty:
        print("No se pudo cargar o preprocesar los datos. Saliendo del EDA.")
        return

    latest_date = df_historical['extraction_date'].max()
    print(f"Analizando datos hasta la última fecha de extracción: {latest_date.strftime('%Y-%m-%d')}")

    # Filtrar datos de la fecha más reciente para los gráficos de meta actual
    df_latest = df_historical[df_historical['extraction_date'] == latest_date].copy()

    if df_latest.empty:
        print("No hay datos para la fecha más reciente. No se generarán gráficos.")
        return

    # Generar y guardar los gráficos
    plot_win_rate_vs_ban_rate(df_latest, latest_date.strftime('%Y%m%d'))
    plot_win_rate_by_role(df_latest, latest_date.strftime('%Y%m%d'))
    plot_win_rate_by_lane(df_latest,latest_date.strftime('%Y%m%d'))
    print("EDA completado y gráficos generados.")

# ----------------------------------------------------
# --- 5. EJECUCIÓN DEL SCRIPT ---
# ----------------------------------------------------
if __name__ == "__main__":
    run_eda_analysis()