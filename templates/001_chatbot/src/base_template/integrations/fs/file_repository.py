"""
목적: 파일 기반 로그 저장소를 제공한다.
설명: 파일 시스템 엔진을 통해 날짜-UUID.log 파일로 로그를 저장한다.
디자인 패턴: 저장소 패턴
참조: src/base_template/integrations/fs/base/engine.py, src/base_template/integrations/fs/engines/local.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel

from base_template.integrations.fs.base.engine import BaseFSEngine
from base_template.integrations.fs.engines.local import LocalFSEngine
from base_template.shared.const import SharedConst
from base_template.shared.logging.logger import LogRepository
from base_template.shared.logging.models import LogLevel, LogRecord


class FileLogRepository(LogRepository):
    """파일 기반 로그 저장소 구현체."""

    def __init__(
        self,
        base_dir: str,
        encoding: Optional[str] = None,
        engine: Optional[BaseFSEngine] = None,
    ) -> None:
        if not base_dir:
            raise ValueError("base_dir는 비어 있을 수 없습니다.")
        self._base_dir = base_dir
        self._encoding = encoding or SharedConst.DEFAULT_ENCODING
        self._engine = engine or LocalFSEngine()
        self._engine.mkdir(self._base_dir, exist_ok=True)

    @property
    def base_dir(self) -> str:
        """로그 디렉터리 경로를 반환한다."""

        return self._base_dir

    def add(self, record: LogRecord) -> None:
        payload = self._to_payload(record)
        content = json.dumps(payload, ensure_ascii=True)
        path = self._create_log_path()
        self._engine.write_text(path, content, self._encoding)

    def list(self) -> List[LogRecord]:
        candidates = self._engine.list_files(
            self._base_dir, recursive=True, suffix=".log"
        )
        collected: List[Tuple[datetime, LogRecord]] = []
        for path in candidates:
            record = self._read_record(path)
            if record is None:
                continue
            collected.append((record.timestamp, record))
        collected.sort(key=lambda item: item[0])
        return [record for _, record in collected]

    def _create_log_path(self) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        date_dir = Path(self._base_dir) / date_str
        self._engine.mkdir(str(date_dir), exist_ok=True)
        name = f"{uuid4()}.log"
        return str(date_dir / name)

    def _read_record(self, path: str) -> Optional[LogRecord]:
        try:
            raw = self._engine.read_text(path, self._encoding)
            payload = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            return self._fallback_record(path, "디코딩 실패")
        try:
            return LogRecord.model_validate(payload)
        except Exception:  # noqa: BLE001 - 손상된 레코드 방어
            return self._fallback_record(path, "유효성 검사 실패")

    def _to_payload(self, record: LogRecord) -> dict:
        if isinstance(record, BaseModel):
            return record.model_dump(mode="json")
        return {
            "level": str(record.level),
            "message": record.message,
            "timestamp": record.timestamp,
            "logger_name": record.logger_name,
            "context": record.context,
            "metadata": record.metadata,
        }

    def _fallback_record(self, path: str, reason: str) -> Optional[LogRecord]:
        try:
            modified = datetime.fromtimestamp(Path(path).stat().st_mtime, tz=timezone.utc)
        except OSError:
            return None
        return LogRecord(
            level=LogLevel.WARNING,
            message="손상된 로그 파일이 감지되었습니다.",
            timestamp=modified,
            logger_name="FileLogRepository",
            context=None,
            metadata={"path": path, "reason": reason},
        )
