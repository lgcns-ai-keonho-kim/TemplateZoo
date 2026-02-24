"""
목적: LangChain BaseChatModel 기반 LLM 클라이언트를 제공한다.
설명: 기존 메서드(invoke/ainvoke/stream/astream)를 유지하면서 로깅과 예외 처리를 통합한다.
디자인 패턴: 프록시, 데코레이터
참조: src/chatbot/shared/logging, src/chatbot/shared/exceptions
"""

from __future__ import annotations

import threading
import time
from typing import Any, AsyncIterator, Callable, Iterator, Optional, Sequence, TYPE_CHECKING, TypeAlias

from pydantic import ConfigDict, PrivateAttr

from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, BaseMessageChunk
from langchain_core.outputs import ChatGenerationChunk, ChatResult

from chatbot.shared.exceptions import BaseAppException, ExceptionDetail
from chatbot.shared.logging import (
    InMemoryLogger,
    LogContext,
    LogLevel,
    LogRepository,
    Logger,
    create_default_logger,
)

if TYPE_CHECKING:
    from chatbot.integrations.db import DBClient
    from chatbot.integrations.db.base import BaseDBEngine, CollectionSchema

    LoggingEngine: TypeAlias = BaseDBEngine | LogRepository | Logger
else:
    LoggingEngine: TypeAlias = object


