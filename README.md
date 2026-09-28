# Plant Reliability Agent

**설비 이상 신고가 들어오면, 첫 조사는 에이전트가 먼저.** 관련 계측과 이력을 스스로 골라 읽고, 다음에 무엇을 확인해야 하는지 근거와 함께 엔지니어에게 넘겨줍니다. NVIDIA Nemotron 3 Ultra로 만들었고, 공개 지역난방 데이터(PreDist v2)의 실제 신고로 시연합니다.

## 데모 보기

Python 3.12 이상만 있으면 API 키 없이 볼 수 있습니다. 압축을 풀고 폴더에서 실행하세요.

```sh
python3 scripts/serve_demo.py --port 8771
```

- [소개 페이지](http://127.0.0.1:8771/web/)
- [조사 데모](http://127.0.0.1:8771/web/system2.html): 점검 항목을 누르면 에이전트가 참고한 원본 기록과 조회 순서가 열립니다. 저장된 실제 실행을 다시 보여주는 화면이라 모델을 새로 호출하지 않습니다.

함께 볼 자료:

- [발표 슬라이드](submission/slides/Plant_Reliability_Agent_submission.pptx) (발표 노트 포함)
- [보고서](submission/REPORT.md)
- [제출 안내](submission/SUBMISSION_GUIDE.md)
- [비교 실험 상세](evaluation/cycle4/RESULTS.md)

## 무엇을 하나요

1. 신고와 접수 시각을 받으면, 그 이전 자료만 볼 수 있게 준비합니다.
2. Nemotron 3 Ultra가 계측, 센서 정의, 과거 신고, 정비 이력, 시간대별 값 중 필요한 자료를 골라 읽습니다.
3. 다음에 확인할 항목과 그 이유를 내놓고, 모든 이유에 원본 기록을 연결합니다.
4. 데이터로 알 수 없는 것까지 함께 엔지니어에게 넘깁니다.

1차측 유량과 2차측 유량, 공급온도와 실내 온도처럼 설비 데이터에서 헷갈리기 쉬운 부분은 도구 단계에서 구분합니다.

사용한 NVIDIA 기술 (범용 챗봇이 아니라, NVIDIA 모델이 실제 도구를 고르고 그 결과로 근거 달린 점검안을 쓰는 에이전트 구조):

| 기술 | 맡은 일 | 상태 | 확인할 곳 |
|---|---|---|---|
| Nemotron 3 Ultra (NIM) | 도구 6종 중 무엇을 읽을지 고르고, 결과를 비교해 구조화된 점검안 작성 | 모든 데모의 핵심 경로 | [ARCHITECTURE.md](ARCHITECTURE.md) |
| NeMo Agent Toolkit 1.8.0 | 읽기 도구 6종 등록·실행 (계획 루프는 자체 Python) | 연동 완료 (`--read-backend nat`) | [NAT 연동](integrations/NAT_LIVE.md) |
| OpenShell 0.1.2 | 허용 읽기만 통과, 쓰기·외부 연결 차단 | 별도 시험 완료 (전체 경로 미적용) | [OpenShell 시험](integrations/openshell-README.md) |
| Nemotron Nano, NeMo Retriever | 상시 감시·재정렬, 문서·도면 검색 | 계획 | [ARCHITECTURE.md](ARCHITECTURE.md) |

## 결과

같은 자료로 Claude Code + Sonnet 5와 4건을 비교했습니다. 근거 연결 검사 통과는 Ultra **2/4**, Sonnet **4/4**입니다. Ultra가 놓친 2건은 조회 6번을 다 쓰고 조사를 끝내지 못한 경우였고, 한도에 닿으면 모은 자료로 정리하도록 고쳐(`bounded_finalize_v2`) 사례 52에서 확인했습니다. 비교 점수는 수정 전 그대로 둡니다.

둘 다 결과를 낸 2건의 내용 평가는 Ultra 41/48, Sonnet 42/48로 비슷했습니다([내용 평가](evaluation/readiness/content-review/v2/CONTENT_RESULTS.md)). 현장 전문가 평가와 실제 조사 시간 단축은 다음 단계에서 측정합니다.

## 실제 모델을 다시 실행하려면

NVIDIA API 키를 로컬 `.env`에 `NVIDIA_API_KEY=...` 형식으로 보관합니다. 키를 제출하거나 공유하지 않습니다. API 호출은 계정 사용량을 소비합니다. 먼저 직접 읽기 backend로 한 사건을 실행합니다:

```sh
uv sync --locked
uv run python -m poc.live_investigation \
  --case replay-52.json \
  --read-backend direct \
  --handoff-policy bounded_finalize_v2 \
  --output .artifacts/my-live-case52.json
```

기존 출력 경로를 덮어쓰지 않습니다. NAT backend의 설치·동등성 시험·실제 실행 명령은 [NAT_LIVE.md](integrations/NAT_LIVE.md)에 있습니다. 키나 optional NAT 환경이 없어도 저장 실행 데모는 열 수 있습니다. 새 실행은 원래 비교를 대체하지 않습니다.

## 품질 확인

```sh
uv run ruff check .
uv run ruff format --check .
uv run vulture poc scripts tests integrations submission evaluation --min-confidence 80
uv run python -m unittest discover -s tests -q
```

데이터·경계·예산·참조 회귀 시험을 포함합니다. optional NAT 시험은 해당 환경에서 별도로 실행합니다. [준비도 기준](evaluation/readiness/RUBRIC.md)은 공식 심사 배점이 아닌 사전에 고정한 내부 기준입니다.

## 자료와 이전 실험

PreDist v2는 [Fraunhofer IEE / enercity Netz GmbH 공개 자료](https://zenodo.org/records/19496480), CC BY 4.0입니다. 현재 사건의 사후 진단은 모델 입력과 공개 데모에서 제외합니다. 과거 회고적 기록이 당시 실제로 가용했는지는 확인되지 않았습니다. DOE 계통도는 독립적인 공개 문서 예시이며 PreDist 설비의 도면이 아닙니다.

`web/investigation.html`은 이전 Nano→Ultra 실험 화면입니다. 이전 PDF·영상·ZIP은 과거 스냅샷이며 최신 System2 제출 패키지와 구분합니다. Nano 재정렬·지속 감시와 NeMo Retriever는 후속 후보입니다.
