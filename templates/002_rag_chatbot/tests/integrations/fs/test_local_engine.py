"""
목적: 로컬 파일 시스템 엔진 동작을 검증한다.
설명: 파일 쓰기/읽기/이동/복사 기능을 테스트한다.
디자인 패턴: 어댑터 패턴 테스트
참조: src/chatbot/integrations/fs/engines/local.py
"""

from __future__ import annotations

from chatbot.integrations.fs.engines import LocalFSEngine


def test_local_engine_write_read_move_copy(tmp_path):
    """로컬 파일 엔진의 기본 동작을 검증한다."""

    engine = LocalFSEngine()
    source = tmp_path / "source.txt"
    target = tmp_path / "moved" / "target.txt"
    copied = tmp_path / "copied" / "copy.txt"

    engine.write_text(str(source), "hello", encoding="utf-8")
    assert engine.read_text(str(source), encoding="utf-8") == "hello"

    engine.move(str(source), str(target))
    assert engine.exists(str(target))

    engine.copy(str(target), str(copied))
    assert engine.exists(str(copied))
    assert engine.read_text(str(copied), encoding="utf-8") == "hello"
