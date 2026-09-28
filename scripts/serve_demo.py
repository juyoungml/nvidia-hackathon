"""Serve only public demo assets on the local loopback interface."""

from __future__ import annotations

import argparse
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "web"
WEB_SUFFIXES = {".html", ".css", ".js", ".json", ".svg", ".png", ".jpg", ".jpeg", ".webp"}
EXACT_FILES = {
    "POC_RESULT.md",
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
    if relative.as_posix() not in EXACT_FILES:
        if not (parts[0] == "web" and relative.suffix.lower() in WEB_SUFFIXES):
            return None
    candidate = ROOT / relative
    # The resolved path check also rejects symlinks pointing outside the allowed web subtree.
    if not candidate.is_file() or candidate.is_symlink():
        return None
    resolved = candidate.resolve()
    if parts[0] == "web" and not resolved.is_relative_to(WEB_ROOT.resolve()):
        return None
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
