"""
목적: Chat 코어의 설정 상수를 정의한다.
설명: SQLite 저장 경로, 컬렉션 명(세션/메시지/요청커밋), 기본 페이지네이션 값을 제공한다.
디자인 패턴: 상수 객체 패턴
참조: src/base_template/shared/chat/repositories/history_repository.py
"""

from __future__ import annotations

import os
from pathlib import Path

CHAT_DB_PATH = Path(
    os.getenv("CHAT_DB_PATH", "data/db/chat/chat_history.sqlite")
)
# DBClient/SQLiteEngine에서 세션 메타데이터를 저장하는 컬렉션 이름
CHAT_SESSION_COLLECTION = "chat_sessions"
# DBClient/SQLiteEngine에서 메시지 본문을 저장하는 컬렉션 이름
CHAT_MESSAGE_COLLECTION = "chat_messages"
# 요청 단위 저장 멱등성(request_id)을 기록하는 컬렉션 이름
CHAT_REQUEST_COMMIT_COLLECTION = "chat_request_commits"

# 목록 조회 API의 기본 페이지 크기
DEFAULT_PAGE_SIZE = 50
# 목록 조회 API에서 허용하는 최대 페이지 크기
MAX_PAGE_SIZE = 200
# LLM 응답 생성 시 참고하는 기본 대화 컨텍스트 길이(최근 메시지 개수)
DEFAULT_CONTEXT_WINDOW = 20
