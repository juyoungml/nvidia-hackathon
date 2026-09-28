# Slide deck validation

Final presentation: `Plant_Reliability_Agent_submission.pptx`

- SHA-256: `b50c032a1b37b40831a376330a924349228eefe31288ad6204d49dfff059cdc5`
- Slides: 9, 16:9, each with Korean speaker notes. Diagrams (district heating, agent result, architecture, NVIDIA roles) are native, editable PowerPoint shapes.
- 2026-09-28 rebuild: the deck was rebuilt from scratch by `build_deck.py` with python-pptx (`uv run --with python-pptx python submission/slides/build_deck.py`). The earlier `build_deck.mjs` is superseded and no longer matches the deck.
- The deck was rendered to PDF with LibreOffice (`soffice --headless --convert-to pdf`) and every slide was rasterized and visually checked for overflow, overlap and wrapping. It was not opened in Microsoft PowerPoint or Keynote.

Slides: 1 표지 · 2 문제 · 3 30초 배경(지역난방) · 4 실제 신고(사례 29) · 5 에이전트가 한 일 · 6 구조 · 7 NVIDIA 기술이 맡은 일 · 8 솔직한 결과 · 9 다음 단계

These are structural and visual checks. They do not establish diagnosis accuracy or field performance.
