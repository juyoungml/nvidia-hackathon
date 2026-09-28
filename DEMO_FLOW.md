# 심사위원용 데모 플로우

[Figma 스토리보드](https://www.figma.com/design/QpWqsuZE7NZ8dyvP71tSpu/Plant-Reliability-Agent-NVIDIA-Hackathon-Demo-Flow?node-id=2-3) · 기준 사건: 공개 PreDist v2 서브스테이션 21의 `no heat` 신고. 화면에 표시하는 실제 계측·사건 기록은 공개 자료이고, 계통도와 bbox는 자체 제작·수동 지정이다.

## 4분 발표 동선

| 순서 | 심사위원에게 보여줄 행동 | 핵심 문장 | 현재 상태 |
| --- | --- | --- | --- |
| 1. Signal watch | 신고와 24시간 계측을 비교하고 사건을 선택 | 센서가 정상처럼 보여도 고객 신고가 조사 이유가 된다. 작은 Nemotron Nano 또는 규칙이 좁은 선별 질문을 맡는다. | 설계. 실시간 ingest·Nano 선별 미구현 |
| 2. Evidence map | [현재 UI](web/index.html)에서 TT-21을 누른 뒤 고객 측 점선 bbox 선택 | 관측한 설비측 공급과 모르는 고객측 열전달을 같은 도면에서 분리한다. | 실행 가능한 UI. bbox는 수동 지정, 도면은 예시 |
| 3. Ultra investigation | [저장된 trace](poc/trace-52-nvidia-nemotron-3-ultra-550b-a55b.json)의 세 읽기 전용 도구 호출과 출처 확인 | Ultra는 원인 단정보다 출처가 있는 다음 점검을 만든다. 알려지지 않은 신호 태그는 경고로 남긴다. | 공개 사건 한 건 실행 |
| 4. Engineer review | 제안·근거·결측을 보고 승인 또는 수정 | 현장 조치의 최종 판단은 사람에게 있다. | 설계. 승인 워크플로 미구현 |
| 5. Economics bench | 기준선과 agent-assisted 식별 시간을 비교 | 식별 시간은 실험으로 측정하고 MWh·금액은 가정을 분리해 계산한다. | 설계. 실측 개선치 없음 |

발표 전환은 **사건을 왜 올렸나 → 어디까지 아나 → Ultra가 무엇을 읽었나 → 사람은 무엇을 결정하나 → 시간을 얼마나 줄였나** 순서다. 첫 3단계에서 현 POC를 재현하고, 4·5단계는 제품 목표 및 다음 평가로만 설명한다. `Jev`는 TypeSafe AI의 빠른 System 1 모델 아이디어로만 언급하고, 제품 의존성이나 별도 API 사용으로 표현하지 않는다.

## 구현 우선순위

1. **제출 전:** 현재 bbox UI와 Ultra trace를 연결한 2분 녹화, 추가 공개 사건 2건과 단순 검색·요약 기준선 평가, 출처·미정의 태그·사후 정보 누출 점검.
2. **시간이 남으면:** 공개 시계열 재생으로 System 1 규칙 기준선을 만들고, Nano 선별을 같은 사건에서 비교한다. 미탐과 불필요한 Ultra 호출을 모두 기록한다.
3. **후속 실험:** Restricted OpenShell에서 허용된 읽기와 차단된 외부 접근을 실행해 보안 주장을 검증한다. 재사용 권한이 확인된 공개 도면에서 자동 bbox·태그 연결을 별도 평가한다.
4. **경제성 연결:** 실제로 측정한 식별 시간만 Plant Economics Bench 입력으로 넣는다. 회수 MWh·금액은 출력·수요·판매 가능 조건을 가정으로 표시한다.

비공개 고객 도면·기록·crop·OCR 결과는 Figma, GitHub, NVIDIA hosted API, 제출 PDF에 넣지 않는다. 현재 Figma는 공개 데이터와 자체 제작 예시만 담는다.
