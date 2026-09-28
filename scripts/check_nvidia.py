"""Verify an NVIDIA hosted NIM key without printing it.

Reads ``NVIDIA_API_KEY`` from a dotenv file (default ``.env`` in the current
directory), sends one tiny chat completion to the hosted NIM endpoint and
prints the HTTP status, model and reply as JSON. Exits 1 on an HTTP error.

Usage::

    uv run python scripts/check_nvidia.py [--env-file .env]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import urllib.error
import urllib.request


def load_key(path: pathlib.Path = pathlib.Path(".env")) -> str:
    for line in path.read_text().splitlines():
        if line.startswith("NVIDIA_API_KEY="):
            return line.partition("=")[2].strip().strip('"').strip("'")
    raise RuntimeError("NVIDIA_API_KEY missing from .env")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--env-file",
        type=pathlib.Path,
        default=pathlib.Path(".env"),
        help="dotenv file containing NVIDIA_API_KEY (default: .env)",
    )
    args = parser.parse_args()
    key = load_key(args.env_file)
    if not key:
        raise RuntimeError("NVIDIA_API_KEY is empty")
    payload = {
        "model": "nvidia/nemotron-3.5-lightning-30b-a3b",
        "messages": [{"role": "user", "content": "Reply with the single word OK."}],
        "temperature": 0,
        "max_tokens": 128,
        "chat_template_kwargs": {"enable_thinking": False},
        "stream": False,
    }
    request = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.load(response)
            print(
                json.dumps(
                    {
                        "http_status": response.status,
                        "model": data.get("model"),
                        "finish_reason": data["choices"][0].get("finish_reason"),
                        "content": data["choices"][0]["message"].get("content"),
                    },
                    ensure_ascii=False,
                )
            )
    except urllib.error.HTTPError as error:
        print(
            json.dumps(
                {"http_status": error.code, "error": error.read(500).decode(errors="replace")}
            )
        )
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
