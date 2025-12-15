import json
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt

X = 5
Y = 6

MQTT_BROKER = "shras"
MQTT_PORT = 1883
MQTT_TOPIC = "arm/control"
