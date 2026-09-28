# Slide deck validation

Final presentation: `Plant_Reliability_Agent_submission.pptx`

- SHA-256: `451502ed5be5f72aada665efd13ba435beb38b606bf109600d806a07fa30ee03`
- Slides: 12, 16:9, each with Korean speaker notes. Diagrams are native, editable PowerPoint shapes.
- Built by `build_deck.py` with python-pptx (`uv run --with python-pptx python submission/slides/build_deck.py`). `build_deck.mjs` is superseded.
- 2026-09-28 story rebuild: 문제(다운타임 비용) → 자료 분산 → 보안 제약·현장 설치(Nemotron + DGX Spark) → System 1/System 2 → System 1 설계 부하 → 공개 데이터 → 사례 29 → 에이전트 결과 → 구조·NVIDIA 기술 → 평가 → 다음 단계.
- Rendered to PDF with LibreOffice (`soffice --headless --convert-to pdf`); every slide was rasterized and visually checked for overflow, overlap and wrapping. Not opened in Microsoft PowerPoint or Keynote.

Slides: 1 표지 · 2 문제: 다운타임 비용 · 3 왜 어려운가 · 4 제약: 보안·현장 설치 · 5 해법: System 1 + System 2 · 6 System 1 설계 부하 · 7 데이터: 공개 PreDist v2 · 8 실제 신고(사례 29) · 9 에이전트가 한 일 · 10 구조와 NVIDIA 기술 · 11 평가 결과 · 12 다음 단계

Numbers and their status:
- Downtime: Siemens, *The True Cost of Downtime 2024* (Fortune Global 500, US$1.4T/yr, ~11% of revenue). Cross-industry, not power-plant-specific; labeled so on the slide.
- DGX Spark count: our estimate (params × 0.5 byte NVFP4 + 20–30% headroom vs 128 GB per unit). Ultra 550B-A55B: 3 minimum, ~4 recommended; Super 120B-A12B (not evaluated): 1. Not measured.
- System 1 load (50,000 signals × 100 ms): design calculation from `CAPACITY_MODEL.md`, not a measurement. System 1 is design/earlier experiment only.
- Evaluation slide: shows `figures/eval-cycle5.png` (Cycle 5, 32 PreDist reports, one run each): reference/format check passed Ultra 15/32 first attempt (13 provider HTTP 500/429 errors, 4 contract/reference failures; 15/19 = 79% excluding errors) and 16/32 after provider-error reruns (16/21 = 76% of runs that reached the model; 5 real model failures, all measurement-window requests >24 rows) vs Claude Code + Sonnet 5 reference 32/32. Source of truth: `evaluation/cycle5/RESULTS.md`. Not diagnosis accuracy. If the figure is absent, the script falls back to the earlier 4-case result (`EVAL_FIG`).

These are structural and visual checks. They do not establish diagnosis accuracy or field performance.
