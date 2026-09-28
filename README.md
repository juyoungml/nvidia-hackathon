# Plant Reliability Agent

**설비 신고를, 원본 근거와 다음 점검으로.** 공개 지역난방 사건을 조사하는 NVIDIA Nemotron 기반 System 2 POC입니다. 발전소 현장 적용은 후속 목표이며, 회사·고객의 비공개 자료를 사용하지 않습니다.

## 심사위원: 먼저 데모를 확인하세요

Python 3.12+만 있으면 키 없이 실행할 수 있습니다. 압축을 풀고 저장소 루트에서:

```sh
python3 scripts/serve_demo.py --port 8771
```

브라우저에서 [랜딩](http://127.0.0.1:8771/web/) 또는 [최신 System 2 조사 기록](http://127.0.0.1:8771/web/system2.html)을 엽니다. 화면은 **실제 모델 실행을 저장한 재생**이며 클릭할 때 API를 호출하지 않습니다. 공개 사례 29의 점검을 선택하면 인용한 사실의 값·필드·시각·출처와 도구 조회 순서를 확인할 수 있습니다. 사례 52는 비교 종료 후 수정 확인 실행으로 구분합니다. localhost 주소는 외부에 공유하는 배포 URL이 아닙니다.

- [발표 슬라이드](submission/slides/Plant_Reliability_Agent_submission.pptx): 편집 가능한 PowerPoint와 발표 노트
- [제출 보고서](submission/REPORT.md): 실제 사건, 설계, 결과와 한계
- [제출 가이드](submission/SUBMISSION_GUIDE.md): 패키지 구조·재현·파일 제출
- [고정 비교 결과](evaluation/cycle4/RESULTS.md): 실패를 포함한 원본 실험

## 무엇을 구현했나요

신고 시점 이전의 공개 근거를 모델이 조회하고, 원본 사실 ID를 인용해 다음 점검을 생성합니다. 1차측 네트워크 유량과 고객 측 2차 유량, 공급온도와 실내 열 전달을 구분합니다. 시점별 공급온도·설정값을 함께 조회하고, 근거 참조와 조사 예산을 검사합니다. 관측 사실과 모델이 작성한 설명, 모르는 상태를 분리해 사람이 검토합니다.

NVIDIA hosted NIM `nvidia/nemotron-3-ultra-550b-a55b`가 계획과 구조화된 점검 생성을 담당합니다. 선택적 NAT 1.8.0 backend는 최신 6개 공개 읽기 도구를 실행합니다. 모델 계획 루프는 Python 코드가 관리합니다. OpenShell은 독립 공개 fixture 정책 시험이며 전체 hosted 경로의 보호 검증이 아닙니다. [현재 구조](ARCHITECTURE.md), [NAT 실행 증거](integrations/NAT_LIVE.md), [OpenShell 범위](integrations/openshell-README.md)를 참고하세요.

## 현재 결과와 해석

최초 정책의 Cycle 4 고정 비교에서 출력·참조 검사는 Ultra **2/4**, 제한된 Claude Code + Sonnet 5 **4/4**가 통과했습니다. Ultra 두 건은 유효 조회 6회 후 최종 생성으로 전환하지 못했습니다. `bounded_finalize_v2`는 이 전환을 수정했으며 기존 사례 52에서 별도 확인했습니다. 원래 비교 수치는 바꾸지 않았습니다.

이 비율은 진단 정확도가 아닙니다. 모델과 하네스가 함께 달라 하네스만의 우위를 주장할 수 없으며, 성공한 출력에도 인용 근거가 부족한 설명이 있습니다. [내용 검토](evaluation/readiness/content-review/v2/CONTENT_RESULTS.md)와 [구조 검증](evaluation/readiness/ablation/RESULTS.md)을 함께 제시합니다. 현장 식별 시간 절감, 24시간 전 예방, 자동 도면 인덱싱은 검증 전입니다.

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
