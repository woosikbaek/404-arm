import RPi.GPIO as GPIO
import time
import json
import paho.mqtt.client as mqtt
import pigpio
import sys

# 1. pigpio 연결 (로봇팔 제어용)
pi = pigpio.pi()
if not pi.connected:
    print("Error: 'sudo pigpiod'가 실행 중인지 확인하세요.")
    exit()

# 핀 번호 정의
PINS = {
    'base': 26, 'shoulder': 25, 'elbow': 24, 
    'wrist_v': 12, 'wrist_h': 16, 'gripper': 4
}

# [설정] 초기값 (Start Position)
HOME_POS = {26: -1.0, 25: 0.0, 24: 0.3, 16: 0.5, 12: 0.0, 4: -0.2}
current_pos = HOME_POS.copy()

# [설정] 초음파 및 MQTT
TRIG = 17
ECHO = 27
MQTT_BROKER = "192.168.0.25"
MQTT_PORT = 1883
MQTT_TOPIC_COMPLETE = "arm/complete"

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# --- [로봇팔 제어 함수] ---

def move_smooth_sync(targets, step=0.005, delay=0.01):
    """여러 핀을 동시에 부드럽게 이동"""
    global current_pos
    # 핀 번호가 올바른지 확인하고 이동이 필요한 것만 추출
    moving_pins = {pin: target for pin, target in targets.items() if current_pos.get(pin) != target}
    if not moving_pins: return

    while True:
        all_done = True
        for pin, target in moving_pins.items():
            if abs(current_pos[pin] - target) > step:
                if current_pos[pin] < target:
                    current_pos[pin] += step
                else:
                    current_pos[pin] -= step
                all_done = False
            else:
                current_pos[pin] = target
            
            # 실제 서보에 신호 전달
            pi.set_servo_pulsewidth(pin, 1500 + (current_pos[pin] * 1000))
        
        if all_done: break
        time.sleep(delay)

def run_arm_sequence():
    """사용자 정의 8단계 시퀀스"""
    print("\n[동작] 로봇팔 시퀀스 시작...")
    
    # Step 1: 집게(4) -> 0.0 
    move_smooth_sync({4: 0.0})
    time.sleep(0.5)
    
    # Step 2: 16/24 동시 -> (0.7, 0.2)
    move_smooth_sync({16: 0.7, 24: 0.2})
    time.sleep(0.5)
    
    # Step 3: Base(26) -> 0.0
    move_smooth_sync({26: 0.0})
    time.sleep(0.5)
    
    # Step 4: 16/24 동시 -> (0.5, 0.36)
    move_smooth_sync({16: 0.5, 24: 0.3})
    time.sleep(0.5)
    
    # Step 5: 집게(4) -> -0.2
    move_smooth_sync({4: -0.2})
    time.sleep(0.5)
    
    # Step 6: 16/24 동시 -> (0.7, 0.2)
    move_smooth_sync({16: 0.7, 24: 0.2})
    time.sleep(0.5)
    
    # Step 7: Base(26) -> -1.0
    move_smooth_sync({26: -1.0})
    time.sleep(0.5)
    
    # Step 8: 16/24 동시 -> (0.5, 0.36)
    move_smooth_sync({16: 0.5, 24: 0.3})
    
    print("[완료] 시퀀스 종료.")

# --- [초음파 센서 함수] ---

def get_distance():
    GPIO.output(TRIG, GPIO.LOW)
    time.sleep(0.01)
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)
    
    pulse_start = time.time()
    pulse_end = time.time()

    while GPIO.input(ECHO) == GPIO.LOW:
        pulse_start = time.time()
    while GPIO.input(ECHO) == GPIO.HIGH:
        pulse_end = time.time()
    
    distance = (pulse_end - pulse_start) * 34300 / 2
    return distance


def main():
    last_send_time = 0
    
    # 1. 초기화 (전원 인가 시 홈 위치로 0.5초 간격 정렬)
    print("시스템 초기화: 로봇팔 정렬 중 (0.5초 간격)...")
    init_order = [26, 25, 24, 16, 12, 4] # 베이스부터 차례대로
    for pin in init_order:
        val = HOME_POS[pin]
        pi.set_servo_pulsewidth(pin, 1500 + (val * 1000))
        time.sleep(0.5) # 요청하신 0.5초 텀
    
    try:
        mqtt_client = mqtt.Client()
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start() # MQTT 백그라운드 루프 시작
        print("시스템 준비 완료 (감지 대기 중)")

        while True:
            distance = get_distance()
            current_time = time.time()

            # 11cm 이내 감지 및 15초 쿨타임 확인
            if distance < 11 and (current_time - last_send_time >= 15):
                print(f"물체 감지({distance:.1f}cm)! MQTT 발행 및 로봇팔 구동")
                
                # A. MQTT 메시지 발행
                mqtt_client.publish(MQTT_TOPIC_COMPLETE, json.dumps(True))
                
                # B. 로봇팔 시퀀스 실행
                run_arm_sequence()
                
                # 동작이 다 끝난 시점을 기준으로 쿨타임 계산
                last_send_time = time.time() 

            time.sleep(0.2) # 센서 스캔 주기

    except KeyboardInterrupt:
        print("\n프로그램 종료 중...")
    finally:
        for pin in HOME_POS.keys():
            pi.set_servo_pulsewidth(pin, 0)
        pi.stop()
        GPIO.cleanup()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

if __name__ == "__main__":
    main()
