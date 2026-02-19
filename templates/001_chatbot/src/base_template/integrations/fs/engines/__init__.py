"""
목적: 파일 시스템 엔진 구현체 모듈 공개 API를 제공한다.
설명: 로컬 파일 시스템 엔진을 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/integrations/fs/engines/local.py
"""

from base_template.integrations.fs.engines.local import LocalFSEngine

__all__ = ["LocalFSEngine"]
