# 데이터 출처와 라이선스

이 저장소는 공개 데이터만 사용합니다. 회사·고객 자료는 입력, 검색 대상, 평가 대상 어디에도 쓰지 않습니다.

## 사용한 데이터

| 데이터 | 쓰임 | 라이선스 | 비고 |
|---|---|---|---|
| [PreDist v2](https://zenodo.org/records/19496480) (DOI [10.5281/zenodo.19496480](https://doi.org/10.5281/zenodo.19496480)), Fraunhofer IEE / enercity Netz GmbH | System 2 데모와 평가의 모든 사건: 계측, 고장 신고, 장애·정비 기록, 센서 정의 | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | 지역난방 서브스테이션 93곳. 발전소가 아니므로 그렇게 표현하지 않습니다. |
| 미국 DOE *Improving Steam System Performance* Figure 1 | 웹 소개 페이지의 도면 탐색 예시 | 미국 정부 공공 저작물 | PreDist 설비와 무관한 일반 계통도입니다. [web/assets/SOURCES.md](../web/assets/SOURCES.md) |

사건 입력의 구성, 선택 규칙, 원본 CSV 해시와 재생성 방법은 [../data/README.md](../data/README.md)에 있습니다. 32건 평가의 사건 선택 규칙은 [../evaluation/cycle5/PROTOCOL.md](../evaluation/cycle5/PROTOCOL.md)에 있습니다.

## 재생(replay) 원칙

1. 실제 공개 신고 하나를 고르고 출처 URL, 데이터 버전, 라이선스, 설비 ID, 신고 시각을 기록합니다.
2. 결정 시각을 신고 시각으로 두고, 그 이전에 존재한 기록만 에이전트에게 줍니다.
3. 같은 신고의 사후 진단·조치·고장 라벨은 `evaluation/`에 분리하고 모델 입력과 도구 결과에 넣지 않습니다.
4. 과거 신고의 서술이 당시 운영자에게 실제로 보였는지는 PreDist가 보장하지 않으므로, 과거 맥락으로만 취급합니다.
5. 모델 호출(hosted NVIDIA API)에는 공개 사건과 거기서 파생한 사실만 보내고, 출처를 표시합니다.

## 검토했지만 쓰지 않은 후보

2026-09-28 데이터 선정 당시 함께 검토한 공개 데이터입니다. 라이선스는 당시 각 게시처 페이지 기준입니다.

| 후보 | 내용 | 라이선스 | 쓰지 않은 이유 |
|---|---|---|---|
| [EDP Wind Farm 1](https://edp.com/en/innovation/data) | 풍력 터빈 SCADA, 운전·알람 로그, 고장 기록 | CC BY-SA 4.0 | 일부 SCADA·로그 다운로드 링크에 접근할 수 없어 같은 터빈의 자료를 결합하지 못함 |
| [EDP thermal boiler units](https://edp.com/en/innovation/data/boiler-unit-y-year-xxx4) | 화력 보일러 1분 공정값 | CC BY-SA 4.0 | 연결된 고장·정비 기록이 없음 |
| [Hill of Towie wind farm](https://zenodo.org/records/22662930) | 10분 SCADA, 알람 로그, 정지 기록 | CC BY 4.0 | 연간 1.4–1.6GB로 일정 안에 다루기 큼 |
| [MetroPT-3](https://archive.ics.uci.edu/dataset/791/metropt%203%20dataset) | 지하철 압축기 신호와 고장·정비 구간 | CC BY 4.0 | 에너지 설비가 아님 |

PreDist v2는 계측, 신고, 정비 기록이 같은 설비 단위로 결합되어 있어 다중 소스 조사 시연에 가장 적합했습니다.
