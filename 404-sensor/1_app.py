import RPi.GPIO as GPIO
import time
import json
import paho.mqtt.client as mqtt

# [설정] 핀 번호 및 MQTT 정보
TRIG = 5
ECHO = 6
MQTT_BROKER = "192.168.0.25"
MQTT_PORT = 1883
MQTT_TOPIC = "ult01"

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def get_distance():
    """초음파 거리 측정 (타임아웃 포함)"""
    GPIO.output(TRIG, GPIO.LOW)
    time.sleep(0.01)
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)
    
    # ECHO 신호 대기 (최대 0.05초)
    timeout = time.time() + 0.05
    pulse_start = time.time()
    while GPIO.input(ECHO) == GPIO.LOW:
        pulse_start = time.time()
        if pulse_start > timeout: return 999  # 측정 실패 시 먼 거리값 반환

    timeout = time.time() + 0.05
    pulse_end = time.time()
    while GPIO.input(ECHO) == GPIO.HIGH:
        pulse_end = time.time()
        if pulse_end > timeout: return 999

    distance = (pulse_end - pulse_start) * 34300 / 2
    return distance

def main():
    last_send_time = 0 
    
    try:
        client = mqtt.Client()
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start() # MQTT 연결 유지 루프 시작
        print(f"--- 센서 감시 시작 (핀: T{TRIG}, E{ECHO}) ---")

        while True:
            dist = get_distance()
            curr_time = time.time()

            # 1. 11cm 이내 감지 (1cm 마진 포함)
            if dist < 11:
                # 2. 마지막 전송으로부터 25초가 지났는지 확인
                if curr_time - last_send_time >= 25:
                    message = True
                    client.publish(MQTT_TOPIC, json.dumps(message))
                    
                    print(f"[{time.strftime('%H:%M:%S')}] 물체 감지({dist:.1f}cm)! 메시지 전송 완료.")
                    print(f"앞으로 25초간 재발신을 중단합니다.")
                    
                    last_send_time = curr_time # 기준 시간 업데이트

            # 센서 측정 주기 (0.5초 정도로 하면 반응이 빠릅니다)
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n사용자에 의해 종료됨")
    finally:
        client.loop_stop()
        client.disconnect()
        GPIO.cleanup()
        print("GPIO 정리 완료.")

if __name__ == "__main__":
    main()