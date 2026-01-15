# 🤖 Smart Pick & Place Robotic Arm System

이 프로젝트는 **초음파 센서**, **컨베이어 벨트**, 그리고 **4축 로봇팔**을 MQTT 통신을 통해 유기적으로 제어하는 스마트 팩토리 자동화 시스템입니다.

<div align="center">
  <a href="https://www.youtube.com/watch?v=gPBmVkVSfhc">
    <img src="https://img.youtube.com/vi/gPBmVkVSfhc/maxresdefault.jpg" width="80%" alt="404found 2차 프로젝트 시연영상">
    <br>
    <img src="https://img.shields.io/badge/YouTube-Watch_Video-red?style=for-the-badge&logo=youtube" alt="Youtube Button">
  </a>
</div>

## 📁 프로젝트 구성 파일
1. `ultrasonic_sensor_1.py`: 첫 번째 지점의 물체를 감지하여 MQTT 신호를 송신합니다. (핀 5, 6)
2. `robotic_arm_control.py`: 두 번째 초음파 센서로 물체를 감지하고, 로봇팔의 Pick & Place 시퀀스를 실행합니다. (핀 17, 27 / 서보 26, 24, 16, 4)
3. `belt_relay_control.py`: MQTT 명령에 따라 컨베이어 벨트(릴레이)를 구동하거나 정지시킵니다. (핀 23)

---

## 🛠 주요 기능
* **유기적 연동**: 초음파 센서가 물체를 감지하면 즉시 MQTT 브로커를 통해 상태를 공유합니다.
* **부드러운 모션 제어**: `math.cos` 함수(Sine Ease In-Out)를 활용하여 로봇팔이 급격하게 움직이지 않고 부드럽게 가감속합니다.
* **에너지 효율 모드**: 동작이 끝난 로봇팔은 서보 신호를 차단(Release)하여 모터 과열을 방지하고 전류를 아낍니다.
* **스마트 대기**: 물체 감지 시 즉시 초기 위치로 정렬하고 2초의 안정화 시간을 가진 후 시퀀스를 시작합니다.
* **원격 벨트 제어**: `power/control` 토픽을 통해 벨트를 ON/OFF 할 수 있습니다.

---

## 🔌 하드웨어 연결 정보 (Raspberry Pi BCM Pin)

### 1. 로봇팔 (Servo Motors - pigpio 제어)
| 관절 | 핀 번호 (BCM) | 초기값 (HOME) | 설명 |
|:---:|:---:|:---:|---|
| **Base** | 26 | -1.0 | 로봇팔 하단 회전축 |
| **Elbow** | 24 | -0.1 | 팔꿈치 관절 |
| **Wrist** | 16 | 0.5 | 손목 상하 이동 |
| **Gripper** | 4 | -0.2 | 물체를 집는 집게 |

### 2. 센서 및 액추에이터
| 장치 | 핀 번호 (BCM) | 비고 |
|:---:|:---:|---|
| **Ultrasonic 1** | Trig: 5, Echo: 6 | 물체 진입 감지용 |
| **Ultrasonic 2** | Trig: 17, Echo: 27 | 로봇팔 작업 구역 감지용 |
| **Relay (Belt)** | 23 | 컨베이어 벨트 모터 제어 |

---

## 🚀 동작 시퀀스 (Robotic Arm)
1.  **감지 대기**: 초음파 센서가 10.5cm 이내의 물체를 감지할 때까지 대기합니다. (25초 간격 제한)
2.  **초기화**: 감지 시 즉시 홈 포지션으로 이동하고 **2초간 대기**합니다.
3.  **Pick 단계**: 물체를 집고(4번), 팔을 들어 올립니다(24번, 16번 동시).
4.  **Place 단계**: 목표 지점(26번 0.0)으로 회전 후 팔을 내리고 집게를 벌립니다.
5.  **복귀**: 팔을 다시 들어 올린 후 베이스를 원위치(-1.0)로 복귀시킵니다.
6.  **Release**: 서보 모터의 전류를 차단하고 다음 신호까지 대기합니다.

---

## 📦 설치 및 실행 방법

### 1. 필수 라이브러리 설치
```bash
1.
sudo apt-get update
sudo apt-get install pigpiod
pip install paho-mqtt RPi.GPIO

2. pigpio 데몬 실행
Bash
sudo pigpiod

3. 각 모듈 실행 (각 터미널에서 실행)
Bash
python belt_relay_control.py
python ultrasonic_sensor_1.py
python robotic_arm_control.py

```

📡 MQTT 토픽 규격
토픽,메시지 (JSON),설명
ult01,true,센서 1 물체 감지 시 송신
ult02,true,센서 2 물체 감지 시 송신
power/control,"{""command"": ""POWER_ON""}",벨트 가동 명령
power/control,"{""command"": ""POWER_OFF""}",벨트 중지 명령

Author: Woosik

Project Path: /home/woosik/404-arm
