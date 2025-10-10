import streamlit as st
import pandas as pd
import plotly.express as px
import ast 
import numpy as np
from datetime import datetime
import os

# --- FUNCIONES AUXILIARES GLOBALES ---

def extract_roles(roles_str):
    if not isinstance(roles_str, str):
        return "Unknown"
    try:
        roles_list = ast.literal_eval(roles_str)
        roles = [item['data']['sort_title'] for item in roles_list if isinstance(item, dict) and 'data' in item]
        return ', '.join(roles) if roles else "Unknown"
    except Exception:
        return "Unknown"
    
# Función auxiliar para extraer el Win Rate
def extract_latest_win_rate(data_str):
    if not isinstance(data_str, str) or pd.isna(data_str):
        return np.nan
    try:
        data_dict = ast.literal_eval(data_str)
        # Aseguramos que tomamos el Win Rate más reciente
        if 'win_rate' in data_dict and data_dict['win_rate']:
            return data_dict['win_rate'][-1].get('win_rate')
        return np.nan
    except Exception:
        return np.nan
    
    # --- Esta Función Auxiliar para Ban Rate ---
        
def extract_latest_ban_rate(data_str):
    if not isinstance(data_str, str) or pd.isna(data_str):
        return np.nan
    try:
        data_dict = ast.literal_eval(data_str)
        if 'win_rate' in data_dict and data_dict['win_rate']:
            return data_dict['win_rate'][-1].get('ban_rate')
        return np.nan
    except Exception:
        return np.nan




# --- 1. Funciones Auxiliares de limpieza (Reutilizamos la lógica de EDA) ---

@st.cache_data # Este decorador cachea la función. Solo se ejecuta una vez, ¡Haciendo la app más rápida!
def load_data(file_path):
    """ Carga y aplica limpieza básica al dataset historico. """
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"❌ Error: Archivo histórico '{file_path}' no encontrado.")
        st.info("Asegúrate de ejecutar 'eda_mobilelegends.py' al menos una vez.")
        return  pd.DataFrame()  # Retorna un DataFrame vacío en caso de error


    # Aplicar extracción
    df['win_rate'] = df['data'].apply(extract_latest_win_rate)
    df['ban_rate'] = df['data'].apply(extract_latest_ban_rate)

    # Renombrar columnas clave y crear la columna de rol
    df.rename(columns={'hero.data.name': 'hero_name', 
                       'hero.data.sortid': 'raw_roles'}, inplace=True)
    
    df['role'] = df['raw_roles'].apply(extract_roles) # Crea la columna 'role'

    # Aplicar conversiones
    df['win_rate_pct'] = df['win_rate'] * 100.0
    df['ban_rate_pct'] = df['ban_rate'] * 100.0
    df['extraction_date'] = pd.to_datetime(df['extraction_date'])

    # Seleccionamos las columnas útiles
    df_clean = df[['hero_name', 'win_rate_pct', 'ban_rate_pct','extraction_date', 'role']].copy()
    df_clean.dropna(subset=['win_rate_pct', 'ban_rate_pct'], inplace=True)

    return df_clean


# --- 2. LAYOUT DE DASHBOARD ---

def run_dashboard():
    # Título de la página que aparece en la pestaña del navegador
    st.set_page_config(
        page_title="MLBB Meta Dashboard",
        layout="wide" # Usa todo en ancho disponible
    )

    # 2.1 Cargar datos
    df = load_data('mobile_legends_data_historical.csv')
    if df.empty:
        return # Si no se cargaron datos, no continuar
    
    # --- Contenido Principal ---
    
    st.title("🛡️ MLBB: Análisis de Tendencias del Meta")
    
    # Filtro de fecha interactivo
    latest_date = df['extraction_date'].max().date()
    st.info(f"Mostrando datos hasta la última fecha de extracción: **{latest_date}**")

    # Mostrar la data cruda (solo para depuración o referencia)
    if st.checkbox("Mostrar datos crudos"):
        st.subheader("Datos Históricos")
        # Mostramos solo la data más reciente
        df_latest = df[df['extraction_date'].dt.date == latest_date].copy()
        st.dataframe(df_latest)
    
     # --- Zona de gráficos: Scatter Plot (Win Rate vs Ban Rate) ---

    st.header("Gráfico 1: Dominancia del Meta (Win Rate vs Ban Rate)")

    # Nos enfocamos en la fecha más reciente
    df_current = df[df['extraction_date'].dt.date == latest_date].copy()

    # Aseguramos de que las columnas necesarias existen (deberían existir después de las correcciones)
    if 'ban_rate_pct' in df_current.columns and 'win_rate_pct' in df_current.columns:

        fig = px.scatter(
            df_current, 
            x='ban_rate_pct', 
            y='win_rate_pct', 
            color='win_rate_pct', 
            size='ban_rate_pct',
            hover_name='hero_name', # Muestra el nombre del héroe al pasar el mouse
            color_continuous_scale=px.colors.sequential.Sunset,
            title=f'Héroes Meta: Tasa de Victoria vs. Tasa de Ban (Datos al {latest_date})'
        )            

        fig.update_layout(
            xaxis_title='Tasa de Ban (%)',
            yaxis_title='Tasa de Victoria (%)',
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se pudo generar el gráfico: Faltan columnas clave. Revise su archivo CSV.")

    # --- 3. EJECUCIÓN DEL DASHBOARD ---
    if __name__ == "__main__":
        run_dashboard()