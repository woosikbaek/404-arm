import RPi.GPIO as GPIO
import time

RELAY = 23
HIGH_LEVEL_TRIGGER = False

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "belt/control"

def main():
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(RELAY, GPIO.OUT)
  
  if HIGH_LEVEL_TRIGGER:
    GPIO.output(RELAY, GPIO.HIGH)
  else:
    GPIO.output(RELAY, GPIO.LOW)
    
  try:
    while True:
      time.sleep(1)
      
  except KeyboardInterrupt:
    GPIO.output(RELAY, GPIO.HIGH)
    GPIO.cleanup()
    
if __name__ == "__main__":
  main()