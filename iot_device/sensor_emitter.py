import requests
import time
import random


# CONFIGURACIÓN DEL DISPOSITIVO IoT EMULADO
# Simula un microcontrolador ESP32 / Raspberry Pi
API_URL    = "http://localhost:8000/lecturas/"
ESTACION_ID = 1        # ID de la estación registrada en la DB
TOKEN      = "TU_TOKEN_JWT_AQUI"  # Del /token

#Umbrales
UMBRAL_ALERTA  = 70.0   # Nivel de inundación, en cm
INTERVALO_NORMAL     = 10   # segundos en modo normal
INTERVALO_EMERGENCIA =  2   # segundos en modo emergencia


def leer_sensor_emulado() -> float:
    """
    Simula la lectura de un sensor de nivel de río (0 – 100 cm).
    """
    return round(random.uniform(10.5, 85.0), 2)


def enviar_telemetria():
    print(f"--- Iniciando Emisor IoT para Estación {ESTACION_ID} ---")

    while True:
        valor = leer_sensor_emulado()

        
        # PARTE DEL RETO
        
        if valor > UMBRAL_ALERTA:
            print(f"[ALERTA] Umbral de inundación superado → {valor} cm")
            intervalo = INTERVALO_EMERGENCIA     # Modo Emergencia: cada 2 s
        else:
            intervalo = INTERVALO_NORMAL         # Modo Normal: cada 10 s

        
        # Construcción del payload y cabeceras JWT
        
        payload = {
            "valor":       valor,
            "estacion_id": ESTACION_ID
        }
        headers = {
            "Authorization": f"Bearer {TOKEN}"
        }

       
        # Envío HTTP a la API SMAT
        
        try:
            response = requests.post(API_URL, json=payload, headers=headers,
                                     timeout=5)
            if response.status_code in (200, 201):
                modo = "🚨 EMERGENCIA" if valor > UMBRAL_ALERTA else "✅ NORMAL"
                print(f"[OK] Lectura enviada: {valor} cm  |  Modo: {modo}  |  Próximo envío: {intervalo}s")
            else:
                print(f"[ERROR] Código HTTP: {response.status_code} – {response.text}")
        except requests.exceptions.ConnectionError:
            print("[CRÍTICO] No hay conexión con el servidor. Reintentando...")
        except Exception as e:
            print(f"[CRÍTICO] Error inesperado: {e}")

        time.sleep(intervalo)


if __name__ == "__main__":
    enviar_telemetria()
