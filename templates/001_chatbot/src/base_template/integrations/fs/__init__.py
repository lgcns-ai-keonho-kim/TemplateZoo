"""
목적: 파일 시스템 통합 모듈 공개 API를 제공한다.
설명: 파일 시스템 엔진과 파일 로그 저장소를 외부에 노출한다.
디자인 패턴: 퍼사드
참조: src/base_template/integrations/fs/file_repository.py
"""

from base_template.integrations.fs.base import BaseFSEngine
from base_template.integrations.fs.engines import LocalFSEngine
from base_template.integrations.fs.file_repository import FileLogRepository

__all__ = ["BaseFSEngine", "LocalFSEngine", "FileLogRepository"]
