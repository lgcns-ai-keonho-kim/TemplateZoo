"""
목적: 파일 로그 저장소 동작을 검증한다.
설명: 로그 저장, 정렬, 손상 파일 방어 로직을 테스트한다.
디자인 패턴: 저장소 패턴 테스트
참조: src/rag_chatbot/integrations/fs/file_repository.py
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from rag_chatbot.integrations.fs import FileLogRepository, LocalFSEngine
from rag_chatbot.shared.logging import LogLevel, LogRecord


def test_file_repository_sorting(tmp_path):
    """로그가 타임스탬프 기준으로 정렬되는지 확인한다."""

    engine = LocalFSEngine()
    repository = FileLogRepository(base_dir=str(tmp_path), engine=engine)

    earlier = datetime.now(timezone.utc) - timedelta(minutes=1)
    later = datetime.now(timezone.utc)

    repository.add(
        LogRecord(
            level=LogLevel.INFO,
            message="later",
            timestamp=later,
            logger_name="test",
            context=None,
            metadata={},
        )
    )
    repository.add(
        LogRecord(
            level=LogLevel.INFO,
            message="earlier",
            timestamp=earlier,
            logger_name="test",
            context=None,
            metadata={},
        )
    )

    records = repository.list()
    assert [record.message for record in records] == ["earlier", "later"]


def test_file_repository_fallback_on_corrupt_file(tmp_path):
    """손상된 로그 파일이 경고 레코드로 복구되는지 확인한다."""

    engine = LocalFSEngine()
    repository = FileLogRepository(base_dir=str(tmp_path), engine=engine)

    repository.add(
        LogRecord(
            level=LogLevel.INFO,
            message="valid",
            timestamp=datetime.now(timezone.utc),
            logger_name="test",
            context=None,
            metadata={},
        )
    )

    date_dir = datetime.now(timezone.utc).strftime("%Y%m%d")
    corrupt_path = tmp_path / date_dir / "corrupt.log"
    engine.write_text(str(corrupt_path), "{invalid-json", encoding="utf-8")

    records = repository.list()
    assert any(record.level == LogLevel.WARNING for record in records)
    assert any(
        record.metadata.get("reason") in {"디코딩 실패", "유효성 검사 실패"}
        for record in records
    )
