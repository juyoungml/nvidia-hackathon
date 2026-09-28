# 발표용 전체 구조 Figures

[Figma 편집본](https://www.figma.com/design/QpWqsuZE7NZ8dyvP71tSpu?node-id=14-3) — `03 · 전체 숲 — 발표 Figures` 페이지. 1600×900, 16:9. PNG는 각 장표에 바로 삽입할 수 있다. 텍스트와 도형은 Figma에서 편집 가능하다.

| 그림 | 발표 문장 | 파일 |
| --- | --- | --- |
| 01 문제 | 데이터는 많지만, 필요한 근거를 연결하는 일이 사람에게 몰려 식별이 늦어진다. | [01.png](01.png) |
| 02 제안 | Nano가 지속적으로 사건을 선별하고, Ultra가 필요한 근거를 조사해 사람에게 제안한다. | [02.png](02.png) |
| 03 기반 | 문서·도면·태그·센서를 미리 연결해 사건 발생 시 관련 근거부터 조회한다. | [03.png](03.png) |
| 04 가치 | 식별 시간을 줄였을 때 복구와 회수 가능한 발전량이 어떻게 달라지는지 평가한다. | [04.png](04.png) |

## 근거와 주장 범위

- 50,000은 사용자 제시 규모 예시다. 발전소 전반의 검증된 센서 수나 이번 POC의 처리 규모로 주장하지 않는다. 첫 장의 파형은 개념 설명용이다.
- System 1에는 시계열 전처리·특징 추출·규칙과 Nano를 결합한다. 원시 5만 신호를 LLM 프롬프트 하나로 넣는 설계가 아니다. 사건 단위로 Ultra에 전달하며 미탐·오탐·조사 비용을 평가한다.
- 전체 시스템 그림은 제안 아키텍처다. UI나 공개 사건 도구 호출 POC와 실제 연속 감시·사내 배포 완료를 구분한다.
- NeMo Retriever는 추출·임베딩·검색/재정렬의 적용 후보다. P&ID의 설비 태그, 배관 토폴로지, 개정본 일치 여부는 팀의 연결·검증 계층이 필요하다. ‘완벽한 인덱싱’ 또는 측정 전 속도 향상 배수를 주장하지 않는다.
- NeMo Agent Toolkit은 도구·워크플로 구성, 관측, 평가에 적용할 수 있다. 인덱싱 품질 자체를 보장하는 도구는 아니다.
- 사내 운영 설계는 원본·crop·OCR·임베딩을 사내 경계에서 처리하고 권한별 검색과 읽기 도구를 사용한다. 현재 그림은 보안 통제의 실증 결과가 아니다.
- 경제성 그림은 기존 Plant Economics Bench의 [고장 한 건 해부](https://www.figma.com/design/su3h8MbFsApi2pHNKnG5uJ?node-id=2-2)를 참고해 재구성했다. 식별 8h→0.5h, 준비 4h, 수리 8h는 설명용 가정이며 해커톤 실측 성능이 아니다. 실측 식별 시간과 복구로 이어지는 비율, 출력·판매 조건을 넣어 경제성을 평가해야 한다.
- 회사 비공개 원문·설비 식별자·도면은 포함하지 않았다.

## NVIDIA 공식 자료 확인 (2026-09-28)

- [NeMo Retriever 개요: 추출, OCR, 임베딩, 저장](https://docs.nvidia.com/nemo/retriever/latest/extraction/overview/)
- [NeMo Retriever: extraction, embedding, reranking](https://docs.nvidia.com/nemo/retriever/)
- [문서 인제스트 워크플로](https://docs.nvidia.com/nemo/retriever/26.5.0/extraction/workflow-document-ingestion/)
- [NeMo Agent Toolkit: 워크플로·도구·관측·평가](https://docs.nvidia.com/nemo/agent-toolkit/latest/index.html)

다음 발표 순서: 이 네 그림으로 전체 가치를 설명한 뒤, 공개 난방 사례의 도면 조사 UI를 작은 검증 사례로 제시한다. 공개 난방 사례 하나를 발전소 전체의 성능 검증으로 확장해 말하지 않는다.
