from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

app = FastAPI(title="MLBB historical Data API")

# Permitir request desde Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta relativa al CSV (local o actualizable)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE_PATH = os.path.join(BASE_DIR, "data", "mobile_legends_data_historical.csv")

@app.get("/data")
def get_historical_data():
    """Devuelve los datos históricos de MLBB en JSON"""
    if not os.path.exists(DATA_FILE_PATH):
        return {"error": "Archivo CSV no encontrado"}
    
    df = pd.read_csv(DATA_FILE_PATH)
    # Convertir fechas a string para que JSON pueda serializar
    if "extraction_date" in df.columns:
        df["extraction_date"] = pd.to_datetime(df["extraction_date"]).dt.strftime('%Y-%m-%d')
    return df.to_dict(orient="records")