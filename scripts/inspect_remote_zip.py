"""List a public ZIP over HTTP ranges without downloading the full archive."""

from __future__ import annotations

import argparse
import io
import json
import shutil
import urllib.request
import zipfile
from collections import OrderedDict


class HTTPRangeReader(io.RawIOBase):
    def __init__(self, url: str, size: int, block_size: int = 1 << 20):
        self.url = url
        self.size = size
        self.block_size = block_size
        self.position = 0
        self.blocks: OrderedDict[int, bytes] = OrderedDict()

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            target = offset
        elif whence == io.SEEK_CUR:
            target = self.position + offset
        elif whence == io.SEEK_END:
            target = self.size + offset
        else:
            raise ValueError(f"unsupported whence: {whence}")
        if target < 0:
            raise ValueError("negative seek")
        self.position = target
        return target

    def _block(self, index: int) -> bytes:
        if index in self.blocks:
            self.blocks.move_to_end(index)
            return self.blocks[index]
        start = index * self.block_size
        end = min(start + self.block_size, self.size) - 1
        request = urllib.request.Request(self.url, headers={"Range": f"bytes={start}-{end}"})
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 206:
                raise RuntimeError(f"server ignored range request: HTTP {response.status}")
            data = response.read()
        if len(data) != end - start + 1:
            raise RuntimeError(f"short range read: {start}-{end}")
        self.blocks[index] = data
        if len(self.blocks) > 12:
            self.blocks.popitem(last=False)
        return data

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = self.size - self.position
        size = min(size, max(0, self.size - self.position))
        chunks = []
        while size:
            index = self.position // self.block_size
            offset = self.position % self.block_size
            chunk = self._block(index)[offset : offset + size]
            chunks.append(chunk)
            self.position += len(chunk)
            size -= len(chunk)
        return b"".join(chunks)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("size", type=int)
    parser.add_argument("--contains", default="")
    parser.add_argument("--preview", help="exact member name to print as UTF-8")
    parser.add_argument("--save", help="save the named member to this local path")
    parser.add_argument("--max-bytes", type=int, default=20000)
    args = parser.parse_args()
    with zipfile.ZipFile(HTTPRangeReader(args.url, args.size)) as archive:
        if args.preview and args.save:
            with archive.open(args.preview) as source, open(args.save, "wb") as destination:
                shutil.copyfileobj(source, destination)
            print(args.save)
        elif args.preview:
            member = archive.getinfo(args.preview)
            if member.file_size > args.max_bytes:
                print(f"Previewing first {args.max_bytes} of {member.file_size} bytes")
            with archive.open(member) as source:
                print(source.read(args.max_bytes).decode("utf-8", errors="replace"))
        else:
            members = [
                {"name": member.filename, "bytes": member.file_size}
                for member in archive.infolist()
                if args.contains.lower() in member.filename.lower()
            ]
            print(json.dumps(members, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
