# Plant Reliability Agent System 2 제출 안내

이 압축 파일에는 코드, 데모, 발표 슬라이드, 실행 기록이 들어 있습니다. 공개 데이터(PreDist v2)만 사용했고 회사·고객 자료와 API 키는 없습니다.

데모 화면은 저장된 실제 실행을 다시 보여주며, 버튼을 눌러도 모델을 호출하지 않습니다. 사례 29는 개발 중 한 번도 보지 않은 설비이고, 사례 52는 조사 종료 로직을 고친 뒤 다시 돌린 결과입니다. 이전 실험을 재현하는 데 쓰는 회고 라벨(`evaluation/held-out-{32,52,62}.json`)은 모델 입력과 웹 서버에서 분리해 두었습니다.

## 키 없이 보기

Python 3.12 이상에서 ZIP을 압축 해제한 뒤 그 폴더에서 실행합니다.

```sh
python3 scripts/serve_demo.py --port 8772
```

브라우저에서 `http://127.0.0.1:8772/web/`을 엽니다. System 2 고정 재생은 `http://127.0.0.1:8772/web/system2.html`입니다. 발표 파일은 `submission/slides/Plant_Reliability_Agent_submission.pptx`이며 PowerPoint에서 편집할 수 있습니다. 서버는 로컬 호스트에만 바인딩하고 공개 파일의 지정 경로만 제공합니다.

## 실제 모델 재실행

고정 재생과 별도입니다. 저장소 루트의 `.env`에 본인 키를 `NVIDIA_API_KEY=...` 형식으로 넣어야 하며, 네트워크 호출과 요금이 발생할 수 있습니다. `.env`는 ZIP에 포함되지 않습니다. 먼저 기본 의존성을 잠근 버전으로 설치합니다.

```sh
uv sync --locked
uv run python -m poc.live_investigation --case replay-52.json \
  --output .artifacts/live-case52-direct.json --read-backend direct \
  --handoff-policy bounded_finalize_v2
```

`poc.live_investigation`은 현재 읽기 도구와 명시적 최종 생성 전환 정책을 사용하는 라이브 경로입니다. `evaluation/run_live_cycle.py`는 동결된 Cycle 4 비교 하네스이고, `poc/system2.py`는 이전 System 2 경로입니다. 자세한 사건 선택과 실행 조건은 `evaluation/cycle4/PROTOCOL.md`를 따릅니다. 키가 없거나 외부 서비스가 실패하면 저장된 결과로 데모를 볼 수 있으나, 그 상태는 새 live 재현 성공이 아닙니다. Claude 비교 실행은 별도 Claude Code 환경과 인증이 필요합니다.

NVIDIA Agent Toolkit(NAT) 1.8.0 선택 도구 읽기 경로는 `integrations/NAT_LIVE.md`에 설치 명령, 키 없는 여섯 도구 동등성 검사, 키가 필요한 live 실행 예시가 있습니다. `--read-backend nat`에서 모델이 선택한 읽기를 NAT가 수행하며 모델 API 호출 자체는 기존 NVIDIA 클라이언트가 수행합니다. 포함된 NAT case-52 기록은 고정 Cycle 4 비교와 별개인 개발 시험입니다. OpenShell 결과도 공개 fixture에 대한 별도 정책 시험입니다.

## 검증과 범위

```sh
uv sync --group dev --locked
uv run ruff check .
uv run ruff format --check .
uv run python -m unittest discover -s tests -v
```

`submission/RELEASE_MANIFEST.json`에 ZIP의 각 입력 파일에 대한 SHA-256과 크기가 있습니다. `python submission/build_bundle.py`로 같은 소스에서 ZIP을 재생성할 수 있습니다. 빌더는 명시된 공개 파일만 담고 개인 경로·자격 증명 형식을 검사합니다. 압축 해제 후 manifest를 이용해 파일 무결성을 확인할 수 있습니다.

이 POC는 지역난방 서브스테이션 자료를 사용합니다. 발전소 현장 적용, 진단 정확도, 장애 예방이나 8시간→30분 개선의 실측은 입증하지 않았습니다. 비교는 출력 계약과 근거 검토에 관한 것이며, 실패도 결과에 포함됩니다. 설명은 `evaluation/cycle4/RESULTS.md`와 `submission/REPORT.md`를 참고하세요. 팀명·인원·개인별 신청은 제출자가 최종 확인해야 합니다.

제출 준비도 기준과 점검 기록은 `evaluation/readiness/RUBRIC.md`, `SCORECARD.md`, `QA.md`에 있습니다. 내용 평가의 최종 검토는 `evaluation/readiness/content-review/v2/CONTENT_RESULTS.md`입니다. 첫 검토는 점검 문구가 가려진 패킷의 한계를 발견하여 `content-review/ERRATUM.md`와 함께 역사 기록으로 남겼고, v2를 주 결과로 사용합니다.
