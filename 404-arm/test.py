import pigpio
import time

# 1. pigpio 연결
pi = pigpio.pi()

if not pi.connected:
    print("에러: 'sudo pigpiod'가 실행 중인지 확인하세요.")
    exit()

# [설정] 최신 초기값 반영
current_positions = {
    26: -1.0,   # Base
    25:  0.0,   # 어깨
    24:  0.36,   # 팔꿈치
    16:  0.5,   # 손목 회전
    12:  0.0,   # 손목 상하
    4:  -0.2    # 집게
}

def move_servo(pin, value):
    """지정한 핀을 해당 위치로 이동"""
    value = max(-1.0, min(1.0, value))
    pulsewidth = 1500 + (value * 1000)
    pi.set_servo_pulsewidth(pin, pulsewidth)
    current_positions[pin] = value

try:
    print("=" * 50)
    print("   로봇팔 0.5초 간격 순차 정렬 및 튜닝 모드")
    print("=" * 50)
    
    # [단계 1] 프로그램 실행 시 0.5초 간격으로 순차 정렬
    print("시스템 정렬 중 (0.5초 간격)...")
    # 핀 번호 순서대로(4, 12, 16...) 정렬하거나 원하는 순서가 있다면 리스트로 만드세요.
    sort_pins = [26, 25, 24, 16, 12, 4] 
    
    for pin in sort_pins:
        val = current_positions[pin]
        move_servo(pin, val)
        print(f"-> 핀 {pin:2d}번 이동 완료: {val:>5.2f}")
        time.sleep(0.5)  # 0.5초 텀 (전류 급증 방지 및 안정화)

    print("\n[알림] 모든 관절 정렬 완료.")
    print("-" * 50)
    print(" [사용 방법]")
    print(" - '핀번호 위치값' 입력 (예: 24 0.36)")
    print(" - 'show' 입력: 현재 수치 확인 / 'exit' 입력: 종료")
    print("-" * 50)

    while True:
        user_input = input(f"\n[입력]: ").strip().lower()

        if user_input == 'exit':
            break
        
        if user_input == 'show':
            print("\n--- 현재 위치값 ---")
            for pin in sort_pins:
                print(f"핀 {pin:2d}: {current_positions[pin]:>5.2f}")
            continue

        try:
            parts = user_input.split()
            if len(parts) != 2:
                print("입력 오류: '핀번호 위치값' 형식 (예: 26 -0.5)")
                continue

            pin = int(parts[0])
            val = float(parts[1])

            if pin in current_positions:
                move_servo(pin, val)
                print(f"-> 핀 {pin}번 이동 중...")
                time.sleep(0.5)  # 개별 이동 후에도 0.5초 텀을 주어 기계적 안정 확보
                print(f"-> 핀 {pin}번 이동 완료: {val}")
            else:
                print(f"오류: 유효한 핀 번호가 아닙니다.")

        except ValueError:
            print("오류: 숫자를 입력해주세요.")

except KeyboardInterrupt:
    print("\n사용자 중단")

finally:
    print("\n[종료] 모든 모터 전원 차단")
    for pin in current_positions.keys():
        pi.set_servo_pulsewidth(pin, 0)
    pi.stop()
