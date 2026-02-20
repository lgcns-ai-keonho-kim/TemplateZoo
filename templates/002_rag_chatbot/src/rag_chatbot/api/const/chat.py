"""
목적: Chat API 라우팅 상수를 정의한다.
설명: Chat/UI 라우터 prefix, tag, 경로 상수를 중앙에서 관리한다.
디자인 패턴: 상수 객체 패턴
참조: src/rag_chatbot/api/chat/routers/router.py, src/rag_chatbot/api/ui/routers/router.py
"""

from __future__ import annotations

# Chat API(백엔드 실행 경로) 공통 상수
CHAT_API_PREFIX = "/chat"
CHAT_API_TAG = "chat"
CHAT_API_CREATE_PATH = ""
CHAT_API_EVENTS_PATH = "/{session_id}/events"
CHAT_API_SESSION_SNAPSHOT_PATH = "/{session_id}"

# UI API(프론트 조회/관리 경로) 공통 상수
UI_CHAT_API_PREFIX = "/ui-api/chat"
UI_CHAT_API_TAG = "ui-chat"
UI_CHAT_SESSIONS_PATH = "/sessions"
UI_CHAT_SESSION_MESSAGES_PATH = "/sessions/{session_id}/messages"
UI_CHAT_SESSION_PATH = "/sessions/{session_id}"

