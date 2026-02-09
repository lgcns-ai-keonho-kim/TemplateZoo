"""
목적: UI Chat 라우터 공통 유틸을 제공한다.
설명: 도메인 예외를 HTTP 예외로 변환하는 헬퍼를 제공한다.
디자인 패턴: 유틸리티 모듈
참조: src/base_template/api/ui/routers/router.py
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
    return HTTPException(status_code=status_code, detail=error.to_dict())

