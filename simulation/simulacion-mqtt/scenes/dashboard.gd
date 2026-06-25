extends Node2D

@onready var mqtt = $MQTTClient
const BROKER = "wss://broker.hivemq.com:8884/mqtt"

func _ready():
	mqtt.broker_connected.connect(_on_connected)
	mqtt.received_message.connect(_on_msg)
	mqtt.connect_to_broker(BROKER)

func _on_connected():
	mqtt.subscribe("fisi/smat/estaciones/+/lecturas")

func _on_msg(topic, message):
	var data = JSON.parse_string(message)
	var id = topic.split('/')[3]
	actualizar_sensor(id, data["valor"])

func actualizar_sensor(id, valor):
	var nodo = get_node_or_null("Estacion_" + str(id))
	if nodo:
		nodo.actualizar_estado(valor)
