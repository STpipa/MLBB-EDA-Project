import streamlit as st
import pandas as pd
import plotly.express as px
import ast 
import numpy as np


# --- 1. Funciones Auxiliares de limpieza (Reutilizamos la lógica de EDA) ---

@st.cache_data # Este decorador cachea la función. Solo se ejecuta una vez, ¡Haciendo la app más rápida!
def load_data(file_path):
    """ Carga y aplica limpieza básica al dataset historico. """
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        st.error("Error: Archivo histórico 'mobile_legends_data_historical.csv' no encontrado.")
        return  pd.DataFrame()  # Retorna un DataFrame vacío en caso de error
    
    

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
                latest_record = data_dict['win_rate'][-1]
                return latest_record.get('ban_rate')
            return np.nan
        except Exception:
            return np.nan



    # Aplicar extracción
    df['win_rate'] = df['data'].apply(extract_latest_win_rate)
    df['ban_rate'] = df['data'].apply(extract_latest_ban_rate)

    # Aplicar conversiones
    df['win_rate_pct'] = df['win_rate'] * 100.0
    df['ban_rate_pct'] = df['ban_rate'] * 100.0
    df.rename(columns={'hero.data.name': 'hero_name'}, inplace=True)
    df['extraction_date'] = pd.to_datetime(df['extraction_date'])

    # Seleccionamos las columnas útiles
    df_clean = df[['hero_name', 'win_rate_pct', 'ban_rate_pct','extraction_date', 'hero.data.sortid']].copy()
    df_clean.dropna(inplace=True)

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
    
    # 2.2 Barra lateral (Sidebar) para filtros y navegación
    st.sidebar.header("Opciones de Visualización")

    # 2.3 Contenido Principal

    st.title("🛡️ MLBB: Análisis de Tendencias del Meta")
    st.markdown("Dashboard interactivo para explorar el Win Rate de héroes a lo largo del tiempo.")

    # Filtro de fecha interactivo
    latest_date = df['extraction_date'].max().date()
    st.info(f"Mostrando datos hasta la última fecha de extracción: **{latest_date}**")

    # Mostrar la data cruda (solo para depuración o referencia)
    if st.checkbox("Mostrar datos crudos"):
        st.subheader("Datos historicos")
        st.write(df)

    # --- Zona de gráficos (Aquí pondremos el Plotly y Bar Charts)---

    st.header("Gráfico 1: Evolución del Win Rate (Placeholder)")
    st.text("Aqui se mostrará el primer gráfico interactivo.")

    # Ejemplo de gráfico con simple (un histograma de Win Rate)
    fig_hist = px.histogram(df[df['extraction_date']==latest_date],x='win_rate_pct',
                            title='Distribución del Win Rate de Héroes hoy')
    st.plotly_chart(fig_hist, use_container_width=True)

    st.header("Gráfico 1: Dominancia del Meta (Win Rate vs Ban Rate)")

    # Nos enfocamos en la fecha más reciente para el scatter plot
    latest_date = df['extraction_date'].max()
    df_current = df[df['extraction_date'] == latest_date]

    # Aseguramos de que las columnas necesarias existen
    if 'ban_rate_pct' in df_current.columns and 'win_rate_pct' in df_current.columns:

        fig = px.scatter(
            df_current, 
            x='ban_rate_pct', 
            y='win_rate_pct', 
            color='win_rate_pct', 
            size='ban_rate_pct',
            hover_name=['hero_name'], # Muestra el nombre del héroe al pasar el mouse
            color_continuous_scale=px.colors.sequential.Sunset,
            title=f'Héroes Meta: Tasa de Victoria vs. Tasa de Ban (Datos al {latest_date.date()})'
        )            

        fig.update_layout(
            xaxis_title='Tasa de Ban (%)',
            yaxis_title='Tasa de Victoria (%)',
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("No se pudo generar el gráfico de Scatter: Faltan las columnas 'ban_rate_pct' o 'win_rate_pct'.")

    # --- 3. EJECUCIÓN DEL DASHBOARD ---
    if __name__ == "__main__":
        run_dashboard()