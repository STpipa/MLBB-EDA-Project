# eda_analysis.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import ast # Necesario para parsear las cadenas JSON anidadas

# Configuración inicial para mejorar la apariencia de los gráficos
sns.set_theme(style="whitegrid", palette="viridis")

# --- FUNCIONES AUXILIARES DE PARSEO ---

def extract_latest_win_rate(data_str):
    """Extrae el Win Rate del registro más reciente (último) en la columna 'data'."""
    if not isinstance(data_str, str) or pd.isna(data_str):
        return np.nan
    try:
        # 1. Convierte la string JSON a diccionario de Python
        data_dict = ast.literal_eval(data_str)
        
        # 2. Busca la lista de series de tiempo de 'win_rate'
        if 'win_rate' in data_dict and data_dict['win_rate']:
            # 3. Obtiene el último (más reciente) registro de la serie de tiempo
            latest_record = data_dict['win_rate'][-1]
            
            # 4. Extrae el valor de 'win_rate' de ese registro
            return latest_record.get('win_rate')
        
        return np.nan
    except Exception:
        return np.nan

def extract_roles(roles_str):
    """Extrae la lista de roles a partir de la columna anidada 'hero.data.sortid'."""
    if not isinstance(roles_str, str) or pd.isna(roles_str):
        return "Unknown"
    try:
        roles_list = ast.literal_eval(roles_str) 
        roles = [item['data']['sort_title'] for item in roles_list if isinstance(item, dict) and 'data' in item]
        return ', '.join(roles) if roles else "Unknown"
    except Exception:
        return "Unknown"

def extract_lane(lane_str):
    """Extrae la línea (Lane) principal a partir de la columna anidada 'hero.data.roadsort'."""
    if not isinstance(lane_str, str) or pd.isna(lane_str):
        return "Unknown"
    try:
        lane_list = ast.literal_eval(lane_str)
        if isinstance(lane_list[0], dict) and 'data' in lane_list[0]:
            return lane_list[0]['data']['road_sort_title']
        return "Unknown"
    except Exception:
        return "Unknown"

# --- ANÁLISIS 1: Win Rate por Rol ---

def analyze_win_rate_by_role():
    
    try:
        df = pd.read_csv("mobile_legends_data.csv")
        print("✔️ Datos cargados exitosamente. Iniciando EDA (Win Rate por Rol)...")
    except FileNotFoundError:
        print("❌ Error: Asegúrate de que 'mobile_legends_data.csv' esté en la misma carpeta.")
        return

    # 1. PASOS DE LIMPIEZA Y PARSEO (Doble Desanidamiento)
    
    # Renombrar columnas anidadas (para claridad, aunque se usa el nombre original en el apply)
    df.rename(columns={'hero.data.sortid': 'raw_roles'}, inplace=True)
    
    # 1.1. EXTRAER EL WIN RATE (Usando la columna 'data')
    df['win_rate'] = df['data'].apply(extract_latest_win_rate)
    
    # 1.2. EXTRAER EL ROL (Usando la columna 'raw_roles')
    df['role'] = df['raw_roles'].apply(extract_roles)
    
    # 2. Preparación final para el análisis de Rol
    df.dropna(subset=['win_rate'], inplace=True) # Eliminar héroes sin Win Rate (si los hay)
    df['primary_role'] = df['role'].apply(lambda x: x.split(',')[0].strip())
    df['win_rate_pct'] = df['win_rate'] * 100 # Convertir a porcentaje
    
    # 3. Agregación y Visualización
    role_performance = df.groupby('primary_role')['win_rate_pct'].mean().sort_values(ascending=False)
    
    plt.figure(figsize=(10, 6))
    bars = sns.barplot(x=role_performance.index, y=role_performance.values, palette="rocket")
    
    for bar in bars.patches:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height + 0.15, f'{height:.2f}%', ha='center', va='bottom', fontsize=9)
    
    plt.title('Tasa de Victoria Promedio por Rol Principal de Héroe', fontsize=16, pad=20)
    plt.xlabel('Rol Principal', fontsize=12)
    plt.ylabel('Tasa de Victoria Promedio (%)', fontsize=12)
    plt.ylim(role_performance.values.min() - 1, role_performance.values.max() + 2)
    plt.savefig("reports/win_rate_by_role.png")
    plt.show()

# --- ANÁLISIS 2: Win Rate por Línea (Lane) ---

