# Plant Reliability Agent

> 설비 이상 신고가 들어오면 NVIDIA Nemotron 에이전트가 먼저 자료를 조사하고, 다음에 확인할 항목을 원본 근거와 함께 엔지니어에게 넘깁니다.

**[Live demo](http://juyoung.site/nvidia-hackathon/)** · [보고서 PDF](submission/NVIDIA%20해커톤_Sona_Plant%20Reliability%20Agent.pdf) · [발표 슬라이드](submission/slides/Plant_Reliability_Agent_submission.pptx) · [평가 결과](evaluation/cycle5/RESULTS.md) · [구조 설명](docs/architecture.md)

Team Sona · NVIDIA Korea Agentic AI Hackathon 제출작

![전체 구조: 현장 데이터(도면·TM·WO·트렌드), System 1 상시 감시(계획), System 2 원인 조사(구현)](docs/assets/architecture.png)

## 한눈에 보기

- **문제**: 발전·열공급 설비의 비계획 정지는 비용이 큽니다. 원인 조사에 필요한 계측, 신고, 정비 이력은 여러 시스템에 흩어져 있고, 보안 요구 때문에 외부 클라우드 AI를 쓰기 어렵습니다.
- **해법**: 현장 안에 배포할 수 있는 NVIDIA Nemotron 기반 에이전트입니다.
  - **System 1 (상시 감시, 계획)**: 시계열 전처리 → Nemotron Nano가 후보를 선별해 알람을 올립니다.
  - **System 2 (원인 조사, 구현)**: 신고나 알람이 들어오면 Nemotron 3 Ultra가 읽기 전용 도구 6종에서 필요한 자료를 골라 읽고, 점검안을 씁니다. 점검안은 **근거 연결 검사**를 통과해야 엔지니어에게 표시됩니다.
- **데모**: 공개 지역난방 데이터 PreDist v2의 실제 신고로 System 2 조사를 재생합니다. 점검 항목을 누르면 에이전트가 참고한 원본 기록과 조회 순서가 열립니다.
- **결과**: 32건 평가에서 Nemotron 3 Ultra **26/32 (81%)**, 끝까지 작성한 점검안은 모두 근거 연결 검사 통과(근거 조작 0건). [상세](#평가-결과)

## Quickstart

API 키 없이 저장된 실제 실행을 로컬에서 봅니다(Python 3.12 이상).

```sh
git clone https://github.com/juyoungml/nvidia-hackathon.git && cd nvidia-hackathon
python3 scripts/serve_demo.py --port 8771
# 브라우저: http://127.0.0.1:8771/web/  (조사 데모: /web/system2.html)
```

데모 화면은 저장된 실행을 재생하며 모델을 새로 호출하지 않습니다. 실제 모델 실행은 [재현](#재현)을 보세요.

## 구조

```text
 설비 계측 ──> [System 1 (상시 감시, 계획)]  시계열 전처리 → Nemotron Nano
                     │ 알람 / 조사 요청
                     v
 이상 신고 ──> [System 2 (원인 조사, 구현)]  Nemotron 3 Ultra (NIM)
                 │ ⇅ 도구 호출 / 조회 결과 (접수 시각 이전 자료만)
                 v
   읽기 전용 도구 6종 (선택: NeMo Agent Toolkit 경유)
   계측 · 센서 정의 · 과거 신고 · 정비 이력 · 편차 구간 · 시간 창(최대 24행)
                 │
                 v
   근거 연결 검사: 인용한 근거 ID가 실제 조회 기록인지 확인
                 │
                 v
             [엔지니어]  점검안(다음 확인 항목 + 이유 + 원본 기록 + 데이터로 알 수 없는 것) 검토
```

1차측/2차측 유량, 공급온도/실내 온도처럼 헷갈리기 쉬운 구분은 도구와 한계 목록에서 처리합니다. 자세한 설계는 [docs/architecture.md](docs/architecture.md)에 있습니다.

## 평가 결과

PreDist v2 제조사 1의 적격 신고 **32건**(그중 21건은 개발 중 한 번도 쓰지 않은 사건), 사건당 1회 실행. 통과 기준은 **근거 연결 검사**(스키마 유효 + 실제 조회한 근거 ID만 인용)이며, 진단 정확도가 아닙니다. 프로토콜은 [PROTOCOL.md](evaluation/cycle5/PROTOCOL.md), 결과는 [RESULTS.md](evaluation/cycle5/RESULTS.md)에 있습니다.

| 구성 | 통과 (32건) | 새 사건 21건 | 비고 |
|---|---:|---:|---|
| Claude Code + Sonnet 5 (클라우드 참고 상한) | 32/32 | 21/21 | 보안상 현장 사용 불가 |
| Nemotron 3 Ultra, 첫 시도 | 15/32 | 11/21 | NVIDIA API 오류(HTTP 500/429) 13건 포함 |
| Nemotron 3 Ultra, API 오류 건 저속 재실행 후 | **26/32 (81%)** | 18/21 | API 오류 0건 |

- Ultra가 끝까지 작성한 점검안 26개는 모두 근거 연결 검사를 통과했습니다(근거 조작 0건).
- 남은 실패 6건(사례 5, 11, 40, 47, 62, 64)은 모두 같은 원인입니다. 시간 창 조회에서 24행을 넘는 구간을 요청했고, 프로토콜상 잘못된 도구 인자는 즉시 실패로 처리됩니다.
- 도구 보완: 24행을 넘는 요청은 이제 오류 대신 최근 24행으로 잘라 반환하고 잘랐다는 사실을 결과에 표시합니다(`poc/temporal_tools.py`).
<!-- CLIP_RESULT -->

![32건 평가 결과](figures/eval-cycle5.png)

이전 4건 비교(Ultra 2/4, Sonnet 5 4/4)는 [evaluation/cycle4/RESULTS.md](evaluation/cycle4/RESULTS.md)에 그대로 남겨 두었고 32건 결과와 합산하지 않습니다. 평가 문서 전체 목록은 [evaluation/README.md](evaluation/README.md)를 보세요.

## NVIDIA 기술

| 기술 | 맡은 일 | 상태 | 확인할 곳 |
|---|---|---|---|
| Nemotron 3 Ultra (NIM) | System 2에서 읽을 자료를 고르고, 결과를 대조해 구조화된 점검안 작성 | 구현 (모든 데모의 핵심 경로) | [live_investigation.py](poc/live_investigation.py) |
| NeMo Agent Toolkit 1.8.0 | 읽기 도구 6종 등록·실행 (계획 루프는 자체 Python) | 구현 (선택 경로 `--read-backend nat`) | [NAT_LIVE.md](integrations/NAT_LIVE.md) |
| OpenShell 0.1.2 | 허용된 읽기만 통과, 쓰기·외부 연결 차단 | 공개 fixture로 별도 시험 (전체 경로에는 미적용) | [OpenShell 시험](integrations/openshell-README.md) |
| Nemotron Nano | System 1 후보 선별·우선순위 | 계획 | [capacity-model.md](docs/capacity-model.md) |
| NeMo Retriever | 도면·문서 검색 | 계획 | [architecture.md](docs/architecture.md) |

## 저장소 구성

```text
poc/           System 2 에이전트: 조사 루프(live_investigation.py), 시점별 도구, 근거 연결 규칙
integrations/  NeMo Agent Toolkit 연동, OpenShell 정책·시험 기록, 구조화 출력 확인
evaluation/    평가 프로토콜·스크립트·trace·결과 (cycle3~5, 내용 평가, 제출 준비도)
data/          공개 PreDist v2에서 만든 사건 입력 JSON (회고 라벨은 evaluation/에 분리)
web/           정적 데모 화면 (소개, System 2 조사 재생)
docs/          구조 설명, System 1 처리량 계산, 데이터 출처, 준비 메모(archive/)
submission/    보고서 PDF·원고, 발표 슬라이드, 제출 안내, 제출 ZIP 빌더
figures/       평가 결과 그림, 발표용 구조 그림
scripts/       데모 서버, 사건 입력 생성, NVIDIA API 확인 등 보조 스크립트
tests/         데이터·접근 경계·조회 예산·근거 참조 회귀 시험
```

## 재현

```sh
uv sync --locked                                   # 기본 의존성 (개발 도구: --group dev)
uv run -q python -m unittest discover -s tests     # 회귀 시험, API 키 불필요
```

코드 품질 확인은 CI([python-quality.yml](.github/workflows/python-quality.yml))와 같습니다: `uv sync --group dev --locked` 후 `uv run ruff check .`, `uv run ruff format --check .`.

**실제 모델로 다시 실행하기.** 저장소 루트의 `.env`에 `NVIDIA_API_KEY=...`를 넣습니다([.env.example](.env.example) 참고, `.env`는 git에서 제외, 호출은 계정 사용량을 소비).

```sh
uv run python -m poc.live_investigation \
  --case replay-52.json \
  --read-backend direct \
  --handoff-policy bounded_finalize_v2 \
  --output .artifacts/my-live-case52.json
```

- API가 HTTP 429/500/502/503을 자주 돌려주면 `NVIDIA_HTTP_RETRIES=3 uv run python -m poc.live_investigation ...`처럼 재시도 횟수를 환경 변수로 지정합니다(기본 0, `Retry-After` 또는 10초씩 늘려 대기). 이 값은 `.env`가 아니라 실행 환경에서 읽습니다.
- `--read-backend nat`로 바꾸면 NeMo Agent Toolkit 경로를 씁니다. 별도 가상환경 설치가 필요하며 [NAT_LIVE.md](integrations/NAT_LIVE.md)에 설명이 있습니다.
- 출력 파일이 이미 있거나 고정된 `evaluation/cycle4` 안을 가리키면 실행을 거부합니다.

## 데이터와 라이선스

- 설비 데이터: [PreDist v2](https://zenodo.org/records/19496480), Fraunhofer IEE / enercity Netz GmbH, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). 사건 입력 구성은 [data/README.md](data/README.md), 출처 검토는 [docs/data-sources.md](docs/data-sources.md)에 있습니다.
- 도면 예시: 미국 DOE 공개 증기 계통도(공공 저작물). PreDist 설비의 도면이 아닌 독립 문서 탐색 예시입니다([출처](web/assets/SOURCES.md)).
- 현재 사건의 사후 진단·조치는 모델 입력과 데모에서 제외하고 `evaluation/`에 따로 보관합니다.
- 회사·고객 데이터와 API 키는 포함하지 않습니다.
- 코드 라이선스: 미정 (아직 LICENSE 파일이 없습니다).

## 한계

- 데모 데이터는 발전소가 아닌 지역난방 서브스테이션입니다. 발전소 현장 적용, 진단 정확도, 조사 시간 단축은 아직 측정하지 않았습니다.
- 근거 연결 검사는 인용 형식 검사입니다. 인용한 근거가 설명을 실제로 뒷받침하는지, 점검안이 현장에서 유용한지는 보증하지 않습니다.
- 32건 평가는 사건당 1회 실행이라 분산 추정이 없고, API 오류 건은 공개된 수정안(Amendment A–D)에 따라 재실행했습니다.
- 도구 6종은 난방 회로 중심이라 급탕·누수 등 다른 신고 유형에는 맞지 않는 부분이 있습니다.
- System 1, Nemotron Nano, NeMo Retriever, 도면·TM·WO 연결은 계획 단계이고, OpenShell은 전체 경로에 아직 적용하지 않았습니다.

## 팀

**Team Sona** · NVIDIA Korea Agentic AI Hackathon
