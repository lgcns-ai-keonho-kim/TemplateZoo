# Integrations 모듈 레퍼런스

`src/chatbot/integrations`는 외부 기술 스택을 애플리케이션 내부 계약으로 감싸는 계층이다.
현재 코드 기준으로 기본 런타임은 이 계층의 일부만 직접 사용하고, 나머지는 선택 확장 경로로 남아 있다.

## 1. 책임 경계

1. 이 계층은 외부 라이브러리와 저장소 엔진의 세부 구현을 감춘다.
2. `api`, `core`, `shared`는 가능한 한 `integrations`의 공개 클래스와 공통 모델만 의존한다.
3. 엔드포인트, 도메인 정책, 서비스 오케스트레이션은 이 계층의 책임이 아니다.

## 2. 하위 모듈

| 경로 | 역할 | 현재 기본 런타임 사용 여부 |
| --- | --- | --- |
| `src/chatbot/integrations/db` | 공통 DB 클라이언트, 쿼리 모델, 엔진 구현체 | 사용 중 |
| `src/chatbot/integrations/llm` | LLM 호출 래퍼와 로깅/예외 표준화 | 사용 중 |
| `src/chatbot/integrations/fs` | 파일 시스템 엔진과 파일 로그 저장소 | 선택 경로 |

## 3. 현재 기본 런타임

1. 채팅 그래프는 `ChatGoogleGenerativeAI`를 `LLMClient`로 감싸서 사용한다.
2. 채팅 이력 저장은 `ChatHistoryRepository`가 기본적으로 `SQLiteEngine`을 생성해 처리한다.
3. 파일 시스템 저장소는 기본 조립 코드에 주입되지 않으며, 로그 아카이브가 필요할 때만 선택적으로 붙인다.

## 4. 선택 가능한 확장 경로

1. DB는 PostgreSQL, MongoDB, Redis, Elasticsearch, LanceDB 엔진으로 전환하거나 병행 구성할 수 있다.
2. LLM은 다른 LangChain 호환 모델을 `LLMClient`에 주입하는 방식으로 교체할 수 있다.
3. FS는 `BaseFSEngine`을 구현하는 원격 스토리지 엔진으로 확장할 수 있다.

## 5. 유지보수 포인트

1. 공개 API는 `src/chatbot/integrations/__init__.py` export와 overview 문서가 항상 같이 맞아야 한다.
2. 기본 런타임에서 실제 사용하는 구현과 예시 구현을 문서에서 분리해 적어야 혼동이 줄어든다.
3. 공통 모델(`Query`, `CollectionSchema`, `LogRecord`) 의미를 바꾸는 변경은 여러 엔진과 저장소에 동시에 파급된다.

## 6. 추가 개발과 확장 시 주의점

1. 새 엔진이나 클라이언트를 추가하더라도 상위 계층이 기대하는 반환 형식과 예외 의미를 유지해야 한다.
2. 선택 확장 기능을 기본 런타임으로 승격할 때는 `runtime.py` 조립 코드와 setup 문서를 같이 수정해야 한다.
3. 외부 라이브러리 고유 개념을 상위 계층으로 직접 노출하지 않는 편이 유지보수에 유리하다.

## 7. 관련 문서

- `docs/integrations/db/overview.md`
- `docs/integrations/llm/overview.md`
- `docs/integrations/fs/overview.md`
- `docs/setup/overview.md`