def analyze_win_rate_by_lane():
    
    try:
        df = pd.read_csv("mobile_legends_data.csv")
        print("✔️ Iniciando EDA (Win Rate por Línea)...")
    except FileNotFoundError:
        return

    # 1. PASOS DE LIMPIEZA Y PARSEO (Doble Desanidamiento)
    
    # Renombrar columna anidada (para claridad)
    df.rename(columns={'hero.data.roadsort': 'raw_lanes'}, inplace=True)
    
    # 1.1. EXTRAER EL WIN RATE (Usando la columna 'data')
    df['win_rate'] = df['data'].apply(extract_latest_win_rate)
    
    # 1.2. EXTRAER LA LÍNEA (Usando la columna 'raw_lanes')
    df['lane'] = df['raw_lanes'].apply(extract_lane)

    # 2. Preparación final para el análisis de Línea
    df.dropna(subset=['lane', 'win_rate'], inplace=True)
    
    df['clean_lane'] = df['lane'].str.replace(':', '', regex=False).str.strip().str.capitalize()
    df['win_rate_pct'] = df['win_rate'] * 100
    
    # 3. Visualización
    plt.figure(figsize=(12, 7))
    
    sns.boxplot(
        x='clean_lane', 
        y='win_rate_pct', 
        data=df, 
        order=df['clean_lane'].value_counts().index, 
        palette="crest"
    )
    
    plt.title('Distribución de Tasa de Victoria (Win Rate) por Línea de Juego', fontsize=16, pad=20)
    plt.xlabel('Línea (Lane)', fontsize=12)
    plt.ylabel('Tasa de Victoria (%)', fontsize=12)
    plt.savefig("reports/win_rate_by_lane.png")
    plt.show()

    # eda_analysis.py (Añade esta función)

# --- ANÁLISIS 3: Gráfico de Dispersión (Scatter Plot) de Ban vs. Win Rate ---

def extract_latest_ban_rate(data_str):
    """Extrae el Ban Rate del registro más reciente."""
    if not isinstance(data_str, str) or pd.isna(data_str):
        return np.nan
    try:
        data_dict = ast.literal_eval(data_str)
        if 'win_rate' in data_dict and data_dict['win_rate']:
            latest_record = data_dict['win_rate'][-1]
            # Extrae el valor de 'ban_rate'
            return latest_record.get('ban_rate')
        return np.nan
    except Exception:
        return np.nan

def analyze_ban_vs_win_rate():
    """
    Genera un Scatter Plot de Tasa de Ban vs. Tasa de Victoria para identificar 
    héroes sobrevalorados y subestimados.
    """
    try:
        # Cargamos el archivo que ya tiene la última data
        df = pd.read_csv("mobile_legends_data.csv")
        print("✔️ Iniciando EDA (Ban Rate vs. Win Rate)...")
    except FileNotFoundError:
        return

    # 1. PASOS DE LIMPIEZA Y PARSEO (Usamos las funciones auxiliares existentes)
    
    # 1.1. EXTRAER EL WIN RATE y BAN RATE (Usando la columna 'data')
    df['win_rate'] = df['data'].apply(extract_latest_win_rate)
    df['ban_rate'] = df['data'].apply(extract_latest_ban_rate)
    
    # 1.2. EXTRAER EL NOMBRE DEL HÉROE
    df.rename(columns={'hero.data.name': 'hero_name'}, inplace=True)
    
    # 2. Preparación final
    df.dropna(subset=['win_rate', 'ban_rate'], inplace=True) 
    
    # Convertir a porcentaje (Win Rate * 100, Ban Rate * 100)
    df['win_rate_pct'] = df['win_rate'] * 100
    df['ban_rate_pct'] = df['ban_rate'] * 100
    
    # 3. Visualización
    plt.figure(figsize=(14, 8))
    
    # Scatter Plot con puntos de color según el Win Rate
    sns.scatterplot(
        x='ban_rate_pct', 
        y='win_rate_pct', 
        data=df, 
        hue='win_rate_pct', # Color por Win Rate
        size='ban_rate_pct', # Tamaño del punto por Ban Rate
        sizes=(20, 400), # Rango de tamaño de los puntos
        palette="coolwarm",
        legend=False
    )
    
    # 4. Etiquetado de héroes clave (los top 3 o los más relevantes)
    
    # Filtramos por los héroes más baneados/efectivos para etiquetarlos
    key_heroes = df.sort_values(by=['ban_rate_pct', 'win_rate_pct'], ascending=False).head(5)
    
    for _, row in key_heroes.iterrows():
        plt.annotate(
            row['hero_name'], 
            (row['ban_rate_pct'] + 0.005, row['win_rate_pct'] - 0.1), # Ajuste de posición
            fontsize=8, 
            color='black',
            weight='bold'
        )
    
    # 5. Etiquetas y título
    plt.title('Win Rate vs. Ban Rate: Identificando Héroes de Meta (Meta-Dominance)', fontsize=16, pad=20)
    plt.xlabel('Tasa de Ban (Ban Rate - %)', fontsize=12)
    plt.ylabel('Tasa de Victoria (Win Rate - %)', fontsize=12)
    plt.savefig("reports/ban_vs_win_rate.png")
    plt.show()


if __name__ == "__main__":
    analyze_win_rate_by_role() 
    analyze_win_rate_by_lane()
    analyze_ban_vs_win_rate()