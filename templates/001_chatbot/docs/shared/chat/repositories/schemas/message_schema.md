# `repositories/schemas/message_schema.py` 레퍼런스

이 파일은 채팅 메시지 컬렉션 스키마를 만드는 팩토리다.

## 1. 코드 설명

`build_chat_message_schema()`가 반환하는 컬럼:

1. `message_id` - 기본 키
2. `session_id`
3. `role`
4. `content`
5. `sequence`
6. `created_at`
7. `metadata`

`metadata`는 문자열 컬럼으로 저장되며, 실제 직렬화/역직렬화는 매퍼가 담당한다.

## 2. 유지보수 포인트

1. 메시지 정렬은 `sequence`를 기준으로 하므로, 순번 정책을 바꾸면 목록 조회와 최근 메시지 조회가 동시에 영향을 받는다.
2. `metadata` 저장 형식을 바꾸면 LLM 응답 부가정보와 request 관련 메타데이터 해석이 달라질 수 있다.

## 3. 추가 개발/확장 가이드

1. 메시지별 토큰 수, 응답 모델명 같은 추가 필드가 필요하면 `metadata`에 둘지 별도 컬럼으로 뺄지 먼저 결정해야 한다. 조회 성능이 중요하면 별도 컬럼이 낫다.

## 4. 관련 코드

- `src/chatbot/shared/chat/repositories/history_repository.py`
- `src/chatbot/core/chat/utils/mapper.py`
