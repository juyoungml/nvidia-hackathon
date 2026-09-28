# 온라인 신청서 초안

서비스명: Plant Reliability Agent (임시명, 사용자 승인)
팀명: 미확정 / 제출 전 입력 필요
팀원 수: 미확정 / 2~5인 자격 및 전원 개별 신청 확인 필요

## 해결하고자 했던 문제 (300자 내외)

발전소에서 이상 징후가 발생하면 엔지니어는 운전 추세, 계통도, 매뉴얼, 과거 정비 기록을 오가며 문제를 조사합니다. 같은 설비의 정보가 여러 곳에 흩어져 있어 관련 근거를 찾고 대조하는 데 시간이 걸립니다. 알람만으로 원인을 단정할 수도 없습니다. Plant Reliability Agent는 조사할 사건과 관련 근거를 연결해, 엔지니어가 어디를 왜 확인해야 하는지 판단하도록 돕습니다. 예선에서는 회사 자료 대신 공개 에너지 설비 데이터를 사용해 이 흐름을 검증합니다.

## 서비스 소개 및 주요 기능 (500자 내외)

Plant Reliability Agent는 사건 선별과 근거 조사를 분리합니다. 로컬 Nemotron Nano 4B가 신고와 계측 집계에서 조사 필요성을 판단하면, hosted Nemotron Ultra가 읽기 도구로 계측과 과거 기록을 조회해 다음 점검을 제안합니다. 공개 PreDist 신고 3건과 별도 파생 시험 2건을 실행하고 출처·미정의 태그·요청 시간을 기록했습니다. 공개 DOE 계통도에서는 위치와 원문 설명을 연결합니다. NAT 1.8.0에서 별도 도구 워크플로를 실행했으며, OpenShell 0.1.2의 독립 fixture 시험에서 허용 읽기와 비허용 파일·쓰기·TCP 차단을 확인했습니다. Nano의 잘못된 선별과 Ultra의 인용 누락도 보존했습니다. 자동 도면 인덱싱, 현장 진단 정확도, 8시간에서 30분으로의 식별 단축은 아직 검증된 성과가 아닙니다.

## Tech Stack

- System 1: Ollama / nemotron-3-nano:4b (로컬), 구조화된 선별·규칙 검증
- System 2: NVIDIA hosted NIM / nvidia/nemotron-3-ultra-550b-a55b, 공개 replay 전용 읽기 도구
- NVIDIA NeMo Agent Toolkit 1.8.0: 별도 FunctionGroup·도구 재생 워크플로 실행
- NVIDIA OpenShell 0.1.2 + Docker: 독립 공개 fixture 정책 검증 (전체 모델 루프와 미통합)
- Python 3.12+, uv, Ruff, Vulture, unittest; HTML/CSS/JavaScript
- 데이터: PreDist v2 (CC BY 4.0), DOE 공개 증기 계통도
- NeMo Retriever 자동 인덱싱: 적용 계획, 현재 구현·성과 아님

## 제출 파일

파일 양식 제한 없음, 1개 파일 최대 100 MB. 최종 ZIP에는 설명 PDF, 재현 가능한 코드, 공개 데이터·출처, 저장된 실행 결과를 포함할 계획이다. GitHub 링크만 제출할 경우 심사위원 접근 권한 문제가 있으므로 단독 자료로 사용하지 않는다.
파일명: NVIDIA 해커톤_실제팀명_Plant Reliability Agent.zip

이 파일은 폼 입력 초안이다. 자동으로 폼을 제출하거나 개인정보 동의하지 않는다.
