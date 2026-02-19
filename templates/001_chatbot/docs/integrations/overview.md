# Integrations 모듈 가이드

이 문서는 `src/base_template/integrations` 계층의 책임, 구성 요소, 교체 절차를 코드 기준으로 정리한다.

## 1. 용어 정리

| 용어 | 의미 | 관련 스크립트 |
| --- | --- | --- |
| 통합 계층 | 외부 시스템(DB, LLM, 파일시스템)과 직접 통신하는 계층 | `src/base_template/integrations/*` |
| DB 엔진 | 저장소별 CRUD/검색 구현체 | `integrations/db/engines/*/engine.py` |
| DB 클라이언트 | 엔진 공통 호출 퍼사드 | `integrations/db/client.py` |
| LLM 클라이언트 | 모델 호출/로깅/예외를 표준화한 래퍼 | `integrations/llm/client.py` |
| 파일 시스템 엔진 | 파일 읽기/쓰기/목록/이동/복사 인터페이스 | `integrations/fs/base/engine.py` |

## 2. 모듈 구성과 스크립트 맵

| 경로 | 책임 | 주요 스크립트 |
| --- | --- | --- |
| `src/base_template/integrations/db` | DB 엔진 추상화, Query DSL, 엔진별 구현 | `client.py`, `base/*.py`, `query_builder/*.py`, `engines/*` |
| `src/base_template/integrations/llm` | LangChain 모델 래핑과 로깅/예외 표준화 | `client.py` |
| `src/base_template/integrations/fs` | 파일 시스템 추상화와 파일 로그 저장소 | `base/engine.py`, `engines/local.py`, `file_repository.py` |
| `src/base_template/integrations/__init__.py` | integrations 공개 API | `__init__.py` |

## 3. 책임 경계

핵심 규칙:

1. API 라우터는 integrations 구현체를 직접 생성하지 않는다.
2. shared 서비스 계층이 integrations를 사용한다.
3. 엔진 교체는 조립 지점(`src/base_template/api/chat/services/runtime.py`)에서 수행한다.
4. 상위 계층은 가능하면 인터페이스(포트/퍼사드)만 의존한다.

## 4. 교체 전략

## 4-1. DB 엔진 교체

1. 엔진 인스턴스를 새 구현으로 교체한다.
2. `DBClient(new_engine)`를 생성한다.
3. `ChatHistoryRepository(db_client=...)` 주입 방식으로 연결한다.
4. 문서와 환경 변수를 함께 갱신한다.

## 4-2. LLM 공급자 교체

1. 노드 조립 파일(`core/chat/nodes/*.py`)에서 BaseChatModel 생성부를 교체한다.
2. `LLMClient` 래퍼는 유지한다.
3. 예외 코드와 로그 메타데이터 키를 유지한다.

## 4-3. 파일 저장소 교체

1. `BaseFSEngine` 구현체를 추가한다.
2. `FileLogRepository(engine=...)`로 주입한다.
3. 호출 계층은 변경하지 않는다.

## 5. 소스 매칭 점검 항목

1. 문서에 기재한 엔진/클라이언트 경로가 실제 파일과 일치하는가
2. 공개 API 목록이 `__init__.py` 노출 항목과 일치하는가
3. 교체 절차가 실제 조립 지점과 일치하는가

## 6. 관련 문서

- `docs/integrations/db.md`
- `docs/integrations/llm.md`
- `docs/integrations/fs.md`
- `docs/setup/postgresql_pgvector.md`
- `docs/setup/mongodb.md`
- `docs/setup/filesystem.md`
- `docs/shared/chat.md`
