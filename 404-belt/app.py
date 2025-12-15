import RPi.GPIO as GPIO # Raspberry Pi GPIO 라이브러리 임포트
import paho.mqtt.client as mqtt # MQTT 라이브러리 임포트
import time # 시간 지연을 위한 time 모듈 임포트
import json # JSON 데이터 처리를 위한 json 모듈 임포트
import signal # 시그널 처리를 위한 signal 모듈 임포트
import sys # 시스템 종료를 위한 sys 모듈 임포트

RELAY = 23
HIGH_LEVEL_TRIGGER = False

MQTT_BROKER = "192.168.0.25"
MQTT_PORT = 1883
MQTT_TOPIC = "belt/control"

current_state = {
  'state': 0,
}

# GPIO 초기화 함수
def setup_gpio():
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(RELAY, GPIO.OUT)
  
  if HIGH_LEVEL_TRIGGER:
    GPIO.output(RELAY, GPIO.LOW)
  else:
    GPIO.output(RELAY, GPIO.HIGH)

# MQTT 연결 해제 시 호출되는 콜백 함수
def on_disconnect(client, userdata, rc):
  print("MQTT 연결이 해제되었습니다. 코드:", rc)
  
# MQTT 연결 시도 시 콜백 함수
def on_connect(client, userdata, flags, rc):
  if rc == 0:
    print("MQTT 브로커에 연결되었습니다.")
    client.subscribe(MQTT_TOPIC)
    print("토픽 구독 완료:", MQTT_TOPIC)
    print("시스템 준비 완료")
  else:
    print("MQTT 브로커 연결 실패, 코드:", rc)
    
# MQTT 메시지 수신 시 호출되는 콜백 함수
def on_message(client, userdata, msg):
  global current_state
  
  try:
    message = json.loads(msg.payload.decode())
    print("수신된 메시지:", message)
    
    if 'state' in message:
      current_state['state'] = message['state']
      
      if current_state['state'] == 1:
        if HIGH_LEVEL_TRIGGER:
          GPIO.output(RELAY, GPIO.HIGH)
        else:
          GPIO.output(RELAY, GPIO.LOW)
        print("벨트 작동 시작")
        
      elif current_state['state'] == 0:
        if HIGH_LEVEL_TRIGGER:
          GPIO.output(RELAY, GPIO.LOW)
        else:
          GPIO.output(RELAY, GPIO.HIGH)
        print("벨트 작동 중지")
        
  except Exception as e:
    print("메시지 처리 중 오류:", e)

def cleanup():
  GPIO.output(RELAY, GPIO.HIGH)
  GPIO.cleanup()
  
  mqtt_client.disconnect()
  
  print("프로그램 종료")
  sys.exit(0)

# 시그널 핸들러 등록
def signal_handler(sig, frame):
  cleanup()

def main():
  global mqtt_client
  
  # 시그널 핸들러 설정
  signal.signal(signal.SIGINT, signal_handler)
  
  # GPIO 초기화
  setup_gpio()
  
  # MQTT 클라이언트 설정
  mqtt_client = mqtt.Client()
  mqtt_client.on_connect = on_connect
  mqtt_client.on_disconnect = on_disconnect
  mqtt_client.on_message = on_message
  
  # MQTT 브로커 연결
  mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
  
  # MQTT 메시지 루프 시작
  mqtt_client.loop_start()
  
  try:
    while True:
      time.sleep(1)
      
  except KeyboardInterrupt:
    cleanup()

if __name__ == "__main__":
  main()