"""Render figures/eval-cycle5.png from evaluation/cycle5/results.json."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

if Path(FONT).exists():
    font_manager.fontManager.addfont(FONT)
    plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False

ARMS = (
    ("ultra", "Ultra\n1차 시도", "#b5d77a"),
    ("ultra_with_provider_rerun", "Ultra\n제공자 오류 재실행(최대 2회)", "#76b900"),
    ("sonnet", "Claude Code +\nSonnet 5", "#8a8a8a"),
)


def main() -> None:
    result = json.loads((HERE / "results.json").read_text())
    cases = result["cases"]
    fig = plt.figure(figsize=(11, 4.6), dpi=200)
    grid = fig.add_gridspec(
        3, 2, width_ratios=[1.2, 2.6], height_ratios=[1, 1, 1], wspace=0.12, hspace=0.9
    )

    ax = fig.add_subplot(grid[:, 0])
    labels, rates, texts, colors = [], [], [], []
    for arm, label, color in ARMS:
        runs = [c["arms"][arm] for c in cases if "validation_status" in c["arms"][arm]]
        passed = sum(r["reference_format_pass"] for r in runs)
        labels.append(label)
        rates.append(100 * passed / len(runs) if runs else 0)
        texts.append(f"{passed}/{len(runs)}")
        colors.append(color)
    bars = ax.bar(labels, rates, color=colors, width=0.65)
    for bar, text in zip(bars, texts, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 2, text, ha="center", fontsize=11
        )
    ax.set_ylim(0, 110)
    ax.set_ylabel("참조·형식 검사 통과율 (%)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", labelsize=7.5)

    # Per-case rows: 1 pass, 0 fail, -1 provider error, nan not run
    order = sorted(cases, key=lambda c: int(c["report_id"]))
    for row_index, (arm, label, _) in enumerate(ARMS):
        axc = fig.add_subplot(grid[row_index, 1])
        values = []
        for c in order:
            r = c["arms"][arm]
            if "validation_status" not in r:
                values.append(0)
            elif r["reference_format_pass"]:
                values.append(3)
            elif r["provider_error"]:
                values.append(1)
            else:
                values.append(2)
        cmap = ListedColormap(["#f0f0f0", "#f2c14e", "#d1495b", "#2e7d32"])
        axc.imshow([values], cmap=cmap, vmin=-0.5, vmax=3.5, aspect="auto")
        axc.set_yticks([])
        axc.set_title(label.replace("\n", " "), loc="left", fontsize=9, pad=3)
        axc.set_xticks(range(len(order)), [c["report_id"] for c in order], fontsize=6.5)
        axc.set_xticks([x - 0.5 for x in range(1, len(order))], minor=True)
        axc.grid(which="minor", axis="x", color="white", linewidth=1.5)
        axc.tick_params(which="minor", length=0)
        for spine in axc.spines.values():
            spine.set_visible(False)
        if row_index == len(ARMS) - 1:
            axc.set_xlabel("PreDist 보고서 ID (제조사 1)", fontsize=9)
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=c) for c in ("#2e7d32", "#d1495b", "#f2c14e", "#f0f0f0")
    ]
    fig.legend(
        handles,
        ["통과", "계약/참조 실패", "제공자 오류(HTTP)", "미완료"],
        loc="upper right",
        ncol=4,
        fontsize=8.5,
        frameon=False,
        bbox_to_anchor=(0.9, 0.95),
    )
    fig.suptitle("Cycle 5: PreDist 사건 32건 — 조사 계획 출력의 참조·형식 검사", fontsize=12)
    out = ROOT / "figures" / "eval-cycle5.png"
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    shutil.copy(out, ROOT / "web" / "assets" / "eval-cycle5.png")
    print(out)


if __name__ == "__main__":
    main()
