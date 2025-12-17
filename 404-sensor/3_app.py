import paho.mqtt.client as mqtt
import json
import signal
import sys
import time

MQTT_BROKER = "192.168.0.25"
MQTT_PORT = 1883
MQTT_TOPIC_SEONSOR = "sensor/result"

current_state = {
  "device": "LED",
  "result": "DEFECT"
}

def on_disconnect(client, userdata, rc):
  print("MQTT 연결이 해제되었습니다. 코드:", rc)

# MQTT 연결 시도 시 콜백 함수
def on_connect(client, userdata, flags, rc):
  if rc == 0:
    print("브로커 연결 성공")

  else:
    print("브로커 연결 실패, 코드:", rc)

def on_message(client, userdata, msg):
  global current_state
  
  try:
    message = json.loads(msg.payload.decode())
    print("수신된 메시지:", message)
    
    if 'result' in message:
      current_state['result'] = message['result']
      print(f"LED 검사 결과: {current_state['result']}")
      
  except Exception as e:
    print("메시지 처리 중 오류 발생:", e)

def main():
  # MQTT 클라이언트 설정
  mqtt_client = mqtt.Client()
  mqtt_client.on_connect = on_connect
  mqtt_client.on_message = on_message
  mqtt_client.on_disconnect = on_disconnect
  
  # MQTT 브로커 연결
  mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
  
  # MQTT 루프 시작
  mqtt_client.loop_start()
  
  try:
    while True:
      # 메시지 발행 예제
      current_state
      mqtt_client.publish(MQTT_TOPIC_SEONSOR, json.dumps(current_state))
      print("메시지 발행:", current_state)
      time.sleep(5)
      
  except KeyboardInterrupt:
    print("\n프로그램 종료")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

if __name__ == "__main__":
  main()