import streamlit as st
import pandas as pd
import plotly.express as px
import ast 
import numpy as np
import requests  
from datetime import datetime
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pandas import DataFrame 

# ----------------------------------------------------------------------
# -------------------- CONFIGURACIÓN DE RUTAS --------------------------
# ----------------------------------------------------------------------

# Se asume la estructura del proyecto: src/ (este archivo), data/, reports/
REPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reports'))
CSV_FILE_PATH = os.path.join(os.path.dirname(__file__),"data", "mobile_legends_data_historical.csv")
API_URL = "http://127.0.0.1:8000/data"  # Por si quieres usar la API en el futuro
CSV_URL = "https://raw.githubusercontent.com/STpipa/MLBB-EDA-Project/main/data/mobile_legends_data_historical.csv"

os.makedirs(REPORT_DIR, exist_ok=True)

# ----------------------------------------------------------------------
# --- 1. FUNCIONES AUXILIARES GLOBALES Y LIMPIEZA (Corregidas) ---
# ----------------------------------------------------------------------

# ----------------------------------------------------
# --- 1. FUNCIONES AUXILIARES GLOBALES ---
# ----------------------------------------------------

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
            if data_dict['win_rate']:
                return data_dict['win_rate'][-1].get('win_rate')
        return np.nan
    except Exception:
        return np.nan
        
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

# ----------------------------------------------------
# --- 2. FUNCIÓN DE CARGA Y CACHÉ ---
# ----------------------------------------------------

@st.cache_data 
def load_data():
    """Carga datos: primero intenta API, luego CSV local, luego CSV remoto"""
    df = pd.DataFrame()
    # --- Intentar API ---
    try:
        response = requests.get(API_URL, timeout=3)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        st.info("Datos cargados desde API local.")
    except Exception:
        st.warning("No se pudieron cargar los datos desde la API. Intentando CSV local...")
        # --- Intentar CSV local ---
        try:
            df = pd.read_csv(CSV_FILE_PATH, quotechar='"', engine='python')
            st.info("Datos cargados desde CSV histórico local.")
        except Exception:
            st.warning("CSV local no disponible. Intentando CSV remoto en GitHub...")
            # --- Intentar CSV remoto ---
            try:
                df = pd.read_csv(CSV_URL, quotechar='"', engine='python')
                st.info("Datos cargados desde CSV remoto en GitHub.")
            except Exception as e:
                st.error(f"No se pudieron cargar los datos: {e}")
                return pd.DataFrame()
    
        # 1. Aplicar funciones de parseo a la columna CRUDA 'data'
        df['win_rate'] = df['data'].apply(extract_latest_win_rate)
        df['ban_rate'] = df['data'].apply(extract_latest_ban_rate)
        # 2. Renombrar columnas clave y crear la columna de rol
        df.rename(columns={'hero.data.name': 'hero_name', 
                    'hero.data.sortid': 'raw_roles'}, inplace=True)
                    
        df['role'] = df['raw_roles'].apply(extract_roles) # Crea la columna 'role'
        df['primary_role'] = df['role'].apply(lambda x: x.split(',')[0].strip())
    
        # 3. Conversiones y limpieza final
        df['win_rate_pct'] = df['win_rate'] * 100
        df['ban_rate_pct'] = df['ban_rate'] * 100
        df['extraction_date'] = pd.to_datetime(df['extraction_date'])

        # Seleccionamos las columnas útiles y limpiamos NaN
        df_clean = df[['hero_name', 'win_rate_pct', 'ban_rate_pct', 
                'extraction_date', 'role']].copy()
        df_clean.dropna(subset=['win_rate_pct', 'ban_rate_pct'], inplace=True)
        return df
    except Exception as e:
        st.error(f"No se pudieron cargar los datos: {e}")
        return pd.DataFrame()

# ----------------------------------------------------
# --- 3. LAYOUT DEL DASHBOARD ---
# ----------------------------------------------------

