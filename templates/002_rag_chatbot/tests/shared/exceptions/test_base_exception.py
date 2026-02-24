"""
목적: 공통 예외 모델과 베이스 예외 동작을 검증한다.
설명: 예외 메시지/상세 모델/원본 예외 저장 및 직렬화 결과를 확인한다.
디자인 패턴: 도메인 예외 객체, DTO
참조: src/rag_chatbot/shared/exceptions/base.py, src/rag_chatbot/shared/exceptions/models.py
"""

from __future__ import annotations

from rag_chatbot.shared.exceptions import BaseAppException, ExceptionDetail


def test_base_app_exception_to_dict() -> None:
    """BaseAppException의 직렬화 결과를 검증한다."""

    detail = ExceptionDetail(
        code="E-001",
        cause="입력 데이터 누락",
        hint="필수 파라미터를 확인하세요.",
        metadata={"field": "name"},
    )
    original = ValueError("name is required")
    error = BaseAppException(message="유효하지 않은 요청입니다.", detail=detail, original=original)

    result = error.to_dict()

    assert error.message == "유효하지 않은 요청입니다."
    assert error.detail.code == "E-001"
    assert error.original is original
    assert result["message"] == "유효하지 않은 요청입니다."
    assert result["detail"]["metadata"]["field"] == "name"
    assert "ValueError" in result["original"]
