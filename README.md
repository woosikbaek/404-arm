🤖 Smart Pick & Place Robotic Arm System이 프로젝트는 초음파 센서, 컨베이어 벨트, 그리고 4축 로봇팔을 MQTT 통신을 통해 유기적으로 제어하는 스마트 팩토리 자동화 시스템입니다.📁 프로젝트 구성 파일ultrasonic_sensor_1.py: 첫 번째 지점의 물체를 감지하여 MQTT 신호를 송신합니다.robotic_arm_control.py: 두 번째 초음파 센서로 물체를 감지하고, 로봇팔의 Pick & Place 시퀀스를 실행합니다. (Sine 가감속 적용)belt_relay_control.py: MQTT 명령에 따라 컨베이어 벨트(릴레이)를 구동하거나 정지시킵니다.🛠 주요 기능유기적 연동: 초음파 센서가 물체를 감지하면 즉시 MQTT 브로커를 통해 상태를 공유합니다.부드러운 모션 제어: math.cos 함수(Sine Ease In-Out)를 활용하여 로봇팔이 급격하게 움직이지 않고 부드럽게 가감속합니다.에너지 효율 모드: 동작이 끝난 로봇팔은 서보 신호를 차단(Release)하여 모터 과열을 방지하고 전류를 아낍니다.스마트 대기: 물체 감지 시 즉시 초기 위치로 정렬하고 2초의 안정화 시간을 가진 후 시퀀스를 시작합니다.원격 벨트 제어: power/control 토픽을 통해 벨트를 ON/OFF 할 수 있습니다.🔌 하드웨어 연결 정보 (Raspberry Pi BCM Pin)1. 로봇팔 (Servo Motors - pigpio 제어)관절핀 번호 (BCM)설명Base26로봇팔 하단 회전축Elbow24팔꿈치 관절Wrist16손목 상하/회전Gripper4물체를 집는 집게2. 센서 및 액추에이터장치핀 번호 (BCM)비고Ultrasonic 1Trig: 5, Echo: 6물체 진입 감지용Ultrasonic 2Trig: 17, Echo: 27로봇팔 작업 구역 감지용Relay (Belt)23컨베이어 벨트 모터 제어🚀 동작 시퀀스 (Robotic Arm)감지 대기: 초음파 센서가 10.5cm 이내의 물체를 감지할 때까지 대기합니다.초기화: 감지 시 즉시 홈 포지션으로 이동하고 2초간 대기합니다.Pick 단계: 물체를 집고(4번), 팔을 들어 올립니다(24번, 16번 동시).Place 단계: 목표 지점(26번 0.0)으로 회전 후 팔을 내리고 집게를 벌립니다.복귀: 팔을 다시 들어 올린 후 베이스를 원위치(-1.0)로 복귀시킵니다.Release: 서보 모터의 전류를 차단하고 다음 신호까지 대기합니다. (재동작 간격 25초)📦 설치 및 실행 방법1. 필수 라이브러리 설치Bashsudo apt-get update
sudo apt-get install pigpiod
pip install paho-mqtt RPi.GPIO
2. pigpio 데몬 실행Bashsudo pigpiod
3. 각 모듈 실행Bash# 벨트 제어 실행
python belt_relay_control.py

# 센서 1 실행
python ultrasonic_sensor_1.py

# 로봇팔 및 센서 2 실행
python robotic_arm_control.py
📡 MQTT 토픽 규격토픽메시지 (JSON)설명ult01true센서 1 물체 감지 시 송신ult02true센서 2 물체 감지 시 송신power/control{"command": "POWER_ON"}벨트 가동 명령power/control{"command": "POWER_OFF"}벨트 중지 명령Author: WoosikPath: /home/woosik/404-arm