# MongoDB 구성 레퍼런스

이 문서는 MongoDB 엔진을 선택적으로 사용할 때 필요한 코드 경계와 설정 포인트를 설명한다.
현재 기본 채팅 런타임은 MongoDB를 자동으로 조립하지 않는다.

## 1. 현재 코드 기준 확장 경로

1. `src/chatbot/integrations/db/engines/mongodb/*`가 연결, 필터, 스키마, 문서 변환을 제공한다.
2. 실제 서비스 전환은 `ChatHistoryRepository`에 MongoDB 기반 `DBClient`를 주입할 때만 일어난다.

## 2. 필요한 환경 변수

```env
MONGODB_URI=
MONGODB_HOST=127.0.0.1
MONGODB_PORT=27017
MONGODB_USER=
MONGODB_PW=
MONGODB_DB=playground
MONGODB_AUTH_DB=
```

## 3. 유지보수 포인트

1. `MONGODB_AUTH_DB`와 실제 사용자 생성 DB가 다르면 인증 실패가 발생하므로 문서와 운영 스크립트를 같이 맞춰야 한다.
2. URI 직접 입력과 host/port 조합 입력을 혼용하면 우선순위 문서를 명확히 해야 한다.
3. 필터 빌더와 document mapper는 스키마 변경의 영향을 직접 받는다.

## 4. 추가 개발과 확장 시 주의점

1. MongoDB를 기본 저장소로 전환할 때는 정렬/페이지네이션/삭제 계약이 기존 SQLite와 같은 의미인지 확인해야 한다.
2. 운영 전환 시 인증 DB, 컬렉션 초기화, 인덱스 정책을 setup 문서에 함께 남겨야 한다.

## 5. 관련 문서

- `docs/integrations/db/engines/mongodb/engine.md`
- `docs/integrations/db/overview.md`
- `docs/setup/env.md`
- `docs/setup/troubleshooting.md`
