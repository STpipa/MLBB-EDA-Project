# Importamos la librería requests y la variable de configuración.

import requests
# Importamos la URL base desde el archivo de configuración. 
from config import API_BASE_URL

def obtener_datos_heroes():
    """
    Función para obtener los datos de los héroes desde la API.
    """
    # Endopoint de ejemplo para obtener los datos de los héroes.
    endpoint = "heroes"
    url = f"{"https://mlbb-stats.ridwaanhall.com/api/"}/{endpoint}"

    print(f"Intentando conectar a: {url}")


    try:
        # Realizamos una solicitud GET a la API para obtener los datos de los héroes.
        response = requests.get(url)
        response.raise_for_status()  # Verificamos si la solicitud fue exitosa.
        
        datos = response.json()
        print(f"Conexión exitosa. Número de héroes obtenidos: {len(datos)}")

    except requests.exceptions.HTTPError as errh:
        print(f"Error HTTP: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error de conexión: {errc}")
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud: {e}")

if __name__ == "__main__":
    obtener_datos_heroes()