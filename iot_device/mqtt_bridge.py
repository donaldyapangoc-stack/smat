import os
import paho.mqtt.client as mqtt
import requests
import json
import time
import sys

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "fisi/smat/estaciones/#"
API_URL = os.environ.get("API_URL", "http://localhost:8000/lecturas/")
JWT_TOKEN = os.environ.get("JWT_TOKEN", "tu_token_jwt_aqui")

DEADBAND_PORCENTAJE = 5.0
INTERVALO_MINIMO = 60

cache = {}


def debe_enviar(estacion_id, nuevo_valor):
    if estacion_id not in cache:
        return True

    ultimo = cache[estacion_id]
    tiempo_transcurrido = time.time() - ultimo["timestamp"]

    if tiempo_transcurrido >= INTERVALO_MINIMO:
        return True

    if ultimo["valor"] != 0:
        cambio = abs((nuevo_valor - ultimo["valor"]) / ultimo["valor"]) * 100
        if cambio > DEADBAND_PORCENTAJE:
            return True

    print(f"  [FILTRADO] Estación {estacion_id}: valor {nuevo_valor} descartado (cambio insignificante)")
    return False


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado exitosamente al Broker MQTT")
        client.subscribe(MQTT_TOPIC)
        print(f"Escuchando transmisiones en el tópico: {MQTT_TOPIC}")
    else:
        print(f"Error de conexión al Broker. Código de retorno: {rc}")
        sys.exit(1)


def on_message(client, userdata, msg):
    try:
        payload_raw = msg.payload.decode("utf-8")
        data_json = json.loads(payload_raw)

        topic_parts = msg.topic.split('/')
        estacion_id = int(topic_parts[3])

        print(f"Telemetría recibida de Estación [{estacion_id}]: {data_json}")

        nuevo_valor = float(data_json["valor"])

        if not debe_enviar(estacion_id, nuevo_valor):
            return

        api_payload = {
            "valor": nuevo_valor,
            "estacion_id": estacion_id
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {JWT_TOKEN}"
        }

        response = requests.post(API_URL, json=api_payload, headers=headers)

        if response.status_code in (200, 201):
            cache[estacion_id] = {"valor": nuevo_valor, "timestamp": time.time()}
            print(f"  [DB Sincronizada] Lectura de {nuevo_valor} cm guardada en SQLite.")
        else:
            print(f"  [Fallo de Ingesta] API rechazó el dato. Código: {response.status_code} - {response.text}")

    except KeyError as e:
        print(f"Error de esquema: Falta la llave {e} en el payload MQTT.")
    except ValueError:
        print("Error de casteo: El valor o el ID de la estación no son numéricos.")
    except Exception as e:
        print(f"Error crítico en el Bridge: {e}")


bridge_client = mqtt.Client()
bridge_client.on_connect = on_connect
bridge_client.on_message = on_message

try:
    print("Inicializando el Bridge de Acoplamiento SMAT...")
    bridge_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    bridge_client.loop_forever()
except KeyboardInterrupt:
    print("\nBridge detenido por el administrador.")
