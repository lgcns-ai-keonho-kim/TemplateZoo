"""
목적: Chat 코어의 설정 상수를 정의한다.
설명: SQLite 저장 경로, 컬렉션 명, 기본 페이지네이션 값을 제공한다.
디자인 패턴: 상수 객체 패턴
참조: src/base_template/core/repositories/chat/history_repository.py
"""

from __future__ import annotations

import os
from pathlib import Path

CHAT_DB_PATH = Path(
    os.getenv("CHAT_DB_PATH", "data/db/chat/chat_history.sqlite")
)
CHAT_SESSION_COLLECTION = "chat_sessions"
CHAT_MESSAGE_COLLECTION = "chat_messages"

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
DEFAULT_CONTEXT_WINDOW = 20
