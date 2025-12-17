import RPi.GPIO as GPIO
import time
import json
import paho.mqtt.client as mqtt

TRIG = 17
ECHO = 27

MQTT_BROKER = "192.168.0.25"
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/control"

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT) # TRIG는 출력신호
GPIO.setup(ECHO, GPIO.IN) # ECHO는 입력신호

GPIO.output(TRIG, GPIO.LOW)
time.sleep(0.5)

def get_distance():
  GPIO.output(TRIG, GPIO.HIGH)
  time.sleep(0.00001) # 10마이크로초 신호 발생
  GPIO.output(TRIG, GPIO.LOW)
  
  while GPIO.input(ECHO) == GPIO.LOW:
    pulse_start = time.time() # 초음파를 보낸 시각 기록
    
  while GPIO.input(ECHO) == GPIO.HIGH:
    pulse_end = time.time() # 초음파가 돌아온 시각 기록
    
  pulse_duration = pulse_end - pulse_start
  
  # 음속이 343m/s
  distance = pulse_duration * 34300 / 2 # cm 단위 거리 
  
  return distance

def main():
  try:
    while True:
      distance = get_distance()
      
      print(f"2번 센서 거리 : {distance} cm")
      
      time.sleep(1)
  except KeyboardInterrupt:
    print(f"프로그램 종료")
  finally:
    GPIO.cleanup()

if __name__ == "__main__":
  main()