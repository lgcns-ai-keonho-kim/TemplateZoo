# Integrations Embedding 가이드

이 문서는 `src/plan_and_then_execute_agent/integrations/embedding/client.py`와 `src/plan_and_then_execute_agent/integrations/embedding/_client_mixin.py` 기준으로 `EmbeddingClient` 인터페이스와 동작 규칙을 정리합니다.

## 1. 용어 정리

| 용어 | 의미 | 관련 스크립트 |
| --- | --- | --- |
| Embeddings | LangChain 임베딩 베이스 타입 | `langchain_core.embeddings` |
| EmbeddingClient | 임베딩 호출/로깅/예외를 표준화한 래퍼 | `integrations/embedding/client.py` |
| logging_engine | 로깅 주입 대상(엔진/로거/저장소) | `EmbeddingClient.__init__` |
| EmbeddingLogRepository | 임베딩 로그 전용 DB 저장소 | `shared/logging/embedding_repository.py` |

## 2. 관련 스크립트

| 파일 | 역할 |
| --- | --- |
| `src/plan_and_then_execute_agent/integrations/embedding/client.py` | EmbeddingClient 공개 인터페이스/핵심 호출 경로 |
| `src/plan_and_then_execute_agent/integrations/embedding/_client_mixin.py` | 보조 로직(로그 메타 생성, 백그라운드 로깅, 컨텍스트 조회) |
| `src/plan_and_then_execute_agent/integrations/embedding/__init__.py` | 공개 API 제공 |
| `src/plan_and_then_execute_agent/shared/logging/embedding_repository.py` | 임베딩 로그 DB 저장소 |
| `src/plan_and_then_execute_agent/shared/config/runtime_env_loader.py` | 임베딩 차원 해석 유틸 |

참고:

- 현재 기본 Chat 런타임(`api/chat/services/runtime.py`)은 `EmbeddingClient`를 직접 사용하지 않습니다.
- EmbeddingClient는 확장 기능 또는 외부 실험 코드에서 사용합니다.

## 3. 인터페이스

호출 메서드:

1. 동기 질의: `embed_query(text)`
2. 동기 문서: `embed_documents(texts)`
3. 비동기 질의: `aembed_query(text)`
4. 비동기 문서: `aembed_documents(texts)`

동작 규칙:

1. 내부 모델이 반환한 벡터를 `float` 리스트로 정규화합니다.
2. 문서 결과 개수와 입력 개수가 다르면 예외를 발생시킵니다.
3. 벡터가 비어 있거나 차원이 문서별로 다르면 예외를 발생시킵니다.

## 4. 로깅 주입 규칙

`logging_engine` 허용 타입:

1. `BaseDBEngine`
2. `Logger`
3. `LogRepository`

동작:

1. `BaseDBEngine` 주입 시 내부에서 `DBClient(engine)`를 만들고 `EmbeddingLogRepository`를 자동 구성합니다.
2. `logger`가 있으면 그대로 사용합니다.
3. `log_repository`만 있으면 `InMemoryLogger`를 생성합니다.
4. 둘 다 없으면 `create_default_logger(name)`를 사용합니다.

## 5. 로그 메타데이터

기본 메타 키:

1. `action`
2. `model_name`
3. `provider`
4. `client_name`

시작 시 추가:

1. `input_count`
2. `input_chars`
3. `payload` (`log_payload=True`일 때)

성공 시 추가:

1. `duration_ms`
2. `success`
3. `output_count`
4. `dimension`
5. `response` (`log_response=True`일 때)

실패 시 추가:

1. `duration_ms`
2. `success=False`
3. `error_type`

## 6. 예외 코드

| 상황 | 코드 |
| --- | --- |
| 동기 질의 실패 | `EMBED_QUERY_ERROR` |
| 동기 문서 실패 | `EMBED_DOCUMENTS_ERROR` |
| 비동기 질의 실패 | `EMBED_AQUERY_ERROR` |
| 비동기 문서 실패 | `EMBED_ADOCUMENTS_ERROR` |
| 벡터 형식 오류 | `EMBEDDING_VECTOR_INVALID` |
| 빈 벡터 반환 | `EMBEDDING_VECTOR_EMPTY` |
| 문서 임베딩 개수 불일치 | `EMBEDDING_DOCUMENT_COUNT_MISMATCH` |
| 문서 임베딩 차원 불일치 | `EMBEDDING_DIMENSION_INCONSISTENT` |

## 7. 사용 예시

```python
import os

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from plan_and_then_execute_agent.integrations.embedding import EmbeddingClient
from plan_and_then_execute_agent.shared.config import resolve_gemini_embedding_dim

dimension = resolve_gemini_embedding_dim()

embedder = EmbeddingClient(
    model=GoogleGenerativeAIEmbeddings(
        model=os.getenv("GEMINI_EMBEDDING_MODEL", ""),
        project=os.getenv("GEMINI_PROJECT", ""),
        output_dimensionality=dimension,
    ),
    name="example-embedding-client",
)

vector = embedder.embed_query("안녕하세요")
```

## 8. 운영 체크리스트

1. `GEMINI_EMBEDDING_DIM`은 1 이상의 정수여야 합니다.
2. 임베딩 호출부 전체가 같은 차원 정책을 사용하도록 고정합니다.
3. 저장소 차원 불일치 시 기존 데이터/스키마 재생성 절차를 준비합니다.
4. 대량 배치에서는 API 한도/지연 시간을 고려해 배치 크기를 조정합니다.

## 9. 관련 문서

- `docs/integrations/overview.md`
- `docs/integrations/llm.md`
- `docs/setup/env.md`

## 10. 소스 매칭 점검 항목

1. 예외 코드 표가 `client.py` 구현과 일치하는가
2. logging_engine 허용 타입 설명이 `_resolve_logging`과 일치하는가
3. 보조 로깅/백그라운드 실행 설명이 `_client_mixin.py`와 일치하는가
4. 문서 경로가 실제 `src/plan_and_then_execute_agent/integrations/embedding` 구조와 일치하는가
