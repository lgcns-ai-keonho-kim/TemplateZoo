"""
목적: 공통 예외 모델을 정의한다.
설명: 에러 코드/원인/힌트/메타데이터를 포함하는 Pydantic 모델을 제공한다.
디자인 패턴: 데이터 전송 객체(DTO)
참조: src/base_template/shared/exceptions/base.py
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ExceptionDetail(BaseModel):
    """예외 상세 정보를 담는 모델이다.

    Args:
        code: 시스템 전반에서 일관되게 사용하는 에러 코드.
        cause: 에러의 직접 원인 설명.
        hint: 해결을 위한 힌트.
        metadata: 추가적인 구조화 메타데이터.
    """

    code: str = Field(..., description="에러 코드")
    cause: Optional[str] = Field(default=None, description="에러 원인")
    hint: Optional[str] = Field(default=None, description="해결 힌트")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")
