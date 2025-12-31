import RPi.GPIO as GPIO
import time
import json
import paho.mqtt.client as mqtt

# [설정] 기존 핀 번호 및 MQTT 정보 유지
TRIG = 5
ECHO = 6
MQTT_BROKER = "192.168.0.25"
MQTT_PORT = 1883
MQTT_TOPIC = "ult01"

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def get_distance():
    """초음파 거리 측정 (타임아웃 로직 개선)"""
    GPIO.output(TRIG, GPIO.LOW)
    time.sleep(0.01)
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)
    
    # 신호 시작 대기
    start_wait = time.time()
    while GPIO.input(ECHO) == GPIO.LOW:
        pulse_start = time.time()
        if pulse_start - start_wait > 0.1: return 999

    # 신호 종료 대기
    end_wait = time.time()
    while GPIO.input(ECHO) == GPIO.HIGH:
        pulse_end = time.time()
        if pulse_end - end_wait > 0.1: return 999

    return (pulse_end - pulse_start) * 34300 / 2

def main():
    last_send_time = 0 
    client = mqtt.Client()
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        print(f"--- 센서 감시 중 (Topic: {MQTT_TOPIC}, 기준: 10cm) ---")

        while True:
            dist = get_distance()
            curr_time = time.time()

            # 1. 10cm 이내 감지 시
            if dist <= 10.0:
                # 2. 25초 간격 제한 (중복 발신 방지)
                if curr_time - last_send_time >= 25:
                    # JSON 형식으로 True 전송
                    client.publish(MQTT_TOPIC, json.dumps(True))
                    
                    print(f"[{time.strftime('%H:%M:%S')}] 물체 감지({dist:.1f}cm)! 'True' 전송 완료.")
                    last_send_time = curr_time 

            time.sleep(0.2) # 반응 속도를 위해 측정 주기 0.2초로 단축

    except KeyboardInterrupt:
        print("\n종료합니다.")
    finally:
        client.loop_stop()
        client.disconnect()
        GPIO.cleanup()

if __name__ == "__main__":
    main()