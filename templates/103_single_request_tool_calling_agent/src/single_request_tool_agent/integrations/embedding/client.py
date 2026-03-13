"""
목적: LangChain Embeddings 기반 임베딩 클라이언트를 제공한다.
설명: 임베딩 호출을 래핑해 로깅과 예외 처리를 통합한다.
디자인 패턴: 프록시, 데코레이터
참조: src/single_request_tool_agent/shared/logging, src/single_request_tool_agent/shared/exceptions
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeAlias

from langchain_core.embeddings import Embeddings

from single_request_tool_agent.integrations.embedding._client_mixin import (
    _EmbeddingClientMixin,
)
from single_request_tool_agent.shared.exceptions import (
    BaseAppException,
    ExceptionDetail,
)
from single_request_tool_agent.shared.logging import (
    InMemoryLogger,
    LogContext,
    LogRepository,
    Logger,
    create_default_logger,
)

if TYPE_CHECKING:
    from single_request_tool_agent.integrations.db import DBClient
    from single_request_tool_agent.integrations.db.base import (
        BaseDBEngine,
        CollectionSchema,
    )

    LoggingEngine: TypeAlias = BaseDBEngine | LogRepository | Logger
else:
    LoggingEngine: TypeAlias = object


class EmbeddingClient(_EmbeddingClientMixin, Embeddings):
    """로깅/예외 처리를 포함한 임베딩 클라이언트 래퍼이다."""

    def __init__(
        self,
        model: Embeddings,
        name: str = "embedding-client",
        logger: Logger | None = None,
        log_repository: LogRepository | None = None,
        log_collection: str = "embedding_logs",
        log_schema: "CollectionSchema | None" = None,
        auto_create_collection: bool = True,
        log_payload: bool = False,
        log_response: bool = False,
        context_provider: Callable[[], LogContext] | None = None,
        logging_engine: LoggingEngine | None = None,
        background_runner: Callable[..., None] | None = None,
    ) -> None:
        self._model = model
        self._name = str(name or "embedding-client").strip() or "embedding-client"
        self._log_payload = bool(log_payload)
        self._log_response = bool(log_response)
        self._context_provider = context_provider
        self._background_runner = background_runner

        db_client: "DBClient | None" = None
        if logging_engine is not None:
            logger, log_repository, db_client = self._resolve_logging(
                logging_engine,
                logger,
                log_repository,
            )

        if log_repository is None and db_client is not None:
            log_repository = self._build_embedding_repository(
                db_client=db_client,
                collection=log_collection,
                schema=log_schema,
                auto_create=auto_create_collection,
                auto_connect=True,
            )

        self._logger = self._build_logger(self._name, logger, log_repository)

    def embed_query(self, text: str) -> list[float]:
        """단일 텍스트 임베딩을 생성한다."""

        vectors = self._embed_sync(
            action="embed_query",
            texts=[str(text or "")],
            invoke=self._model.embed_query,
            single_input=True,
        )
        return vectors[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """복수 텍스트 임베딩을 생성한다."""

        vectors = self._embed_sync(
            action="embed_documents",
            texts=[str(item or "") for item in list(texts or [])],
            invoke=self._model.embed_documents,
            single_input=False,
        )
        return vectors

    async def aembed_query(self, text: str) -> list[float]:
        """비동기 단일 텍스트 임베딩을 생성한다."""

        vectors = await self._embed_async(
            action="aembed_query",
            texts=[str(text or "")],
            invoke=self._model.aembed_query,
            single_input=True,
        )
        return vectors[0]

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """비동기 복수 텍스트 임베딩을 생성한다."""

        vectors = await self._embed_async(
            action="aembed_documents",
            texts=[str(item or "") for item in list(texts or [])],
            invoke=self._model.aembed_documents,
            single_input=False,
        )
        return vectors

    def _embed_sync(
        self,
        *,
        action: str,
        texts: list[str],
        invoke: Callable[[Any], Any],
        single_input: bool,
    ) -> list[list[float]]:
        input_count, input_chars = self._input_stats(texts)
        self._log_start(
            action=action,
            input_count=input_count,
            input_chars=input_chars,
            payload=texts if self._log_payload else None,
        )
        start = time.monotonic()
        try:
            payload = texts[0] if single_input else texts
            raw = invoke(payload)
            vectors = self._normalize_output(
                raw,
                expected_count=input_count,
                single_input=single_input,
            )
        except BaseAppException as error:
            self._log_error(
                action,
                error,
                start,
                input_count=input_count,
                input_chars=input_chars,
            )
            raise
        except Exception as error:  # noqa: BLE001
            self._log_error(
                action,
                error,
                start,
                input_count=input_count,
                input_chars=input_chars,
            )
            raise self._build_call_error(action, error) from error

        self._log_success(
            action,
            start,
            input_count=input_count,
            input_chars=input_chars,
            output_count=len(vectors),
            dimension=len(vectors[0]) if vectors else 0,
            response=vectors if self._log_response else None,
        )
        return vectors

    async def _embed_async(
        self,
        *,
        action: str,
        texts: list[str],
        invoke: Callable[[Any], Any],
        single_input: bool,
    ) -> list[list[float]]:
        input_count, input_chars = self._input_stats(texts)
        self._log_start(
            action=action,
            input_count=input_count,
            input_chars=input_chars,
            payload=texts if self._log_payload else None,
        )
        start = time.monotonic()
        try:
            payload = texts[0] if single_input else texts
            raw = await invoke(payload)
            vectors = self._normalize_output(
                raw,
                expected_count=input_count,
                single_input=single_input,
            )
        except BaseAppException as error:
            self._log_error(
                action,
                error,
                start,
                input_count=input_count,
                input_chars=input_chars,
            )
            raise
        except Exception as error:  # noqa: BLE001
            self._log_error(
                action,
                error,
                start,
                input_count=input_count,
                input_chars=input_chars,
            )
            raise self._build_call_error(action, error) from error

        self._log_success(
            action,
            start,
            input_count=input_count,
            input_chars=input_chars,
            output_count=len(vectors),
            dimension=len(vectors[0]) if vectors else 0,
            response=vectors if self._log_response else None,
        )
        return vectors

    def _input_stats(self, texts: list[str]) -> tuple[int, int]:
        return len(texts), sum(len(item) for item in texts)

    def _normalize_output(
        self,
        raw: Any,
        *,
        expected_count: int,
        single_input: bool,
    ) -> list[list[float]]:
        if expected_count <= 0:
            if raw not in (None, []):
                detail = ExceptionDetail(
                    code="EMBEDDING_DOCUMENT_COUNT_MISMATCH",
                    cause=f"expected=0, actual_output={type(raw).__name__}",
                )
                raise BaseAppException(
                    "문서 임베딩 결과 개수가 입력 개수와 다릅니다.", detail
                )
            return []

        if single_input:
            return [self._coerce_vector(raw, index=0)]

        raw_vectors = list(raw or [])
        vectors = [
            self._coerce_vector(vector, index=index)
            for index, vector in enumerate(raw_vectors)
        ]
        self._validate_document_vectors(expected_count=expected_count, vectors=vectors)
        return vectors

    def _validate_document_vectors(
        self,
        *,
        expected_count: int,
        vectors: list[list[float]],
    ) -> None:
        if expected_count != len(vectors):
            detail = ExceptionDetail(
                code="EMBEDDING_DOCUMENT_COUNT_MISMATCH",
                cause=f"expected={expected_count}, actual={len(vectors)}",
            )
            raise BaseAppException(
                "문서 임베딩 결과 개수가 입력 개수와 다릅니다.", detail
            )

        if not vectors:
            return

        base_dim = len(vectors[0])
        for index, vector in enumerate(vectors, start=1):
            if len(vector) != base_dim:
                detail = ExceptionDetail(
                    code="EMBEDDING_DIMENSION_INCONSISTENT",
                    cause=f"base_dim={base_dim}, index={index}, dim={len(vector)}",
                )
                raise BaseAppException("문서 임베딩 차원이 일관되지 않습니다.", detail)

    def _coerce_vector(self, value: Any, *, index: int) -> list[float]:
        try:
            normalized = [float(item) for item in list(value or [])]
        except (TypeError, ValueError):
            detail = ExceptionDetail(
                code="EMBEDDING_VECTOR_INVALID",
                cause=f"index={index}",
            )
            raise BaseAppException(
                "임베딩 벡터 형식이 올바르지 않습니다.", detail
            ) from None

        if not normalized:
            detail = ExceptionDetail(
                code="EMBEDDING_VECTOR_EMPTY",
                cause=f"index={index}",
            )
            raise BaseAppException("임베딩 벡터가 비어 있습니다.", detail)

        return normalized

    def _build_call_error(self, action: str, error: Exception) -> BaseAppException:
        code_map = {
            "embed_query": "EMBED_QUERY_ERROR",
            "embed_documents": "EMBED_DOCUMENTS_ERROR",
            "aembed_query": "EMBED_AQUERY_ERROR",
            "aembed_documents": "EMBED_ADOCUMENTS_ERROR",
        }
        message_map = {
            "embed_query": "임베딩 질의 생성에 실패했습니다.",
            "embed_documents": "문서 임베딩 생성에 실패했습니다.",
            "aembed_query": "비동기 임베딩 질의 생성에 실패했습니다.",
            "aembed_documents": "비동기 문서 임베딩 생성에 실패했습니다.",
        }
        detail = ExceptionDetail(
            code=code_map.get(action, "EMBEDDING_CALL_ERROR"),
            cause=str(error),
        )
        return BaseAppException(
            message_map.get(action, "임베딩 호출에 실패했습니다."), detail, error
        )

    def _build_logger(
        self,
        name: str,
        logger: Logger | None,
        repository: LogRepository | None,
    ) -> Logger:
        if logger is not None:
            return logger
        if repository is not None:
            return InMemoryLogger(name=name, repository=repository)
        return create_default_logger(name)

    def _resolve_logging(
        self,
        logging_target: object,
        logger: Logger | None,
        log_repository: LogRepository | None,
    ) -> tuple[Logger | None, LogRepository | None, "DBClient | None"]:
        from single_request_tool_agent.integrations.db import DBClient as _DBClient
        from single_request_tool_agent.integrations.db.base import (
            BaseDBEngine as _BaseDBEngine,
        )

        if isinstance(logging_target, Logger):
            return logging_target, log_repository, None
        if isinstance(logging_target, LogRepository):
            return logger, logging_target, None

        if isinstance(logging_target, _BaseDBEngine):
            return logger, log_repository, _DBClient(logging_target)

        if isinstance(logging_target, _DBClient):
            raise ValueError(
                "logging에는 DBClient가 아니라 BaseDBEngine을 주입해야 합니다."
            )

        raise ValueError(
            "logging_engine에는 BaseDBEngine, Logger, LogRepository만 허용됩니다."
        )

    def _build_embedding_repository(
        self,
        *,
        db_client: "DBClient",
        collection: str,
        schema: "CollectionSchema | None",
        auto_create: bool,
        auto_connect: bool,
    ) -> LogRepository:
        from single_request_tool_agent.shared.logging.embedding_repository import (
            EmbeddingLogRepository,
        )

        return EmbeddingLogRepository(
            client=db_client,
            collection=collection,
            schema=schema,
            auto_create=auto_create,
            auto_connect=auto_connect,
        )

    def _base_metadata(self, action: str) -> dict[str, Any]:
        provider = type(self._model).__name__
        model_name = str(getattr(self._model, "model", "") or self._name)
        return {
            "action": action,
            "model_name": model_name,
            "provider": provider,
            "client_name": self._name,
        }


__all__ = ["EmbeddingClient"]