def run_dashboard():
    st.set_page_config(page_title="MLBB Meta Dashboard", layout="wide") 
    st.title("🛡️ MLBB: Análisis de Tendencias del Meta")


    # 3.1 Cargar datos
    
    df = load_data()
    if df.empty:
        st.stop()  # Termina si no hay datos
        
        
    # --- Contenido Principal ---
    
    
    
    latest_date = df['extraction_date'].max().date()
    st.info(f"Mostrando datos hasta la última fecha de extracción: **{latest_date}**")

    tab1, tab2, tab3 = st.tabs(["📊 Análisis del Meta", "📈 Tendencia Semanal", "🔍 Detalle por Héroe"])

    with tab1:
        st.header("Meta Actual: Dominancia y Balance")

        # 1. Scatter Plot
        st.header("Gráfico 1: Dominancia del Meta (Win Rate vs Ban Rate)")
        df_current = df[df['extraction_date'].dt.date == latest_date].copy()

        # 2. Comparativa de Roles (Win Rate Promedio)
        df['primary_role'] = df['role'].apply(lambda x: x.split(',')[0].strip())
        df_role_winrate = df.groupby('primary_role')['win_rate_pct'].mean().reset_index()

        st.subheader("Win Rate Promedio por Rol")
        fig_role = px.bar(
            df_role_winrate.sort_values(by='win_rate_pct', ascending=False),
            x='primary_role',
            y='win_rate_pct',
            color='win_rate_pct',
            title='Roles más Efectivos en el Meta Actual',
            text_auto='.2s'
        )   
        st.plotly_chart(fig_role, use_container_width=True)


    with tab2:
        st.header("Resumen del Meta y Tendencias Clave")

        # Aseguramos la ruta del archivo de reporte más reciente
        # Esto asume que el reporte se corre el mismo día de la última extracción
        latest_report_date = df['extraction_date'].max().strftime('%Y%m%d') 
        report_file_path = f"reports/reporte_tendencia_{latest_report_date}.txt"
    
        try:
            with open(report_file_path, 'r', encoding='utf-8') as f:
                report_content = f.read()

            st.text_area("Reporte de Tendencia Generado:", value=report_content, height=500)

        except FileNotFoundError:
            st.warning(f"⚠️ Reporte de tendencia ({report_file_path}) no encontrado. Asegúrate de haber ejecutado 'python reporting.py'.")

            # Asumiendo que has generado un reporte para la fecha más reciente (df.max())
            latest_report_date = df['extraction_date'].max().strftime('%Y%m%d')
            report_file_path = f"reports/reporte_tendencia_{latest_report_date}.txt"
        
            with open(report_file_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
        
            st.code(report_content) # Muestra el texto formateado
        except FileNotFoundError:
            st.warning("El reporte de tendencia más reciente no ha sido generado. Ejecuta 'reporting.py'.")

    with tab3:
        st.header("Detalle y Perfil del Héroe")
    
        hero_list = sorted(df['hero_name'].unique())
        selected_hero = st.selectbox("Selecciona un Héroe", hero_list)
        
        df_hero = df[df['hero_name'] == selected_hero].copy()

        if not df_hero.empty:

            # 1. Preparación de Métricas
            # Ordenamos por fecha para asegurar que la última es la más reciente
            df_hero.sort_values(by='extraction_date', inplace=True)
            latest_metrics = df_hero.iloc[-1]

            # 2. Cálculo del Delta (Cambio vs. fecha anterior)
            # Filtramos las dos últimas fechas disponibles para el héroe
            df_hero_history = df_hero.nlargest(2, 'extraction_date')
            change = 0.0 

            if len(df_hero_history) == 2:
                win_rate_latest = df_hero_history.iloc[-1]['win_rate_pct']
                win_rate_previous = df_hero_history.iloc[0]['win_rate_pct']
                change = win_rate_latest - win_rate_previous

            # 3. Mostrar Metricas Clave (usando st.metric)
            col_metrics_1, col_metrics_2, col_metrics_3 = st.columns(3)

            with col_metrics_1:
                st.metric("Win Rate Actual", f"{latest_metrics['win_rate_pct']:.2f}%")

            with col_metrics_2:
                st.metric("Ban Rate Actual", f"{latest_metrics['ban_rate_pct']:.2f}%")

            with col_metrics_3:
                st.metric("Rol Principal", latest_metrics['role'].split(',')[0])

            # 4. Gráfico de Línea de Tendencia (Win Rate histórico del héroe)
            st.subheader(f"Evolución del Win Rate de {selected_hero}")

            fig_trend = px.line(
                df_hero, 
                x='extraction_date', 
                y='win_rate_pct', 
                title='Tendencia Histórica de {selected_hero}',
                markers=True # Mostrar puntos para cada extracción
            )

            # Añadir una línea horizontal para el Win Rate promedio general para contexto
            avg_win_rate = df['win_rate_pct'].mean()
            fig_trend.add_hline(y=avg_win_rate, line_dash="dash", line_color="red",
                                annotation_text=f"Promedio Meta ({avg_win_rate:.2f}%)") 

            st.plotly_chart(fig_trend, use_container_width=True)

        else:
            st.warning(f"No hay datos disponibles para el héroe seleccionado: {selected_hero}")

        

    # Mostrar la data cruda (Botón de chequeo)
    if st.checkbox("Mostrar datos crudos para chequeo (última fecha)"):
        st.subheader("Datos de la Última Extracción")
        df_latest = df[df['extraction_date'].dt.date == latest_date].copy()
        st.dataframe(df_latest)


    # --- Zona de gráficos: Scatter Plot (Win Rate vs Ban Rate) ---

    st.header("Gráfico 1: Dominancia del Meta (Win Rate vs Ban Rate)")
    df_current = df[df['extraction_date'].dt.date == latest_date].copy()
    
    if 'ban_rate_pct' in df_current.columns and 'win_rate_pct' in df_current.columns:

        fig = px.scatter(
            df_current, 
            x='ban_rate_pct', 
            y='win_rate_pct', 
            color='win_rate_pct', 
            size='ban_rate_pct',
            hover_name='hero_name', 
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
        st.warning("No se pudo generar el gráfico: Faltan las columnas 'ban_rate_pct' o 'win_rate_pct'.")


# ----------------------------------------------------
# --- 4. EJECUCIÓN DEL SCRIPT ---
# ----------------------------------------------------
if __name__ == "__main__":
    run_dashboard()