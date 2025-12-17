import RPi.GPIO as GPIO
import time
import json
import paho.mqtt.client as mqtt

TRIG = 5
ECHO = 6

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

# 10cm 이내에 물체가 들어오면 요청 보내는 함수
def send_request(mqtt_client, last_send_time):
  distance = get_distance()
  current_time = time.time()
  
  if distance < 11:
    # 마지막 전송으로부터 15초가 지났는지 확인
    if current_time - last_send_time >= 2:
      message = True
      mqtt_client.publish(MQTT_TOPIC, json.dumps(message))
      print("검사 요청 메시지 발행:", message)
      return current_time
  
  return last_send_time

def main():
  last_send_time = 0  # 마지막 전송 시간 초기화
  
  try:
    MQTT_client = mqtt.Client()
    MQTT_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    while True:
      last_send_time = send_request(MQTT_client, last_send_time)
      time.sleep(0.1)  # 센서 확인 주기

  except KeyboardInterrupt:
    print(f"프로그램 종료")
  finally:
    GPIO.cleanup()
    MQTT_client.disconnect()


if __name__ == "__main__":
  main()