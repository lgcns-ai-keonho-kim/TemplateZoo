"""
목적: 예외 모듈 공개 API를 제공한다.
설명: 외부에서 사용할 예외 모델과 베이스 클래스를 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/shared/exceptions/models.py, src/base_template/shared/exceptions/base.py
"""

from base_template.shared.exceptions.base import BaseAppException
from base_template.shared.exceptions.models import ExceptionDetail

__all__ = ["BaseAppException", "ExceptionDetail"]
