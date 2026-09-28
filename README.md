# Plant Reliability Agent — NVIDIA Korea Agentic AI Hackathon 2026

**에너지 설비의 알람을, 근거 있는 다음 점검으로.** 공개된 에너지 설비 운전·장애 기록을 과거 시점으로 재생하고, 에이전트가 관련 근거를 조사해 점검 계획을 만드는 해커톤 프로젝트입니다. 회사·고객 자료는 사용하지 않습니다.

This repository is a clean-room hackathon project. It contains only original code, attributed public references and records, and clearly labeled team-authored scenario text. It must not contain employer or customer source material.

The first public-data POC has run. Read [POC_RESULT.md](POC_RESULT.md) and its trace before extending the demo. See [STRATEGY.md](STRATEGY.md) for the product strategy, [DATA_SOURCES.md](DATA_SOURCES.md) for public data candidates, and [PLAN.md](PLAN.md) for the remaining experiments.

The competition's online submission closes on **2026-09-28 at 23:59 KST**. Every member of a 2–5 person team must submit an individual application; one application includes the team's service portfolio.

Python 3.12 and `uv` run the POC. After `uv sync --group dev`, use `uv run ruff check .`, `uv run ruff format --check .`, `uv run vulture poc scripts tests --min-confidence 80`, and `uv run python -m unittest discover -s tests -v`. GitHub Actions runs the same checks on pushes and pull requests.
