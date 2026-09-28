# 시스템 구조

Plant Reliability Agent는 두 단계로 설계했습니다.

- **System 1 (상시 감시, 계획)**: 설비 계측을 계속 보고 이상 후보를 알람으로 올립니다.
- **System 2 (원인 조사, 구현)**: 신고나 알람이 들어오면 필요한 자료를 골라 읽어 점검안을 쓰고, **근거 연결 검사**를 통과한 점검안만 엔지니어에게 넘깁니다.

이 저장소에서 구현·평가한 것은 System 2이며, 자동 제어나 설정 변경은 하지 않습니다.

![전체 구조: 현장 데이터, System 1 상시 감시(계획), System 2 원인 조사(구현)](assets/architecture.png)

실선은 구현·데모, 점선은 설계·계획, 녹색 테두리는 NVIDIA 기술입니다. 원본 벡터는 [assets/architecture.svg](assets/architecture.svg)입니다.

## 구현 범위

| 구성 요소 | 상태 | 근거 |
|---|---|---|
| System 2 조사 루프 (Nemotron 3 Ultra, hosted NIM) | 구현·평가 | [poc/live_investigation.py](../poc/live_investigation.py), [32건 평가](../evaluation/cycle5/RESULTS.md) |
| 읽기 전용 도구 6종 | 구현 | [poc/evidence_contract.py](../poc/evidence_contract.py), [poc/temporal_tools.py](../poc/temporal_tools.py) |
| NeMo Agent Toolkit 1.8.0 도구 실행 경로 | 구현 (선택) | [integrations/NAT_LIVE.md](../integrations/NAT_LIVE.md) |
| 근거 연결 검사 | 구현 | [poc/evidence_contract.py](../poc/evidence_contract.py) |
| OpenShell 0.1.2 격리 실행 | 공개 fixture로 별도 시험, 조사 루프에는 미적용 | [integrations/openshell-README.md](../integrations/openshell-README.md) |
| System 1: 시계열 전처리 → Nemotron Nano → 알람 | 계획 | [capacity-model.md](capacity-model.md) |
| NeMo Retriever 도면·문서 검색 | 계획 | — |

## 데이터 소스

설계상 현장 데이터는 네 가지입니다.

| 소스 | 내용 | 현재 데모 |
|---|---|---|
| 도면 문서 | P&ID, 로직 다이어그램 | 미사용 (NeMo Retriever 계획) |
| TM | 기술 메모, 과거 이상 신고 | PreDist 과거 고장 신고(`faults.csv`)로 대체 |
| WO | 작업 지시, 정비 기록 | PreDist 장애·정비 기록(`disturbances.csv`)으로 대체 |
| 트렌드 | 센서 시계열 | PreDist 계측 (신고 전 24시간, 10분 간격) |

데모는 공개 PreDist v2의 계측·고장 신고·정비 기록만 사용합니다. 출처와 라이선스는 [data-sources.md](data-sources.md)와 [../data/README.md](../data/README.md)에 있습니다.

## System 2 (원인 조사, 구현)

### 실행 단계

| 단계 | 처리 | 경계 |
|---|---|---|
| 사건 설정 | 공개 사건 입력(`data/*.json`)에서 설비 ID, 신고 분류, 결정 시각을 읽음 | 현재 사건의 사후 진단·조치는 입력에서 제외 |
| 계획 | Nemotron 3 Ultra가 도구를 골라 호출 | 계획 요청 최대 6회, 인자·시점 범위를 검사하고 잘못된 요청은 결과 보류 |
| 조회 | 선택된 도구가 공개 자료를 읽음 | 결정 시각 이전 자료만, 각 결과는 source ID·필드·시각·값이 있는 사실(fact)로 변환 |
| 최종 생성 | 같은 실행에서 조회한 사실만으로 구조화된 점검안 작성 | 점검 2~3개, 점검당 근거 1~4개, 고유 근거 최대 12개 |
| 근거 연결 검사 | 점검안의 ID·한도·인용을 검사 | 실패하면 점검안을 표시하지 않음 |
| 엔지니어 검토 | 점검안과 원본 기록을 함께 표시 | 현장 확인이 필요한 항목만 제안, 자동 설정 변경 없음 |

### 읽기 전용 도구 6종

