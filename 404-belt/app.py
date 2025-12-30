import RPi.GPIO as GPIO
import time
import json
import paho.mqtt.client as mqtt
import signal
import sys

RELAY = 23

MQTT_BROKER = "192.168.0.25"
MQTT_PORT = 1883
MQTT_TOPIC = "power/control"

mqtt_client = None
power_state = 'OFF'

def setup_gpio():
    """GPIO 초기화 - 출력 모드로 설정하고 OFF 상태"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RELAY, GPIO.IN)
    print("GPIO 초기화 완료 - 릴레이 OFF")

def control_relay(state):
    """릴레이 제어"""
    global power_state
    
    if state == 'ON':
        GPIO.setup(RELAY, GPIO.OUT)
        power_state = 'ON'
        print("ON - 벨트 가동")
    elif state == 'OFF':
        GPIO.setup(RELAY, GPIO.IN)
        power_state = 'OFF'
        print("OFF - 벨트 중지")

def on_disconnect(client, userdata, rc):
    print("MQTT 연결이 해제되었습니다. 코드:", rc)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("=" * 50)
        print("브로커 연결 성공")
        client.subscribe(MQTT_TOPIC)
        print(f"토픽 구독: {MQTT_TOPIC}")
        print("=" * 50)
    else:
        print("브로커 연결 실패, 코드:", rc)

def on_message(client, userdata, msg):
    """MQTT 메시지 수신"""
    try:
        message = json.loads(msg.payload.decode())
        print(f"\n[수신] 토픽: {msg.topic}")
        print(f"[수신] 메시지: {message}")
        
        if 'command' in message:
            command = message['command']
            
            if command == "POWER_ON":
                control_relay('ON')
            elif command == "POWER_OFF":
                control_relay('OFF')
            else:
                print(f"⚠ 알 수 없는 명령: {command}")
        else:
            print("⚠ 메시지에 'command' 키가 없습니다.")
                
    except json.JSONDecodeError:
        print("⚠ JSON 파싱 실패")
    except Exception as e:
        print(f"⚠ 메시지 처리 중 오류: {e}")

def cleanup():
    """종료 시 정리"""
    print("\n프로그램 종료 중...")
    control_relay('OFF')
    
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    
    GPIO.cleanup()
    print("정리 완료")

def main():
    global mqtt_client

    print("\n벨트 제어 시스템 시작\n")
    
    # GPIO 초기화
    setup_gpio()
    
    # MQTT 클라이언트 설정
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect

    # MQTT 연결
    print(f"MQTT 브로커 연결 시도: {MQTT_BROKER}:{MQTT_PORT}")
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # MQTT 루프 시작
    mqtt_client.loop_start()

    try:
        print("\n대기 중... (종료: Ctrl+C)\n")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()