import RPi.GPIO as GPIO
import time
import json
import paho.mqtt.client as mqtt
import pigpio
import sys
import math

# 로봇팔 모듈 경로
sys.path.insert(0, '/home/woosik/404-arm')

# --- [1. 설정 및 초기화] ---
TRIG = 17
ECHO = 27
MQTT_BROKER = "192.168.0.25"
MQTT_TOPIC = "ult02"

pi = pigpio.pi()
if not pi.connected:
    print("pigpio 데몬 연결 실패.")
    sys.exit()

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# --- [로봇팔 위치 설정] ---
HOME_POS = {
    26: -1.0,   # Base
    24: -0.1,   # 팔꿈치
    16:  0.5,   # 손목 회전
    4:  -0.2    # 집게
}
current_pos = HOME_POS.copy()
is_arm_running = False

# --- [2. 로봇팔 제어 함수] ---

def move_smooth_sine(targets, duration=1.0):
    global current_pos
    start_pos = current_pos.copy()
    moving_pins = {pin: target for pin, target in targets.items() if current_pos.get(pin) != target}
    
    if not moving_pins: return

    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        progress = elapsed_time / duration
        if progress >= 1.0: break
            
        multiplier = (1 - math.cos(math.pi * progress)) / 2
        for pin, target in moving_pins.items():
            start = start_pos[pin]
            current_pos[pin] = start + (target - start) * multiplier
            pi.set_servo_pulsewidth(pin, 1500 + (current_pos[pin] * 1000))
        time.sleep(0.01)

    for pin, target in moving_pins.items():
        current_pos[pin] = target
        pi.set_servo_pulsewidth(pin, 1500 + (target * 1000))

def run_arm_full_sequence():
    global is_arm_running
    is_arm_running = True
    
    try:
        # --- [감지 직후: 초기값 실행] ---
        print("\n[SYSTEM] 신호 감지! 초기 위치 정렬 중...")
        for pin, val in HOME_POS.items():
            pi.set_servo_pulsewidth(pin, 1500 + (val * 1000))
            current_pos[pin] = val
        
        print("[SYSTEM] 2초 대기 후 동작 시작...")
        time.sleep(2.0) 
        
        # --- [동작 시퀀스 시작] ---
        print("-> 물체 잡기")
        move_smooth_sine({4: 0.0}, duration=0.5) 
        time.sleep(0.1)

        print("-> 팔 들기")
        move_smooth_sine({24: -0.3, 16: 0.7}, duration=0.8)
        time.sleep(0.1)

        print("-> 목표 위치 회전")
        move_smooth_sine({26: 0.0}, duration=0.9)
        time.sleep(0.1)

        print("-> 팔 내리기")
        move_smooth_sine({24: -0.1, 16: 0.5}, duration=0.8)
        time.sleep(0.2)

        print("-> 집게 놓기")
        move_smooth_sine({4: -0.2}, duration=0.3)
        time.sleep(0.1)

        print("-> 빈 팔 들기")
        move_smooth_sine({24: -0.3, 16: 0.7}, duration=0.7)
        time.sleep(0.1)

        print("-> 베이스 복귀")
        move_smooth_sine({26: -1.0}, duration=0.9)
        time.sleep(0.1)

        print("-> 최종 위치 도달")
        move_smooth_sine(HOME_POS, duration=0.7)
        time.sleep(0.5)

    finally:
        # --- [핵심 추가: 동작 종료 후 신호 차단] ---
        # 다음 신호가 올 때까지 모터의 전원(신호)을 완전히 끕니다.
        for pin in HOME_POS.keys():
            pi.set_servo_pulsewidth(pin, 0)
        
        is_arm_running = False
        print("[SYSTEM] 시퀀스 종료 및 서보 Release. 다음 신호를 대기합니다.")

# --- [3. 메인 루프] ---

def get_distance(timeout=0.05):
    GPIO.output(TRIG, GPIO.LOW)
    time.sleep(0.02)
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

def main():
    last_action_time = 0
    mqtt_client = mqtt.Client()

    try:
        mqtt_client.connect(MQTT_BROKER, 1883, 60)
        mqtt_client.loop_start()
        print("--- 시스템 가동: 감지 대기 중 (간격: 25초) ---")

        while True:
            if is_arm_running:
                time.sleep(0.5); continue

            dist = get_distance()
            curr_time = time.time()

            # 10.5cm 이내 감지 및 25초 간격 제한
            if dist is not None and dist < 10.5:
                if curr_time - last_action_time >= 25:
                    print(f"🎯 물체 감지! ({dist:.1f}cm)")
                    mqtt_client.publish(MQTT_TOPIC, json.dumps(True))
                    
                    # 시퀀스 실행 (내부에 초기화 및 2초 대기 포함)
                    run_arm_full_sequence()
                    
                    last_action_time = time.time()
            
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\n중단됨")
    finally:
        for pin in HOME_POS.keys(): pi.set_servo_pulsewidth(pin, 0)
        pi.stop(); GPIO.cleanup(); mqtt_client.disconnect()

if __name__ == "__main__":
    main()