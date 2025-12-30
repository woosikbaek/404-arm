import RPi.GPIO as GPIO
import time
import json
import paho.mqtt.client as mqtt
import pigpio
import sys
import math

# 로봇팔 모듈 경로 (기존 유지)
sys.path.insert(0, '/home/woosik/404-arm')

# --- [1. 설정 및 초기화] ---
TRIG = 17
ECHO = 27
MQTT_BROKER = "192.168.0.25"
MQTT_TOPIC = "ult02"
MQTT_TOPIC_COMPLETE = "ult02"

# pigpio 초기화
pi = pigpio.pi()
if not pi.connected:
    print("pigpiod 데몬이 실행 중인지 확인해 보슈")
    sys.exit()

# GPIO 설정
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# 로봇팔 홈 위치 및 상태
HOME_POS = {26: -1.0, 25: 0.0, 24: 0.3, 16: 0.5, 12: 0.0, 4: -0.2}
current_pos = HOME_POS.copy()
is_arm_running = False  # 로봇팔 동작 상태 플래그

# --- [2. 로봇팔 제어 함수군 (Sine 적용)] ---

def move_smooth_sine(targets, duration=1.0):
    """
    Sine 곡선을 이용한 부드러운 가감속(Ease In-Out) 이동
    targets: {핀번호: 목표값} 딕셔너리
    duration: 이동에 걸리는 총 시간 (초)
    """
    global current_pos
    start_pos = current_pos.copy()
    
    # 실제 이동이 필요한 핀들만 필터링
    moving_pins = {pin: target for pin, target in targets.items() if current_pos.get(pin) != target}
    if not moving_pins: return

    start_time = time.time()
    
    while True:
        elapsed_time = time.time() - start_time
        progress = elapsed_time / duration  # 0.0 ~ 1.0 진행률
        
        if progress >= 1.0:
            break
            
        # [핵심] Sine 가감속 공식
        # multiplier가 0에서 1까지 곡선을 그리며 변함
        multiplier = (1 - math.cos(math.pi * progress)) / 2
        
        for pin, target in moving_pins.items():
            start = start_pos[pin]
            # 부드러운 현재 위치 계산
            current_pos[pin] = start + (target - start) * multiplier
            pi.set_servo_pulsewidth(pin, 1500 + (current_pos[pin] * 1000))
            
        time.sleep(0.01) # 제어 주기 (100Hz)

    # 루프 종료 후 목표 위치에 정확히 고정
    for pin, target in moving_pins.items():
        current_pos[pin] = target
        pi.set_servo_pulsewidth(pin, 1500 + (target * 1000))

def run_arm_full_sequence():
    """8단계 시퀀스 실행 (Sine 방식 적용)"""
    global is_arm_running
    is_arm_running = True
    
    try:
        # duration 값을 조절하여 각 단계의 속도를 맞출 수 있습니다. (예: 0.8초)
        move_smooth_sine({4: 0.0}, duration=0.5) ; time.sleep(0.3)
        move_smooth_sine({16: 0.7, 24: 0.1}, duration=0.8) ; time.sleep(0.3)
        move_smooth_sine({26: 0.0}, duration=1.0) ; time.sleep(0.3)
        move_smooth_sine({16: 0.5, 24: 0.3}, duration=0.8) ; time.sleep(0.3)
        move_smooth_sine({4: -0.2}, duration=0.5) ; time.sleep(0.3)
        move_smooth_sine({16: 0.7, 24: 0.1}, duration=0.8) ; time.sleep(0.3)
        move_smooth_sine({26: -1.0}, duration=1.0) ; time.sleep(0.3)
        move_smooth_sine({16: 0.5, 24: 0.3}, duration=0.8)
    finally:
        is_arm_running = False
        print("[ARM] 시퀀스 완료.")

# --- [3. 초음파 센서 함수] ---

def get_distance(timeout=0.05):
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)

    start = time.time()
    while GPIO.input(ECHO) == GPIO.LOW:
        if time.time() - start > timeout: return None
    
    pulse_start = time.time()
    while GPIO.input(ECHO) == GPIO.HIGH:
        if time.time() - pulse_start > timeout: return None
    
    return (time.time() - pulse_start) * 34300 / 2

# --- [4. 메인 루프] ---

def main():
    last_action_time = 0
    mqtt_client = mqtt.Client()

    try:
        # 초기 정렬 (부드럽게 초기화)
        print("시스템 초기화: 0.5초 간격 정렬 시작...")
        for pin in [26, 25, 24, 16, 12, 4]:
            val = HOME_POS[pin]
            # 초기화는 단순하게 이동
            pi.set_servo_pulsewidth(pin, 1500 + (val * 1000))
            time.sleep(0.5)

        mqtt_client.connect(MQTT_BROKER, 1883, 60)
        mqtt_client.loop_start()
        print("모든 준비 완료. 감지 시작.")

        while True:
            if is_arm_running:
                time.sleep(1)
                continue

            dist = get_distance()
            curr_time = time.time()

            if dist and dist < 11:
                if curr_time - last_action_time >= 15:
                    payload = {
                        "request": True,
                        "distance_cm": round(dist, 2),
                        "timestamp": curr_time
                    }
                    mqtt_client.publish(MQTT_TOPIC, json.dumps(payload))
                    mqtt_client.publish(MQTT_TOPIC_COMPLETE, json.dumps(True))
                    print(f"감지! ({dist:.1f}cm) 동작 시작")

                    run_arm_full_sequence()
                    last_action_time = time.time()

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n중단됨")
    finally:
        for pin in HOME_POS.keys():
            pi.set_servo_pulsewidth(pin, 0)
        pi.stop()
        GPIO.cleanup()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

if __name__ == "__main__":
    main()