class LLMClient(BaseChatModel):
    """로깅/예외 처리를 포함한 LLM 클라이언트 래퍼이다."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    _model: BaseChatModel = PrivateAttr()
    _logger: Logger = PrivateAttr()
    _name: str = PrivateAttr()
    _log_payload: bool = PrivateAttr(default=False)
    _log_response: bool = PrivateAttr(default=False)
    _log_repository: Optional[LogRepository] = PrivateAttr(default=None)
    _context_provider: Optional[Callable[[], LogContext]] = PrivateAttr(default=None)
    _background_runner: Optional[Callable[..., None]] = PrivateAttr(default=None)

    def __init__(
        self,
        model: BaseChatModel,
        name: str = "llm-client",
        logger: Optional[Logger] = None,
        log_repository: Optional[LogRepository] = None,
        log_collection: str = "llm_logs",
        log_schema: Optional["CollectionSchema"] = None,
        auto_create_collection: bool = True,
        log_payload: bool = False,
        log_response: bool = False,
        context_provider: Optional[Callable[[], LogContext]] = None,
        logging_engine: Optional[LoggingEngine] = None,
        background_runner: Optional[Callable[..., None]] = None,
    ) -> None:
        super().__init__()
        self._model = model
        self._name = name
        self._log_payload = log_payload
        self._log_response = log_response
        self._context_provider = context_provider
        self._background_runner = background_runner
        db_client: Optional["DBClient"] = None
        if logging_engine is not None:
            logger, log_repository, db_client = self._resolve_logging(
                logging_engine, logger, log_repository
            )

        if log_repository is None and db_client is not None:
            log_repository = self._build_llm_repository(
                db_client=db_client,
                collection=log_collection,
                schema=log_schema,
                auto_create=auto_create_collection,
                auto_connect=True,
            )
        self._log_repository = log_repository
        self._logger = self._build_logger(name, logger, log_repository)

    def chat(self, messages: Sequence[BaseMessage], **kwargs: Any) -> BaseMessage:
        """메시지 기반 동기 스트리밍 호출을 수행한다."""

        merged: list[str] = []
        for chunk in self.stream(list(messages), **kwargs):
            message_chunk = self._to_message_chunk(chunk)
            text = self._to_text(message_chunk.content)
            if text:
                merged.append(text)
        content = "".join(merged).strip()
        if not content:
            detail = ExceptionDetail(code="LLM_STREAM_EMPTY", cause="chat stream produced empty content")
            raise BaseAppException("LLM 스트리밍 결과가 비어 있습니다.", detail)
        return AIMessage(content=content)

    @property
    def _llm_type(self) -> str:
        base_type = getattr(self._model, "_llm_type", None)
        if base_type:
            return f"logged-{base_type}"
        return "logged-chat-model"

    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Callable[..., Any] | Any],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """도구 바인딩을 내부 모델에 위임한다."""

        try:
            return self._model.bind_tools(tools, tool_choice=tool_choice, **kwargs)
        except NotImplementedError as error:
            raise NotImplementedError("주입된 모델은 bind_tools를 지원하지 않습니다.") from error

    def with_structured_output(
        self,
        schema: dict[str, Any] | type,
        *,
        include_raw: bool = False,
        **kwargs: Any,
    ) -> Any:
        """구조화 출력 래핑을 내부 모델에 위임한다."""

        try:
            return self._model.with_structured_output(
                schema,
                include_raw=include_raw,
                **kwargs,
            )
        except NotImplementedError as error:
            raise NotImplementedError(
                "주입된 모델은 with_structured_output을 지원하지 않습니다."
            ) from error

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        start = time.monotonic()
        self._log_start("invoke", messages, stop, False, kwargs)
        try:
            result = self._model._generate(
                messages,
                stop=stop,
                run_manager=run_manager,
                **kwargs,
            )
        except Exception as error:  # noqa: BLE001 - 외부 라이브러리 오류 캡처
            self._log_error("invoke", error, start)
            detail = ExceptionDetail(code="LLM_INVOKE_ERROR", cause=str(error))
            raise BaseAppException("LLM 호출에 실패했습니다.", detail, error) from error
        self._log_success("invoke", start, result)
        return result

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        start = time.monotonic()
        self._log_start("ainvoke", messages, stop, False, kwargs)
        try:
            result = await self._model._agenerate(
                messages,
                stop=stop,
                run_manager=run_manager,
                **kwargs,
            )
        except Exception as error:  # noqa: BLE001 - 외부 라이브러리 오류 캡처
            self._log_error("ainvoke", error, start)
            detail = ExceptionDetail(code="LLM_AINVOKE_ERROR", cause=str(error))
            raise BaseAppException("LLM 비동기 호출에 실패했습니다.", detail, error) from error
        self._log_success("ainvoke", start, result)
        return result

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        start = time.monotonic()
        self._log_start("stream", messages, stop, True, kwargs)
        completed = False
        try:
            for chunk in self._iter_stream_chunks(messages, stop, run_manager, kwargs):
                yield self._to_generation_chunk(chunk)
            completed = True
        except BaseAppException as error:
            self._log_error("stream", error, start)
            raise
        except Exception as error:  # noqa: BLE001 - 외부 라이브러리 오류 캡처
            self._log_error("stream", error, start)
            detail = ExceptionDetail(code="LLM_STREAM_ERROR", cause=str(error))
            raise BaseAppException("LLM 스트리밍 호출에 실패했습니다.", detail, error) from error
        finally:
            if completed:
                self._run_background(self._log_success, "stream", start, None)

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        start = time.monotonic()
        self._log_start("astream", messages, stop, True, kwargs)
        completed = False
        try:
            async for chunk in self._aiter_stream_chunks(messages, stop, run_manager, kwargs):
                yield self._to_generation_chunk(chunk)
            completed = True
        except BaseAppException as error:
            self._log_error("astream", error, start)
            raise
        except Exception as error:  # noqa: BLE001 - 외부 라이브러리 오류 캡처
            self._log_error("astream", error, start)
            detail = ExceptionDetail(code="LLM_ASTREAM_ERROR", cause=str(error))
            raise BaseAppException("LLM 비동기 스트리밍 호출에 실패했습니다.", detail, error) from error
        finally:
            if completed:
                self._run_background(self._log_success, "astream", start, None)

    def _build_logger(
        self,
        name: str,
        logger: Optional[Logger],
        repository: Optional[LogRepository],
    ) -> Logger:
        if logger is not None:
            return logger
        if repository is not None:
            return InMemoryLogger(name=name, repository=repository)
        return create_default_logger(name)

    def _resolve_logging(
        self,
        logging_target: object,
        logger: Optional[Logger],
        log_repository: Optional[LogRepository],
    ) -> tuple[Optional[Logger], Optional[LogRepository], Optional["DBClient"]]:
        if isinstance(logging_target, Logger):
            return logging_target, log_repository, None
        if isinstance(logging_target, LogRepository):
            return logger, logging_target, None
        db_client_cls: Any | None = None
        base_db_engine_cls: Any | None = None
        try:
            from chatbot.integrations.db import DBClient as _DBClient
            from chatbot.integrations.db.base import BaseDBEngine as _BaseDBEngine
        except ImportError:
            db_client_cls = None
            base_db_engine_cls = None
        else:
            db_client_cls = _DBClient
            base_db_engine_cls = _BaseDBEngine
        if (
            base_db_engine_cls is not None
            and db_client_cls is not None
            and isinstance(logging_target, base_db_engine_cls)
        ):
            return logger, log_repository, db_client_cls(logging_target)
        if db_client_cls is not None and isinstance(logging_target, db_client_cls):
            raise ValueError("logging에는 DBClient가 아니라 BaseDBEngine을 주입해야 합니다.")
        raise ValueError("logging_engine에는 BaseDBEngine, Logger, LogRepository만 허용됩니다.")

    def _build_llm_repository(
        self,
        db_client: "DBClient",
        collection: str,
        schema: Optional["CollectionSchema"],
        auto_create: bool,
        auto_connect: bool,
    ) -> LogRepository:
        from chatbot.shared.logging.llm_repository import LLMLogRepository

        return LLMLogRepository(
            client=db_client,
            collection=collection,
            schema=schema,
            auto_create=auto_create,
            auto_connect=auto_connect,
        )

    def _iter_stream_chunks(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None,
        run_manager: CallbackManagerForLLMRun | None,
        kwargs: dict[str, Any],
    ) -> Iterator[Any]:
        """내부 모델의 네이티브 스트리밍 구현만 사용한다."""

        stream_impl = getattr(type(self._model), "_stream", None)
        if stream_impl is None or stream_impl is BaseChatModel._stream:
            detail = ExceptionDetail(
                code="LLM_STREAM_NOT_SUPPORTED",
                cause=f"model={type(self._model).__name__}",
            )
            raise BaseAppException(
                "현재 모델은 네이티브 스트리밍을 지원하지 않습니다.",
                detail,
            )
        yield from self._model._stream(
            messages,
            stop=stop,
            run_manager=run_manager,
            **kwargs,
        )

    async def _aiter_stream_chunks(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None,
        run_manager: AsyncCallbackManagerForLLMRun | None,
        kwargs: dict[str, Any],
    ) -> AsyncIterator[Any]:
        """내부 모델의 네이티브 비동기 스트리밍 구현만 사용한다."""

        astream_impl = getattr(type(self._model), "_astream", None)
        if astream_impl is None or astream_impl is BaseChatModel._astream:
            detail = ExceptionDetail(
                code="LLM_ASTREAM_NOT_SUPPORTED",
                cause=f"model={type(self._model).__name__}",
            )
            raise BaseAppException(
                "현재 모델은 네이티브 비동기 스트리밍을 지원하지 않습니다.",
                detail,
            )
        async for chunk in self._model._astream(
            messages,
            stop=stop,
            run_manager=run_manager,
            **kwargs,
        ):
            yield chunk

    def _log_start(
        self,
        action: str,
        messages: Sequence[BaseMessage],
        stop: Optional[Sequence[str]],
        stream: bool,
        kwargs: dict,
    ) -> None:
        metadata = self._build_metadata(action, messages, stop, stream, kwargs)
        context = self._get_context()
        self._safe_log(LogLevel.INFO, f"LLM {action} 호출 시작", context=context, metadata=metadata)

    def _log_success(self, action: str, start: float, result: Optional[ChatResult]) -> None:
        metadata = self._base_metadata(action)
        metadata.update(
            {
                "duration_ms": int((time.monotonic() - start) * 1000),
                "success": True,
            }
        )
        usage = self._extract_usage_metadata(result)
        if usage:
            metadata["usage_metadata"] = usage
        if self._log_response and result is not None:
            metadata["result"] = self._serialize_result(result)
        context = self._get_context()
        self._safe_log(LogLevel.INFO, f"LLM {action} 호출 성공", context=context, metadata=metadata)

    def _log_error(self, action: str, error: Exception, start: float) -> None:
        metadata = self._base_metadata(action)
        metadata.update(
            {
                "duration_ms": int((time.monotonic() - start) * 1000),
                "error_type": type(error).__name__,
                "success": False,
            }
        )
        context = self._get_context()
        self._safe_log(
            LogLevel.ERROR,
            f"LLM {action} 호출 실패: {error}",
            context=context,
            metadata=metadata,
        )

    def _build_metadata(
        self,
        action: str,
        messages: Sequence[BaseMessage],
        stop: Optional[Sequence[str]],
        stream: bool,
        kwargs: dict,
    ) -> dict:
        metadata = self._base_metadata(action)
        metadata.update(
            {
                "message_count": len(messages),
                "stop": bool(stop),
                "stream": stream,
                "kwargs": list(kwargs.keys()),
            }
        )
        if self._log_payload:
            metadata["messages"] = [self._serialize_message(msg) for msg in messages]
        return metadata

    def _base_metadata(self, action: str) -> dict:
        llm_type = getattr(self._model, "_llm_type", None)
        return {
            "action": action,
            "model_name": self._name,
            "ls_model_name": self._name,
            "llm_type": llm_type,
            "provider": llm_type,
            "ls_provider": llm_type,
        }

    def _run_background(self, fn: Callable[..., None], *args: Any) -> None:
        if self._background_runner is not None:
            try:
                self._background_runner(fn, *args)
            except Exception:  # noqa: BLE001 - 백그라운드 실패가 본 호출을 깨지 않도록 보호
                return
            return
        try:
            thread = threading.Thread(target=fn, args=args, daemon=True)
            thread.start()
        except Exception:  # noqa: BLE001 - 스레드 시작 실패가 본 호출을 깨지 않도록 보호
            return

    def _safe_log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[LogContext],
        metadata: Optional[dict],
    ) -> None:
        """로깅 실패가 본 호출을 깨지 않도록 보호한다."""

        try:
            self._logger.log(level, message, context=context, metadata=metadata)
        except Exception:  # noqa: BLE001 - 로깅은 best-effort로 동작해야 한다.
            return

    def _get_context(self) -> Optional[LogContext]:
        if not self._context_provider:
            return None
        try:
            return self._context_provider()
        except Exception:  # noqa: BLE001 - 로깅 실패 방지
            return None

    def _extract_usage_metadata(self, result: Optional[ChatResult]) -> Optional[dict]:
        if result is None:
            return None
        llm_output = getattr(result, "llm_output", None)
        if isinstance(llm_output, dict):
            usage = llm_output.get("usage_metadata")
            if isinstance(usage, dict):
                return usage
        generations = getattr(result, "generations", [])
        for item in generations:
            if isinstance(item, list):
                candidates = item
            else:
                candidates = [item]
            for generation in candidates:
                message = getattr(generation, "message", None)
                usage = getattr(message, "usage_metadata", None)
                if isinstance(usage, dict):
                    return usage
                response_metadata = getattr(message, "response_metadata", None)
                if isinstance(response_metadata, dict):
                    usage = response_metadata.get("usage_metadata")
                    if isinstance(usage, dict):
                        return usage
        return None

    def _serialize_message(self, message: BaseMessage) -> dict:
        if hasattr(message, "model_dump"):
            return message.model_dump(mode="json")
        if hasattr(message, "dict"):
            return message.dict()
        return {"text": str(message)}

    def _serialize_result(self, result: ChatResult) -> dict:
        if hasattr(result, "model_dump"):
            return result.model_dump(mode="json")
        if hasattr(result, "dict"):
            return result.dict()
        return {"text": str(result)}

    def _to_generation_chunk(self, chunk: Any) -> ChatGenerationChunk:
        """스트리밍 출력 객체를 ChatGenerationChunk로 정규화한다."""

        if isinstance(chunk, ChatGenerationChunk):
            return chunk
        return ChatGenerationChunk(message=self._to_message_chunk(chunk))

    def _to_message_chunk(self, chunk: Any) -> BaseMessageChunk:
        """스트리밍 출력 객체를 BaseMessageChunk로 정규화한다."""

        if isinstance(chunk, BaseMessageChunk):
            return chunk
        if isinstance(chunk, AIMessage):
            return AIMessageChunk(
                content=chunk.content,
                additional_kwargs=chunk.additional_kwargs,
                response_metadata=chunk.response_metadata,
                name=chunk.name,
                id=chunk.id,
                tool_calls=chunk.tool_calls,
                invalid_tool_calls=chunk.invalid_tool_calls,
                usage_metadata=chunk.usage_metadata,
            )
        if isinstance(chunk, BaseMessage):
            return AIMessageChunk(
                content=chunk.content,
                additional_kwargs=getattr(chunk, "additional_kwargs", {}),
                response_metadata=getattr(chunk, "response_metadata", {}),
                name=getattr(chunk, "name", None),
                id=getattr(chunk, "id", None),
            )
        return AIMessageChunk(content=str(chunk))

    def _to_text(self, content: Any) -> str:
        """메시지 콘텐츠를 문자열로 정규화한다."""

        if isinstance(content, str):
            return content
        if isinstance(content, list):
            chunks: list[str] = []
            for item in content:
                if isinstance(item, str):
                    chunks.append(item)
                elif isinstance(item, dict):
                    text = item.get("text")
                    if text is not None:
                        chunks.append(str(text))
                else:
                    chunks.append(str(item))
            return "".join(chunks)
        return str(content)
