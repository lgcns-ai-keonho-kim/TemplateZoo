"""
목적: 공통 상수 집합을 제공한다.
설명: 프로젝트 전역에서 사용하는 기본 상수 값을 정의한다.
디자인 패턴: 상수 객체
참조: src/base_template/shared/config/loader.py
"""


class SharedConst:
    """공통 상수 집합이다.

    Attributes:
        DEFAULT_ENCODING: 기본 파일 인코딩.
        DEFAULT_TIMEZONE: 기본 타임존 이름.
        ENV_NESTED_DELIMITER: 환경 변수 키를 중첩 경로로 해석하는 구분자.
    """

    DEFAULT_ENCODING = "utf-8"
    DEFAULT_TIMEZONE = "UTC"
    ENV_NESTED_DELIMITER = "__"


__all__ = ["SharedConst"]
