import requests
import pandas as pd
import time
import os
import sys
import json
from datetime import datetime
import csv   

# ---------------------------------------------------
# Añadir el directorio padre al path para importar config
# ---------------------------------------------------
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Añadir el directorio padre al path de Python para que pueda encontrar la carpeta 'config/'
sys.path.append(parent_dir)

from config.config import API_BASE_URL # Debe existir este archivo con la URL base de la API

# --- FUNCIONES AUXILIARES ---

def fetch_data(endpoint):
    """
    Función robusta para hacer la llamada a la API y retornar el objeto JSON crudo.
    """
    url_completa = f"{API_BASE_URL}{endpoint}"
    print(f"-> Extrayendo datos de: /{endpoint}")
    
    try:
        response = requests.get(url_completa)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al conectar con la API en /{endpoint}: {e}")
        return None

def extract_list_from_api_response(raw_json, _endpoint_name):
    """ 
    Extrae la lista de registros de un JSON de API, probando el patrón conocido.
    """
    if not raw_json:
        return []
    
    # Patrón: {'data': {'records': [...]}}
    if isinstance(raw_json, dict) and 'data' in raw_json and 'records' in raw_json['data'] and isinstance(raw_json['data']['records'], list):
        return raw_json['data']['records']
        
    return []

def fetch_all_hero_rates(hero_ids):
    """
    Itera sobre una lista de IDs y hace una petición individual a hero-rate/ID/.
    """
    all_rates = []
    total_heroes = len(hero_ids)
    
    print(f"\n--- FASE 2: EXTRACCIÓN INDIVIDUAL DE RATINGS ({total_heroes} héroes) ---")
    
    for i, hero_id in enumerate(hero_ids):
        # Endpoint para el rating de un héroe, usando el ID como parámetro de ruta.
        endpoint = f"hero-rate/{hero_id}/" 
        
        rate_raw = fetch_data(endpoint) # Obtiene el JSON crudo
        
        # Desempaquetado para hero-rate: 'data' -> 'records'
        if rate_raw and 'data' in rate_raw and 'records' in rate_raw['data']:
            rate_data_records = rate_raw['data']['records']
            
            if rate_data_records:
                # Seleccionamos la data más reciente de la serie de tiempo para el EDA.
                latest_rate = rate_data_records[-1] 
                
                # Añadimos el ID para poder hacer el merge (¡Usamos el ID correcto!)
                latest_rate['hero_id'] = hero_id 
                all_rates.append(latest_rate)
            
        time.sleep(0.1) 
        print(f"Procesando ratings... {i + 1}/{total_heroes}", end='\r')
        
    print(f"\n✔️ Extracción de {len(all_rates)} ratings individuales completada.")
    return pd.DataFrame(all_rates)

# --- PIPELINE PRINCIPAL ---

def data_extraction_pipeline():
    """ 
    Orquesta la extracción, combinación y guardado de datos.
    """
    
    print("--- FASE 1: EXTRACCIÓN MASIVA DE DATOS ---")
    
    # 1. Extracción de POSICIONES (Base para Nombres y Roles)
    df_positions_raw = fetch_data("hero-position/?size=200") 
    positions_list = extract_list_from_api_response(df_positions_raw, "hero-position/")
    df_positions = pd.DataFrame(positions_list)
    
    if df_positions.empty:
        print("\n❌ Extracción de Posiciones fallida. No se puede continuar.")
        return None
    
    
    # Convertimos la columna 'data' (que contiene un diccionario) en nuevas columnas
    # Esto expone 'hero_id', 'role', 'lane', etc., como columnas principales.
    try:
        if 'data' in df_positions.columns:
            df_positions = pd.json_normalize(df_positions['data'])
    except Exception as e:
        print(f"❌ Error al desanidar el DataFrame de Posiciones: {e}")
        return None
    
    
    print(f"\n✔️ Extracción de posiciones exitosa. Héroes encontrados: {len(df_positions)}.")
    
    # 2. **GENERACIÓN DE ID:** Creamos la lista de IDs secuenciales
    hero_ids = list(range(1, 131)) 
    df_rates = fetch_all_hero_rates(hero_ids)
    
    if df_rates.empty:
        print("\n❌ Extracción de ratings fallida. La API no devolvió datos para los IDs secuenciales.")
        return None
    
    # 3. Preparación y Combinación (Merge)
    print("\n--- FASE 3: COMBINACIÓN Y GUARDADO ---")
    
    try:
        # 3a. Limpiamos df_positions
        # Renombramos el ID largo ('id') que ahora es visible, y usamos el 'hero_id' para el merge.
        if 'id' in df_positions.columns:
            df_positions.rename(columns={'id': 'pos_id'}, inplace=True)
            df_positions.drop(columns=['pos_id'], inplace=True, errors='ignore') 
        
        # 3b. Limpiamos df_rates
        # Eliminamos el 'id' de la tabla de rates, si existe, para evitar ambigüedad.
        if 'id' in df_rates.columns:
            df_rates.drop(columns=['id'], inplace=True, errors='ignore') 
        
        # 3c. Ejecutamos el Merge (Ahora 'hero_id' debería existir en ambos DataFrames)
        df_final = pd.merge(df_positions, df_rates, on='hero_id', how='inner')
        
        # Eliminamos duplicados si hay héroes listados más de una vez
        df_final.drop_duplicates(subset=['hero_id'], inplace=True) 

        if 'data' in df_final.columns:
            df_final['data'] = df_final['data'].apply(lambda x: json.dumps(x, ensure_ascii=False))

        print(f"✔️ Combinación (Merge) exitosa. Filas finales (Héroes únicos): {len(df_final)}")
        
        # 4. Guardado de los datos limpios en modo histórico
        
        # 4a. Añadir columna de fecha de extracción para el seguimiento
        df_final['extraction_date'] = datetime.now().strftime('%Y-%m-%d')

        # 4b. Lógica de guardado en modo APPEND al archivo histórico
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        historica_file_path = os.path.join(data_dir, "mobile_legends_data_historical.csv")

        # Aseguramos que la carpeta de datos exista
        os.makedirs(data_dir, exist_ok=True)

        # Guardar CSV histórico con comillas para evitar problemas
        df_final.to_csv(historica_file_path,
                        mode='a' if os.path.exists(historica_file_path) else 'w',
                        index=False,
                        header=not os.path.exists(historica_file_path),
                        quoting=csv.QUOTE_ALL)
        print(f"💾 Datos guardados en archivo histórico: {historica_file_path}")
        
        # CSV limpio para EDA rápido / Streamlit
        clean_csv_path = os.path.join(data_dir, "mobile_legends_data_clean.csv")
        df_final.to_csv(clean_csv_path, index=False, quoting=csv.QUOTE_ALL)
        print(f"💾 CSV limpio guardado para EDA/Streamlit: {clean_csv_path}")

        return df_final
        
    except Exception as e:
        print(f"❌ Error durante la Combinación (Merge). Error: {e}")
        return None


if __name__ == "__main__":
    final_dataframe = data_extraction_pipeline()
    
    if final_dataframe is not None:
        print("\n✅ ¡LA EXTRACCIÓN HA FINALIZADO CON ÉXITO!")
        print("El archivo 'mobile_legends_data_historical.csv' es tu fuente de datos lista para el EDA.")