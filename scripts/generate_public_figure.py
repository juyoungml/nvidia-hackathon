"""Draw the public PreDist case-29 paired temperature series for the landing.

Renders ``data/holdout-29.json`` (supply temperature vs. setpoint) to
``web/assets/system2-case29-trend.png``. Requires ``rsvg-convert`` (librsvg)
on PATH. Takes no options.

Usage::

    uv run python scripts/generate_public_figure.py
"""

import argparse
import json
import subprocess
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/holdout-29.json"
TARGET = ROOT / "web/assets/system2-case29-trend.png"


def main() -> None:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    case = json.loads(SOURCE.read_text())
    rows = case["measurement_window"]["rows"]
    assert len(rows) == 144
    width, height = 1600, 650
    left, right, top, bottom = 110, 1510, 105, 525
    low, high = 50, 75

    def point(index: int, value: float) -> str:
        x = left + index * (right - left) / (len(rows) - 1)
        y = bottom - (value - low) * (bottom - top) / (high - low)
        return f"{x:.1f},{y:.1f}"

    actual = " ".join(point(i, row["s_hc1_supply_temperature"]) for i, row in enumerate(rows))
    target = " ".join(
        point(i, row["s_hc1_supply_temperature_setpoint"]) for i, row in enumerate(rows)
    )
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="1600" height="650" fill="#f9f9f3"/>',
        '<text x="110" y="43" font-family="Arial,sans-serif" font-size="23" font-weight="700" fill="#183a32">SECONDARY HEATING CIRCUIT / SUPPLY TEMPERATURE</text>',
        '<text x="1510" y="43" text-anchor="end" font-family="Arial,sans-serif" font-size="17" fill="#748578">144 PAIRED PUBLIC READINGS · 10-MINUTE INTERVALS</text>',
    ]
    for temp in range(low, high + 1, 5):
        y = bottom - (temp - low) * (bottom - top) / (high - low)
        svg.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="#d7ded3" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="90" y="{y + 6:.1f}" text-anchor="end" font-family="Arial,sans-serif" font-size="16" fill="#89998b">{temp}°</text>'
        )
    for i in (0, 36, 72, 108, 143):
        x = left + i * (right - left) / (len(rows) - 1)
        stamp = rows[i]["timestamp"][5:16]
        svg.append(
            f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}" stroke="#e5eae0" stroke-width="1"/>'
        )
        svg.append(
            f'<text x="{x:.1f}" y="555" text-anchor="middle" font-family="Arial,sans-serif" font-size="15" fill="#829386">{escape(stamp)}</text>'
        )
    svg += [
        f'<polyline points="{target}" fill="none" stroke="#bf7850" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>',
        f'<polyline points="{actual}" fill="none" stroke="#285e4c" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>',
        '<circle cx="1510" cy="291.5" r="8" fill="#285e4c" stroke="#f9f9f3" stroke-width="3"/>',
        '<circle cx="1510" cy="293.2" r="5" fill="#bf7850"/>',
        '<line x1="110" y1="604" x2="149" y2="604" stroke="#285e4c" stroke-width="4"/>',
        '<text x="160" y="610" font-family="Arial,sans-serif" font-size="17" fill="#385e4b">MEASURED SUPPLY</text>',
        '<line x1="405" y1="604" x2="444" y2="604" stroke="#bf7850" stroke-width="4"/>',
        '<text x="455" y="610" font-family="Arial,sans-serif" font-size="17" fill="#996745">SETPOINT</text>',
        '<text x="1510" y="610" text-anchor="end" font-family="Arial,sans-serif" font-size="17" fill="#536e5e">LAST PAIR 14:10  ·  63.9°C / 63.8°C</text>',
        "</svg>",
    ]
    svg_text = "\n".join(svg)
    subprocess.run(
        ["rsvg-convert", "--output", str(TARGET)],
        input=svg_text.encode(),
        check=True,
    )
    print(TARGET.relative_to(ROOT), TARGET.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
