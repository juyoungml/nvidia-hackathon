"""Serve only public demo assets on the local loopback interface."""

from __future__ import annotations

import argparse
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = {
    "web/index.html",
    "web/evidence.html",
    "web/investigation.html",
    "web/system2.html",
    "web/app.js",
    "web/landing.js",
    "web/investigation.js",
    "web/system2.js",
    "web/style.css",
    "web/landing.css",
    "web/investigation.css",
    "web/system2.css",
    "web/hotspots.json",
    "web/plant-detailed.svg",
    "web/substation.svg",
    "web/assets/doe-steam-figure-1.png",
    "web/assets/doe-steam-page-3.png",
    "web/assets/predist-record.png",
    "web/assets/predist-trend.png",
    "web/assets/system2-29.json",
    "web/assets/system2-52.json",
    "web/assets/system2-case29-trend.png",
    "web/assets/eval-cycle5.png",
    "README.md",
    "ARCHITECTURE.md",
    "DATA_SOURCES.md",
    "POC_RESULT.md",
    "submission/CASE_STORY.md",
    "submission/SUBMISSION_GUIDE.md",
    "submission/slides/Plant_Reliability_Agent_submission.pptx",
    "data/replay-52.json",
    "poc/trace-52-pipeline.json",
    "poc/trace-52-nvidia-nemotron-3-ultra-550b-a55b.json",
    "poc/trace-52-ollama-nemotron-3-nano-4b.json",
}


def resolve_demo_path(raw_target: str) -> Path | None:
    """Map a URL to a public file, rejecting escapes and every unlisted path."""
    path = unquote(urlsplit(raw_target).path)
    if path in {"", "/", "/web", "/web/"}:
        path = "/web/index.html"
    if "\\" in path or "\x00" in path:
        return None
    parts = Path(path.lstrip("/")).parts
    if not parts or any(part in {".", ".."} or part.startswith(".") for part in parts):
        return None
    relative = Path(*parts)
    if relative.as_posix() not in PUBLIC_FILES:
        return None
    candidate = ROOT / relative
    if not candidate.is_file() or any(
        (ROOT / Path(*parts[:index])).is_symlink() for index in range(1, len(parts) + 1)
    ):
        return None
    resolved = candidate.resolve()
    if not resolved.is_relative_to(ROOT.resolve()):
        return None
    return resolved


class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self._serve(send_body=True)

    def do_HEAD(self) -> None:  # noqa: N802
        self._serve(send_body=False)

    def _serve(self, *, send_body: bool) -> None:
        path = resolve_demo_path(self.path)
        if path is None:
            self.send_error(404, "Not part of the public demo")
            return
        content = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if path.suffix == ".md":
            content_type = "text/markdown"
        self.send_response(200)
        self.send_header(
            "Content-Type",
            f"{content_type}; charset=utf-8"
            if content_type.startswith("text/") or content_type == "application/javascript"
            else content_type,
        )
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if send_body:
            self.wfile.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8767)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), DemoHandler)
    print(f"Public demo: http://127.0.0.1:{args.port}/web/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
