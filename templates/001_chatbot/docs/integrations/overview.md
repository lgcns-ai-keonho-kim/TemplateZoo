# Integrations 모듈 레퍼런스

`src/chatbot/integrations`는 외부 기술 스택을 애플리케이션 내부 계약으로 감싸는 계층이다.

## 1. 책임

1. 외부 라이브러리와 저장소 엔진의 세부 구현을 숨긴다.
2. 상위 계층이 엔진/공급자 교체 비용을 낮출 수 있게 공통 계약을 제공한다.
3. 도메인 정책이나 HTTP 라우팅은 담당하지 않는다.

## 2. 하위 모듈

| 경로 | 역할 | 현재 기본 런타임 사용 여부 |
| --- | --- | --- |
| `src/chatbot/integrations/db` | 공통 DB 클라이언트, 쿼리 모델, 엔진 구현체 | 사용 중 |
| `src/chatbot/integrations/llm` | LLM 호출 래퍼와 예외/로깅 표준화 | 사용 중 |
| `src/chatbot/integrations/fs` | 파일 시스템 엔진과 파일 로그 저장소 | 기본 경로 아님 |

## 3. 현재 기본 런타임

1. 채팅 그래프는 `ChatGoogleGenerativeAI`를 `LLMClient`로 감싸 사용한다.
2. 채팅 이력 저장은 `ChatHistoryRepository` 기본 생성자를 통해 SQLite를 사용한다.
3. 파일 시스템 저장소는 기본 조립에 포함되지 않는다.

## 4. 유지보수 포인트

1. 기본 경로와 선택 확장 경로를 문서에서 분리해야 한다.
2. 공통 모델 의미를 바꾸면 여러 엔진과 저장소가 동시에 영향을 받는다.
3. 외부 라이브러리 고유 개념을 상위 계층으로 직접 노출하지 않는 편이 유지보수에 유리하다.

## 5. 관련 문서

- `docs/integrations/db/overview.md`
- `docs/integrations/llm/overview.md`
- `docs/integrations/fs/overview.md`
- `docs/setup/overview.md`
