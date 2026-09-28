# 제출 안내 — Plant Reliability Agent (Team Sona)

NVIDIA Korea Agentic AI Hackathon 제출물의 안내입니다. 공개 데이터(PreDist v2)만 사용했고 회사·고객 자료와 API 키는 포함하지 않습니다.

## 제출물

| 파일 | 내용 |
|---|---|
| [보고서 PDF](NVIDIA%20해커톤_Sona_Plant%20Reliability%20Agent.pdf) | 제출 보고서 (원고: [REPORT.md](REPORT.md)) |
| [발표 슬라이드](slides/Plant_Reliability_Agent_submission.pptx) | PowerPoint에서 편집 가능 |
| [제출 ZIP](NVIDIA%20해커톤_Sona_Plant%20Reliability%20Agent.zip) | 코드·데모·실행 기록 묶음. 각 파일의 SHA-256과 크기는 [RELEASE_MANIFEST.json](RELEASE_MANIFEST.json) |
| [2분 데모 대본](DEMO_SCRIPT.md) | 발표용 데모 순서 |

ZIP과 manifest는 제출 시점의 스냅샷입니다. 이후 저장소 문서가 갱신되면 manifest 해시와 다를 수 있습니다. `python submission/build_bundle.py`로 현재 소스에서 ZIP을 다시 만들 수 있으며, 빌더는 명시된 공개 파일만 담고 개인 경로·자격 증명 형식을 검사합니다.

## 바로 보기

- **라이브 데모**: http://juyoung.site/nvidia-hackathon/ (설치 없이 저장된 실제 실행 재생)
- **로컬 데모** (Python 3.12 이상, API 키 불필요): 저장소 또는 ZIP을 푼 폴더에서

  ```sh
  python3 scripts/serve_demo.py --port 8772
  ```

  `http://127.0.0.1:8772/web/`(소개)과 `http://127.0.0.1:8772/web/system2.html`(조사 재생)을 엽니다. 서버는 localhost에만 바인딩하고 공개 파일만 제공합니다.

데모는 저장된 실행을 재생하며 버튼을 눌러도 모델을 호출하지 않습니다. 사례 29는 개발 중 한 번도 보지 않은 설비이고, 사례 52는 조사 종료 정책(`bounded_finalize_v2`)을 고친 뒤 다시 실행한 결과입니다.

## 평가 결과 요약

32건 평가(사건당 1회), 통과 기준은 **근거 연결 검사**(스키마 유효 + 실제 조회한 근거 ID만 인용)이며 진단 정확도가 아닙니다.

- Claude Code + Sonnet 5 (클라우드 참고 상한): 32/32
- Nemotron 3 Ultra: 첫 시도 15/32 (NVIDIA API 오류 13건 포함) → API 오류 건 저속 재실행 후 26/32 (81%) → 24행 도구 보정 후 **32/32** (제출 이후 추가 실험), 새 사건 21건 중 18건
- Ultra가 끝까지 작성한 점검안 26개는 모두 통과(근거 조작 0건). 남은 실패 6건은 모두 24행을 넘는 시간 창 요청이며, 이후 도구가 최근 24행으로 잘라 반환하도록 보완했습니다.

상세: [evaluation/cycle5/RESULTS.md](../evaluation/cycle5/RESULTS.md). 이전 4건 비교는 [evaluation/cycle4/RESULTS.md](../evaluation/cycle4/RESULTS.md).

## 실제 모델 재실행

저장소 루트의 `.env`에 본인 키를 `NVIDIA_API_KEY=...`로 넣습니다. 네트워크 호출과 계정 사용량이 발생하며, `.env`는 git과 ZIP에서 제외됩니다.

```sh
uv sync --locked
uv run python -m poc.live_investigation --case replay-52.json \
  --output .artifacts/live-case52-direct.json --read-backend direct \
  --handoff-policy bounded_finalize_v2
```

- API가 HTTP 429/500을 자주 돌려주면 명령 앞에 `NVIDIA_HTTP_RETRIES=3`을 붙여 재시도합니다(`.env`가 아니라 실행 환경에서 읽음).
- `--read-backend nat`는 NeMo Agent Toolkit 1.8.0으로 도구를 실행합니다(모델 호출은 같은 NVIDIA 클라이언트). 설치와 키 없는 동등성 검사는 [integrations/NAT_LIVE.md](../integrations/NAT_LIVE.md)에 있습니다.
- OpenShell 결과는 공개 fixture에 대한 별도 정책 시험입니다([openshell-README.md](../integrations/openshell-README.md)).
- 키가 없거나 외부 서비스가 실패해도 저장된 결과로 데모를 볼 수 있지만, 그것은 새 실행의 재현 성공이 아닙니다. Claude 비교 실행은 별도 Claude Code 환경과 인증이 필요합니다.

## 검증

```sh
uv sync --group dev --locked
uv run ruff check .
uv run ruff format --check .
uv run -q python -m unittest discover -s tests
```

## 범위와 한계

- 데모 데이터는 지역난방 서브스테이션입니다. 발전소 현장 적용, 진단 정확도, 장애 예방, 조사 시간 단축(예: 8시간→30분)은 실측하지 않았습니다.
- System 1 (상시 감시, 계획)은 설계 단계이고, 구현·평가한 것은 System 2 (원인 조사, 구현)입니다.
- 회고 라벨(현재 사건의 사후 진단·조치)은 `evaluation/`에 분리해 모델 입력과 웹 서버에서 제외했습니다.
- 제출 준비도 기준과 점검 기록은 [evaluation/readiness/](../evaluation/readiness/), 내용 평가의 최종본은 [CONTENT_RESULTS.md](../evaluation/readiness/content-review/v2/CONTENT_RESULTS.md)에 있습니다.
