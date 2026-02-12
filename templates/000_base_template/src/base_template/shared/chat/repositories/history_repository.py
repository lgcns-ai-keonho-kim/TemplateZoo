"""
목적: Chat 대화 이력 저장소를 제공한다.
설명: DBClient 기반으로 세션/메시지 저장, 조회, 삭제를 수행하며, db_client 미주입 시 SQLite를 기본으로 사용한다.
디자인 패턴: 저장소 패턴
참조: src/base_template/integrations/db/client.py, src/base_template/shared/chat/repositories/schemas
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from base_template.core.chat.const import (
    CHAT_DB_PATH,
    CHAT_MESSAGE_COLLECTION,
    CHAT_REQUEST_COMMIT_COLLECTION,
    CHAT_SESSION_COLLECTION,
)
from base_template.core.chat.models import ChatMessage, ChatRole, ChatSession, utc_now
from base_template.core.chat.utils import ChatHistoryMapper
from base_template.integrations.db import DBClient
from base_template.integrations.db.base import (
    FieldSource,
    FilterCondition,
    FilterExpression,
    FilterOperator,
    Pagination,
    Query,
    SortField,
    SortOrder,
)
from base_template.integrations.db.engines.sqlite import SQLiteEngine
from base_template.shared.chat.repositories.schemas import (
    build_chat_message_schema,
    build_chat_request_commit_schema,
    build_chat_session_schema,
)
from base_template.shared.exceptions import BaseAppException, ExceptionDetail
from base_template.shared.logging import Logger, create_default_logger


class ChatHistoryRepository:
    """대화 이력 저장소 구현체."""

    def __init__(
        self,
        db_client: Optional[DBClient] = None,
        database_path: str = str(CHAT_DB_PATH),
        logger: Optional[Logger] = None,
    ) -> None:
        # 참고:
        # - db_client를 주입하면 호출자가 선택한 엔진(PostgreSQL 등)으로 동작한다.
        # - db_client를 주입하지 않으면 기본 SQLiteEngine(database_path)로 동작한다.
        self._logger = logger or create_default_logger("ChatHistoryRepository")
        self._database_path = Path(database_path)
        self._mapper = ChatHistoryMapper()
        self._session_schema = build_chat_session_schema()
        self._message_schema = build_chat_message_schema()
        self._request_commit_schema = build_chat_request_commit_schema()

        self._owns_client = db_client is None
        if db_client is not None:
            self._client = db_client
        else:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
            engine = SQLiteEngine(
                database_path=str(self._database_path),
                logger=self._logger,
                enable_vector=False,
            )
            self._client = DBClient(engine)
        self._initialize()

    def close(self) -> None:
        """내부 DB 연결을 종료한다."""

        if not self._owns_client:
            return
        self._client.close()

    def create_session(
        self,
        session_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> ChatSession:
        """새 세션을 생성한다.

        session_id가 이미 존재하면 기존 세션을 반환한다.
        """

        try:
            if session_id:
                existing = self.get_session(session_id)
                if existing is not None:
                    if title and title.strip() and title.strip() != existing.title:
                        existing.title = title.strip()
                        existing.updated_at = utc_now()
                        self._upsert_session(existing)
                    return existing

            now = utc_now()
            session = ChatSession(
                session_id=session_id or str(uuid4()),
                title=(title or "새 대화").strip() or "새 대화",
                created_at=now,
                updated_at=now,
                message_count=0,
                last_message_preview=None,
            )
            self._upsert_session(session)
            return session
        except Exception as error:  # noqa: BLE001
            self._raise_repository_error("CHAT_SESSION_CREATE_ERROR", error)

    def ensure_session(
        self,
        session_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> ChatSession:
        """세션 식별자 기준으로 세션을 보장한다."""

        if not session_id:
            return self.create_session(title=title)
        existing = self.get_session(session_id)
        if existing is None:
            return self.create_session(session_id=session_id, title=title)
        if title and title.strip() and title.strip() != existing.title:
            existing.title = title.strip()
            existing.updated_at = utc_now()
            self._upsert_session(existing)
        return existing

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """세션 1건을 조회한다."""

        try:
            query = Query(
                filter_expression=self._build_session_filter(session_id),
                pagination=Pagination(limit=1, offset=0),
            )
            documents = self._client.fetch(CHAT_SESSION_COLLECTION, query)
            if not documents:
                return None
            return self._mapper.session_from_document(documents[0])
        except Exception as error:  # noqa: BLE001
            self._raise_repository_error("CHAT_SESSION_GET_ERROR", error)

    def list_sessions(self, limit: int, offset: int) -> list[ChatSession]:
        """최근 갱신 순으로 세션 목록을 조회한다."""

        try:
            query = Query(
                sort=[
                    SortField(
                        field="updated_at",
                        source=FieldSource.COLUMN,
                        order=SortOrder.DESC,
                    )
                ],
                pagination=Pagination(limit=limit, offset=offset),
            )
            documents = self._client.fetch(CHAT_SESSION_COLLECTION, query)
            return [self._mapper.session_from_document(document) for document in documents]
        except Exception as error:  # noqa: BLE001
            self._raise_repository_error("CHAT_SESSION_LIST_ERROR", error)

    def append_message(
        self,
        session_id: str,
        role: ChatRole,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ChatMessage:
        """메시지를 저장하고 세션 요약 정보를 갱신한다."""

        if not content or not content.strip():
            detail = ExceptionDetail(code="CHAT_MESSAGE_EMPTY", cause="content is empty")
            raise BaseAppException("메시지 본문은 비어 있을 수 없습니다.", detail)

        try:
            session = self.ensure_session(session_id=session_id)
            next_sequence = session.message_count + 1
            message = ChatMessage(
                message_id=str(uuid4()),
                session_id=session.session_id,
                role=role,
                content=content,
                sequence=next_sequence,
                created_at=utc_now(),
                metadata=metadata or {},
            )
            self._client.upsert(
                CHAT_MESSAGE_COLLECTION,
                [self._mapper.message_to_document(message)],
            )
            session.message_count = next_sequence
            session.updated_at = message.created_at
            session.last_message_preview = self._mapper.preview(message.content)
            self._upsert_session(session)
            return message
        except BaseAppException:
            raise
        except Exception as error:  # noqa: BLE001
            self._raise_repository_error("CHAT_MESSAGE_APPEND_ERROR", error)

    def is_request_committed(self, request_id: str) -> bool:
        """요청 식별자의 저장 커밋 여부를 반환한다."""

        candidate = str(request_id or "").strip()
        if not candidate:
            detail = ExceptionDetail(code="CHAT_REQUEST_ID_EMPTY", cause="request_id is empty")
            raise BaseAppException("request_id는 비어 있을 수 없습니다.", detail)

        try:
            query = Query(
                filter_expression=FilterExpression(
                    conditions=[
                        FilterCondition(
                            field="request_id",
                            source=FieldSource.COLUMN,
                            operator=FilterOperator.EQ,
                            value=candidate,
                        )
                    ]
                ),
                pagination=Pagination(limit=1, offset=0),
            )
            documents = self._client.fetch(CHAT_REQUEST_COMMIT_COLLECTION, query)
            return bool(documents)
        except BaseAppException:
            raise
        except Exception as error:  # noqa: BLE001
            self._raise_repository_error("CHAT_REQUEST_COMMIT_GET_ERROR", error)

    def mark_request_committed(
        self,
        request_id: str,
        session_id: str,
        message_id: str,
    ) -> None:
        """요청 식별자의 저장 완료를 기록한다."""

        candidate = str(request_id or "").strip()
        if not candidate:
            detail = ExceptionDetail(code="CHAT_REQUEST_ID_EMPTY", cause="request_id is empty")
            raise BaseAppException("request_id는 비어 있을 수 없습니다.", detail)

        try:
            self._client.upsert(
                CHAT_REQUEST_COMMIT_COLLECTION,
                [
                    self._mapper.request_commit_to_document(
                        request_id=candidate,
                        session_id=session_id,
                        message_id=message_id,
                    )
                ],
            )
        except BaseAppException:
            raise
        except Exception as error:  # noqa: BLE001
            self._raise_repository_error("CHAT_REQUEST_COMMIT_UPSERT_ERROR", error)

    def list_messages(self, session_id: str, limit: int, offset: int) -> list[ChatMessage]:
        """세션별 메시지 목록을 순번 오름차순으로 조회한다."""

        try:
            query = Query(
                filter_expression=self._build_session_filter(session_id),
                sort=[
                    SortField(
                        field="sequence",
                        source=FieldSource.COLUMN,
                        order=SortOrder.ASC,
                    )
                ],
                pagination=Pagination(limit=limit, offset=offset),
            )
            documents = self._client.fetch(CHAT_MESSAGE_COLLECTION, query)
            return [self._mapper.message_from_document(document) for document in documents]
        except Exception as error:  # noqa: BLE001
            self._raise_repository_error("CHAT_MESSAGE_LIST_ERROR", error)

    def get_recent_messages(self, session_id: str, limit: int) -> list[ChatMessage]:
        """최근 메시지 n개를 조회한 뒤 순서를 복원한다."""

        try:
            query = Query(
                filter_expression=self._build_session_filter(session_id),
                sort=[
                    SortField(
                        field="sequence",
                        source=FieldSource.COLUMN,
                        order=SortOrder.DESC,
                    )
                ],
                pagination=Pagination(limit=limit, offset=0),
            )
            documents = self._client.fetch(CHAT_MESSAGE_COLLECTION, query)
            recent = [self._mapper.message_from_document(document) for document in documents]
            recent.reverse()
            return recent
        except Exception as error:  # noqa: BLE001
            self._raise_repository_error("CHAT_MESSAGE_RECENT_ERROR", error)

    def delete_session(self, session_id: str) -> tuple[bool, int]:
        """세션과 해당 세션의 메시지를 함께 삭제한다."""

        try:
            existing = self.get_session(session_id)
            if existing is None:
                return False, 0
            deleted_message_count = self._client.delete(CHAT_MESSAGE_COLLECTION).where_column(
                "session_id"
            ).eq(session_id).execute()
            self._client.delete(CHAT_SESSION_COLLECTION).by_id(session_id)
            return True, deleted_message_count
        except Exception as error:  # noqa: BLE001
            self._raise_repository_error("CHAT_SESSION_DELETE_ERROR", error)

    def _initialize(self) -> None:
        self._client.connect()
        self._client.create_collection(self._session_schema)
        self._client.create_collection(self._message_schema)
        self._client.create_collection(self._request_commit_schema)
        self._logger.info(f"Chat 저장소 초기화 완료: {self._database_path}")

    def _upsert_session(self, session: ChatSession) -> None:
        self._client.upsert(
            CHAT_SESSION_COLLECTION,
            [self._mapper.session_to_document(session)],
        )

    def _build_session_filter(self, session_id: str) -> FilterExpression:
        return FilterExpression(
            conditions=[
                FilterCondition(
                    field="session_id",
                    source=FieldSource.COLUMN,
                    operator=FilterOperator.EQ,
                    value=session_id,
                )
            ]
        )

    def _raise_repository_error(self, code: str, error: Exception) -> None:
        detail = ExceptionDetail(code=code, cause=str(error))
        raise BaseAppException("대화 이력 저장소 처리 중 오류가 발생했습니다.", detail, error) from error
