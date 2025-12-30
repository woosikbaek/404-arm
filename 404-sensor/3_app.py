import RPi.GPIO as GPIO
import time
import json
import paho.mqtt.client as mqtt

SENSOR = 3

MQTT_BROKER = "192.168.0.25"
MQTT_PORT = 1883
MQTT_TOPIC = "ult03"

GPIO.setmode(GPIO.BCM)
GPIO.setup(SENSOR, GPIO.OUT)

GPIO.output(SENSOR, GPIO.HIGH)
time.sleep(0.5)
print("3번 센서 실행 중...")