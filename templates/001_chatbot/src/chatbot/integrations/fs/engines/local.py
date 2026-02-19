"""
목적: 로컬 파일 시스템 엔진을 제공한다.
설명: 표준 라이브러리를 사용해 파일 조작을 수행한다.
디자인 패턴: 어댑터 패턴
참조: src/chatbot/integrations/fs/base/engine.py
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List, Optional

from chatbot.integrations.fs.base.engine import BaseFSEngine


class LocalFSEngine(BaseFSEngine):
    """로컬 파일 시스템 엔진 구현체."""

    @property
    def name(self) -> str:
        return "local"

    def write_text(self, path: str, content: str, encoding: str) -> None:
        self._ensure_parent(path)
        with open(path, "x", encoding=encoding) as handle:
            handle.write(content)

    def read_text(self, path: str, encoding: str) -> str:
        with open(path, "r", encoding=encoding) as handle:
            return handle.read()

    def list_files(
        self,
        base_dir: str,
        recursive: bool = False,
        suffix: Optional[str] = None,
    ) -> List[str]:
        if not os.path.isdir(base_dir):
            return []
        results: List[str] = []
        if recursive:
            for root, _, files in os.walk(base_dir):
                for name in files:
                    if suffix and not name.endswith(suffix):
                        continue
                    results.append(os.path.join(root, name))
            return results
        for name in os.listdir(base_dir):
            if suffix and not name.endswith(suffix):
                continue
            path = os.path.join(base_dir, name)
            if os.path.isfile(path):
                results.append(path)
        return results

    def exists(self, path: str) -> bool:
        return os.path.exists(path)

    def mkdir(self, path: str, exist_ok: bool = True) -> None:
        os.makedirs(path, exist_ok=exist_ok)

    def move(self, src: str, dst: str) -> None:
        self._ensure_parent(dst)
        shutil.move(src, dst)

    def copy(self, src: str, dst: str) -> None:
        self._ensure_parent(dst)
        shutil.copy2(src, dst)

    def _ensure_parent(self, path: str) -> None:
        parent = Path(path).parent
        if parent == Path("."):
            return
        os.makedirs(parent, exist_ok=True)
