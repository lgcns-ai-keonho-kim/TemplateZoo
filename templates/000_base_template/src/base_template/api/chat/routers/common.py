"""
목적: Chat 라우터 공통 유틸을 제공한다.
설명: 도메인 예외를 HTTP 예외로 변환하는 헬퍼를 제공한다.
디자인 패턴: 유틸리티 모듈
참조: src/base_template/api/chat/routers/router.py
"""

from __future__ import annotations

from fastapi import HTTPException, status

from base_template.shared.exceptions import BaseAppException


def to_http_exception(error: BaseAppException) -> HTTPException:
    """도메인 예외를 HTTP 예외로 변환한다."""

    code = error.detail.code
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if code in {"CHAT_SESSION_NOT_FOUND"}:
        status_code = status.HTTP_404_NOT_FOUND
    if code in {"CHAT_MESSAGE_EMPTY", "CHAT_STREAM_NODE_INVALID"}:
        status_code = status.HTTP_400_BAD_REQUEST
    if code in {"CHAT_STREAM_TIMEOUT"}:
        status_code = status.HTTP_504_GATEWAY_TIMEOUT
    return HTTPException(status_code=status_code, detail=error.to_dict())