| 도구 | 읽는 자료 |
|---|---|
| `get_recent_measurements` | 신고 전 계측 요약 |
| `get_signal_definitions` | 센서 정의 (1차측/2차측, 난방/급탕 구분, 정상 범위 부재 명시) |
| `get_prior_incidents` | 같은 설비의 과거 신고 |
| `get_maintenance_timeline` | 같은 설비의 장애·정비 기록 (시각이 해결을 뜻하지 않음을 명시) |
| `get_temporal_episodes` | 공급온도·설정값 편차 구간과 정확한 시작·끝 값 |
| `query_measurement_window` | 지정 시간 창의 계측 행 (최대 24행, 더 긴 요청은 최근 24행으로 잘라 반환하고 잘림을 표시) |

2°C 편차 기준은 설명용이며 운전 정상 범위나 고장 임계값이 아닙니다. 모델에는 "공급온도가 설정값을 따른다고 실내 난방이 된 것은 아니다" 같은 데이터 한계 목록도 함께 주어, 점검안에 데이터로 알 수 없는 것을 표시하게 합니다.

### 모델과 도구의 연결

`poc/live_investigation.py`가 계획 요청, 도구 실행, 최종 생성을 관리합니다. Ultra 호출은 NVIDIA hosted NIM의 chat completions API(`integrate.api.nvidia.com`)로 보냅니다.

- `--read-backend direct`: 도구를 Python 함수로 직접 호출합니다.
- `--read-backend nat`: 같은 도구를 NeMo Agent Toolkit 1.8.0의 function group(`public_predist_live_tools`)과 workflow로 실행합니다. NAT는 선택된 도구를 실행할 뿐 모델 루프를 돌리지 않습니다.

[직접/NAT 동등성 기록](../integrations/nat-live-smoke.json)은 도구 6종의 반환값과 사실 해시가 두 경로에서 같음을 확인합니다. [NAT 개발 실행 기록](../integrations/nat-live-case52.json)은 모델이 고른 조회 6회가 NAT로 실행되고 최종 점검안까지 이어지는 것을 보여 줍니다. 이 실행은 평가 점수에 포함하지 않습니다.

### 종료 정책

`--handoff-policy`는 필수입니다.

- `explicit_finish_v1`: 모델이 `finish_investigation`을 호출했을 때만 최종 점검안을 만듭니다.
- `bounded_finalize_v2`: 위에 더해, 유효한 조회로 계획 한도 6회를 모두 쓴 경우에도 모은 자료로 최종 점검안을 한 번 요청합니다. 이때 `planning_cap_handoff`와 `investigation_budget_exhausted`를 기록하며, 근거가 충분하다는 뜻은 아닙니다.

잘못된 도구 인자, 시점 위반, API 오류는 결과를 보류합니다. API 오류는 `NVIDIA_HTTP_RETRIES`로 같은 요청을 재시도할 수 있습니다(HTTP 429/500/502/503).

### 근거 연결 검사의 범위

검사는 점검안이 스키마에 맞는지, 인용한 근거 ID가 이번 실행에서 실제로 조회한 사실인지, 필요한 자료를 읽었는지를 확인합니다. 시각·수치 표현이 인용 사실과 어긋나 보이면 검토 경고를 붙이지만 이는 휴리스틱입니다. 인용이 설명을 실제로 뒷받침하는지, 진단이 맞는지는 판정하지 않으며 원본 trace는 사후 수정하지 않습니다.

## System 1 (상시 감시, 계획)

트렌드 데이터를 시계열 전처리로 요약해 이상 후보를 만들고, Nemotron Nano가 후보를 선별·우선순위화해 알람 또는 조사 요청을 System 2로 넘기는 구조입니다. 현재 구현은 없으며, 5만 신호 × 100ms 기준 처리량과 호출 예산 가정은 [capacity-model.md](capacity-model.md)에 있습니다.

## 데이터·보안

- 회사·고객 자료를 쓰지 않습니다. hosted 요청에는 공개 PreDist 사건과 거기서 파생한 사실만 들어갑니다.
- API 키는 로컬 `.env`에만 두며 git과 제출 ZIP에서 제외합니다.
- 로컬 데모 서버는 localhost에만 바인딩하고 공개 파일만 제공합니다.
- OpenShell은 공개 fixture에 대해 허용된 읽기 통과와 읽기·쓰기·직접 TCP 차단을 확인한 별도 시험입니다. 전체 조사 루프나 사내 배포의 보호를 검증한 것은 아닙니다.
- 설계상 목표는 현장 내부(DGX Spark 등) 배포이며, 그림의 "Ultra 기준 3~4대"는 추정입니다.
