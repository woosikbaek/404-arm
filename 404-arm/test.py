import pigpio
import time
import math

# 1. pigpio 연결
pi = pigpio.pi()

if not pi.connected:
    print("에러: 'sudo pigpiod'가 실행 중인지 확인하세요.")
    exit()

# [설정] 최신 초기값 반영
current_positions = {
    26: -1.0,   # Base
    25:  0.55,   # 어깨
    24:  0.1,   # 팔꿈치
    16:  0.5,   # 손목 회전
    12:  0.0,   # 손목 상하
    4:  -0.2    # 집게
}

def move_servo_smooth(pin, target_val, duration=1.0):
    """
    Sine 가감속을 이용하여 특정 핀을 부드럽게 이동시킵니다.
    """
    start_val = current_positions[pin]
    
    # 이동 거리가 없으면 종료
    if start_val == target_val:
        return

    start_time = time.time()
    
    while True:
        elapsed_time = time.time() - start_time
        progress = elapsed_time / duration
        
        if progress >= 1.0:
            break
            
        # Sine Ease In-Out 공식
        multiplier = (1 - math.cos(math.pi * progress)) / 2
        current_val = start_val + (target_val - start_val) * multiplier
        
        # 실제 모터에 신호 전송
        pulsewidth = 1500 + (current_val * 1000)
        pi.set_servo_pulsewidth(pin, pulsewidth)
        
        time.sleep(0.01) # 100Hz 제어 주기

    # 마지막 위치 정확히 고정
    pi.set_servo_pulsewidth(pin, 1500 + (target_val * 1000))
    current_positions[pin] = target_val

try:
    print("=" * 50)
    print("   로봇팔 Sine 부드러운 튜닝 모드 (pigpio)")
    print("=" * 50)
    
    sort_pins = [26, 25, 24, 16, 12, 4] 
    
    # [단계 1] 초기 정렬도 부드럽게 진행
    print("시스템 부드러운 정렬 중...")
    for pin in sort_pins:
        val = current_positions[pin]
        # 초기 정렬은 현재 위치를 모르므로 일단 Snap 이동 후 짧은 대기
        pi.set_servo_pulsewidth(pin, 1500 + (val * 1000))
        print(f"-> 핀 {pin:2d}번 정렬: {val:>5.2f}")
        time.sleep(0.3)

    print("\n[사용 방법]")
    print(" - '핀번호 위치값' (예: 24 0.36)")
    print(" - '핀번호 위치값 시간' (예: 26 0.5 2.0 -> 26번을 2초 동안 느리게 이동)")
    print(" - 'show': 현재 수치 확인 / 'exit': 종료")
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
            
            # 핀번호와 위치값은 필수
            if len(parts) < 2:
                print("입력 오류: '핀번호 위치값' 형식")
                continue

            pin = int(parts[0])
            target_val = float(parts[1])
            
            # 세 번째 인자로 시간을 입력하면 그 시간만큼 느리게 이동 (기본 1.0초)
            duration = float(parts[2]) if len(parts) == 3 else 1.0

            if pin in current_positions:
                print(f"-> 핀 {pin}번 {duration}초 동안 부드럽게 이동 중...")
                move_servo_smooth(pin, target_val, duration)
                print(f"-> 핀 {pin}번 이동 완료: {target_val}")
            else:
                print(f"오류: 유효한 핀 번호가 아닙니다.")

        except ValueError:
            print("오류: 올바른 숫자를 입력해주세요.")

except KeyboardInterrupt:
    print("\n사용자 중단")

finally:
    print("\n[종료] 모든 모터 전원 차단 (Release)")
    for pin in current_positions.keys():
        pi.set_servo_pulsewidth(pin, 0)
    pi.stop()
