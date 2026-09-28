# 제출 패키지 검증 기록

2026-09-28. 구현·표시·재현을 확인한 기록이다. 진단 정확도나 공식 심사 점수를 뜻하지 않는다.

## 실제 실행과 변경 경계

- 최초 Cycle 4는 개발 2건·새 설비 2건이다. Ultra 2/4, 제한된 Sonnet 4/4가 출력·참조 검사를 통과했다. 원래 실패와 추론 자료를 보존했다.
- 이후 개발 사례 52에서 bounded handoff로 최종 생성을 확인했다. 최초 비교에 합산하지 않았다.
- 별도 NAT 통합 사례 52에서 실제 모델이 선택한 6개 도구가 NAT 1.8.0을 거쳤고 native 최종 생성이 참조 검사를 통과했다. heuristic 경고가 없다는 사실은 의미적 정확성을 보증하지 않는다.
- NAT 동등성 시험에서 6개 reader의 direct/NAT 결과와 사실이 일치했다. 버전·해시는 `integrations/nat-live-smoke.json`에 있다.
- 익명 AI 내용 평가를 실시했다. v1 packet의 점검 본문 누락을 발견해 원본을 보존하고 v2로 수정했다. 모델 출력과 고정 비교 수치는 바꾸지 않았다. 현장 전문가 검증은 아니다.

## 슬라이드와 웹

9장 슬라이드를 개별 렌더로 검토했다. 글자 가독성, 도면 비율, 편집 가능한 아키텍처와 비교 분모를 확인했다. 슬라이드 5는 조회·반환 루프와 최종 생성을 구분한다. 슬라이드 6은 모델이 오류를 내지 않는다고 단정하는 대신 도구가 제공하는 자료를 설명한다. 렌더와 검증 파일은 로컬 `.artifacts/slides`에 보존한다.

웹 담당자가 랜딩과 데모의 데스크톱·390px 모바일 초안, 사례 전환과 원문 근거 표시를 브라우저에서 검토했다. 상세 범위는 [WEB_QA.md](WEB_QA.md)에 있다. 이후 인용 경고·NAT 설명·아키텍처 변경은 정적 검사로 확인했다. Root의 기존 오류 브라우저 탭 접근은 URL 보안 정책에 차단돼 우회하지 않았다. 최종 웹 변경 전체를 root가 브라우저에서 재검수했다고 주장하지 않는다.

## 코드 검사

- `uv run ruff check .`: 통과
- `uv run ruff format --check .`: Python 59개 파일 통과
- `uv run vulture poc scripts tests integrations submission evaluation --min-confidence 80`: 통과
- `uv run python -m unittest discover -s tests -q`: 105개 실행, 오류 없음. 이 환경에 없는 optional NAT 검사 2개 건너뜀
- `.artifacts/nat-venv/bin/python -m unittest tests.test_nat_live -q`: 위 NAT 검사 2개 별도 통과
- optional NAT 환경의 `uv pip check`: 의존성 충돌 없음
- `uv run python -m unittest discover -s evaluation/readiness/ablation -p 'test*.py' -q`: 평가 자료·패킷·점수 출처 검사 5개 통과

이 수치는 위 검사를 수행한 시점의 결과다. 최종 패키지 검사는 아래에 별도로 기록한다.

## 최종 패키지

공개 파일 231개와 manifest를 담은 ZIP을 새 임시 디렉터리에 풀어 모든 파일 해시·크기와 Markdown 링크를 확인했다. 공개 페이지·자산·PPTX HTTP 8개 경로는 200, 비밀키·새 사후 평가 경로·초기 사후 평가 3개 파일 등 비공개 HTTP 경로 7개는 404였다. 압축 해제 환경에서 회귀 105개(선택적 NAT 2개 건너뜀)와 최신 live CLI 도움말이 통과했다. 동일 소스로 재빌드하면 같은 ZIP 해시가 생성됐다.

초기 3개 공개 사건의 사후 자료는 과거 평가 시험 재현용으로만 별도 evaluation 경로에 포함한다. 새로운 holdout-outcomes 자료는 제외한다. 이 자료들은 모델 입력 bundle이나 웹 서버에서 제공하지 않는다. “모든 평가 정답을 ZIP에서 제외했다”는 표현은 사용하지 않는다.

평가 문서 갱신 후 같은 검사로 ZIP을 다시 생성한다. ZIP 자체 해시·크기·최종 receipt는 자기 참조를 피하기 위해 패키지 밖의 `.artifacts/release-qa.json`에 보관한다. 최종 슬라이드 해시는 `29b1f4404ddc99cace60006e08f97c3bd4da4bd6925f6273e5df0e96e5b70aa1`이며 독립 검토자가 확인했다.

기술 재현 검사를 통과해도 최종 웹 시각 검수 대기 상태는 해제되지 않는다.
